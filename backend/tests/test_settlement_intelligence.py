"""Unit and integration tests for ColdChain AI Settlement Intelligence."""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.enums import UserRole, OrganizationStatus
from app.models.organization import Organization
from app.models.user import User
from app.services.contract_service import contract_service, SAMPLE_CONTRACTS
from app.services.settlement_service import settlement_service
from app.schemas.contract_intelligence import (
    ContractExtractionRequest,
    HumanApprovalRequest,
)


@pytest.fixture
def memory_db():
    """In-memory SQLite database for deterministic settlement testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    org = Organization(
        id="org-test-settlement",
        name="Pharma Logistics Corp",
        slug="pharma-logistics",
        status=OrganizationStatus.ACTIVE,
    )
    session.add(org)

    user = User(
        id="user-qa-auditor",
        organization_id=org.id,
        email="qa-auditor@pharmalogistics.com",
        full_name="Dr. QA Auditor",
        role=UserRole.ADMIN,
        hashed_password="hashed_test_password",
        is_active=True,
    )
    session.add(user)
    session.commit()

    yield session
    session.close()


def test_contract_samples_retrieval():
    """Verify curated master service agreements are available with complete clauses."""
    samples = contract_service.get_sample_contracts()
    assert len(samples) >= 3
    for s in samples:
        assert s.contract_id
        assert s.agreed_payment_amount > Decimal("0")
        assert s.permitted_min_temp_celsius < s.permitted_max_temp_celsius
        assert len(s.clauses) > 0
        assert s.clauses[0].source_document
        assert s.clauses[0].source_page is not None


def test_contract_extraction_sample_mode():
    """Verify sample contract extraction correctly cites sources and categories."""
    req = ContractExtractionRequest(sample_id="SAMPLE-MSA-01-CLEAN")
    res = contract_service.extract_contract(sample_id=req.sample_id)
    assert res.contract.contract_id == "MSA-2026-CH-01"
    assert res.contract.permitted_min_temp_celsius == Decimal("2.00")
    assert res.contract.permitted_max_temp_celsius == Decimal("8.00")
    assert "DEMO_SIMULATION" in res.ai_mode


def test_clean_shipment_investigation_and_lot_eligibility(memory_db):
    """
    Scenario A: Clean shipment satisfies all conditions.
    AI investigation should recommend ELIGIBLE and approve settlement.
    """
    result = settlement_service.run_investigation(
        db=memory_db,
        org_id="org-test-settlement",
        shipment_identifier="CHALLENGE-01-CLEAN",
    )
    assert result.tracking_number == "CHALLENGE-01-CLEAN"
    assert result.overall_recommendation == "ELIGIBLE_FOR_SETTLEMENT"
    assert result.compliance_breakdown["temperature_compliant"] is True
    assert result.compliance_breakdown["evidence_hash_valid"] is True
    assert len(result.lots) == 2
    for lot in result.lots:
        assert lot.recommendation == "ELIGIBLE"
        assert lot.temperature_status == "PASS"

    # Deterministic sum of lots must equal total authorized amount
    lot_sum = sum(l.allocated_amount for l in result.lots)
    assert lot_sum == result.total_authorized_amount


def test_thermal_excursion_investigation_and_quality_hold(memory_db):
    """
    Scenario B: Temperature excursion breach during tarmac transfer.
    AI investigation must flag breach and recommend QUALITY_REVIEW.
    """
    result = settlement_service.run_investigation(
        db=memory_db,
        org_id="org-test-settlement",
        shipment_identifier="CHALLENGE-02-EXCURSION",
    )
    assert result.overall_recommendation == "REQUIRES_QUALITY_REVIEW"
    assert result.compliance_breakdown["temperature_compliant"] is False
    assert result.compliance_breakdown["recorded_max_temp"] == 14.50
    assert len(result.lots) >= 1
    assert result.lots[0].recommendation == "QUALITY_REVIEW"
    assert result.lots[0].temperature_status == "BREACH"


def test_evidence_tamper_investigation_insufficient_evidence(memory_db):
    """
    Scenario C: Cryptographic hash discrepancy.
    AI investigation must flag HASH_MISMATCH and recommend INSUFFICIENT_EVIDENCE.
    """
    result = settlement_service.run_investigation(
        db=memory_db,
        org_id="org-test-settlement",
        shipment_identifier="CHALLENGE-03-TAMPER",
    )
    assert result.overall_recommendation == "INSUFFICIENT_EVIDENCE"
    assert result.compliance_breakdown["evidence_hash_valid"] is False
    assert result.lots[0].recommendation == "INSUFFICIENT_EVIDENCE"
    assert result.lots[0].evidence_status == "HASH_MISMATCH"


def test_human_approval_execution_and_paypal_capture(memory_db):
    """
    Verify human review step executes PayPal capture only when explicitly approved,
    and returns valid transaction ID and status.
    """
    approval_req = HumanApprovalRequest(
        investigation_id="INV-AI-TEST-001",
        shipment_id="s-clean-01",
        approved=True,
        approved_amount=Decimal("12500.00"),
        reviewer_notes="Verified by Lead QA Specialist: All cold-chain requirements satisfied.",
        reviewer_id="lead-qa-auditor@pharmalogistics.com",
    )

    exec_res = settlement_service.execute_human_approval(
        db=memory_db,
        org_id="org-test-settlement",
        approval_req=approval_req,
    )

    assert exec_res.decision == "APPROVED_AND_CAPTURED"
    assert exec_res.approved_amount == Decimal("12500.00")
    assert exec_res.paypal_status == "COMPLETED"
    assert exec_res.paypal_transaction_id.startswith("SIMULATED-PAYPAL-CAP-")
    assert exec_res.idempotency_key is not None


def test_human_rejection_execution_quality_hold(memory_db):
    """
    Verify human reviewer can reject settlement, withholding all funds in quality hold.
    """
    rejection_req = HumanApprovalRequest(
        investigation_id="INV-AI-TEST-REJECT-002",
        shipment_id="s-excursion-02",
        approved=False,
        approved_amount=Decimal("0.00"),
        reviewer_notes="Withheld due to critical 14.5°C breach on tarmac. Consignment quarantined.",
        reviewer_id="lead-qa-auditor@pharmalogistics.com",
    )

    exec_res = settlement_service.execute_human_approval(
        db=memory_db,
        org_id="org-test-settlement",
        approval_req=rejection_req,
    )

    assert exec_res.decision == "REJECTED_QUALITY_HOLD"
    assert exec_res.approved_amount == Decimal("0.00")
    assert exec_res.paypal_transaction_id is None
    assert "CAPTURE_BLOCKED" in exec_res.paypal_status


def test_duplicate_capture_prevention(memory_db):
    """
    Verify accidental duplicate capture calls for the same investigation return
    the original execution response without re-executing payment.
    """
    approval_req = HumanApprovalRequest(
        investigation_id="INV-AI-TEST-DUPE-003",
        shipment_id="s-clean-01",
        approved=True,
        approved_amount=Decimal("12500.00"),
        reviewer_notes="Initial approval",
        reviewer_id="qa@pharma.com",
    )

    res1 = settlement_service.execute_human_approval(
        db=memory_db,
        org_id="org-test-settlement",
        approval_req=approval_req,
    )

    # Second identical attempt
    res2 = settlement_service.execute_human_approval(
        db=memory_db,
        org_id="org-test-settlement",
        approval_req=approval_req,
    )

    assert res1.execution_id == res2.execution_id
    assert res1.paypal_transaction_id == res2.paypal_transaction_id
    assert res1.idempotency_key == res2.idempotency_key

