"""Sentinel Challenge service implementing the 4 reproducible hackathon demo scenarios."""

from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.shipment import Shipment
from app.models.product_profile import ProductProfile
from app.models.investigation import Investigation
from app.models.enums import (
    ShipmentStatus,
    PaymentStatus,
    DecisionType,
    EvidenceType,
    CustodyEventType,
    InvestigationPriority,
)
from app.services import (
    product_profile_service,
    shipment_service,
    evidence_service,
    temperature_service,
    custody_service,
    payment_service,
    investigation_service,
)
from app.schemas.challenge import ChallengeScenarioResponse


SCENARIO_METADATA = [
    {
        "scenario_id": "clean-shipment",
        "title": "Scenario 1: Clean Shipment (Full Compliance)",
        "description": "Continuous cold storage within 2°C–8°C limit. Intact custody chain. Automated verification passes and PayPal Sandbox capture settles.",
        "expected_outcome": "VERIFIED & CAPTURED",
        "tracking_prefix": "CHALLENGE-01-CLEAN",
    },
    {
        "scenario_id": "thermal-excursion",
        "title": "Scenario 2: Thermal Excursion (Limit Breach)",
        "description": "Excursion spikes to 14.5°C during tarmac transfer exceeding the allowed 10-minute threshold. Verification fails; payment capture blocked.",
        "expected_outcome": "FAILED & CAPTURE_BLOCKED",
        "tracking_prefix": "CHALLENGE-02-EXCURSION",
    },
    {
        "scenario_id": "evidence-tamper",
        "title": "Scenario 3: Evidence Hash Tamper Anomaly",
        "description": "Discrepancy detected between recorded evidence SHA-256 digest and physical storage. Cryptographic tamper alert raised; routed to investigation.",
        "expected_outcome": "TAMPER_DETECTED & BLOCKED",
        "tracking_prefix": "CHALLENGE-03-TAMPER",
    },
    {
        "scenario_id": "custody-gap",
        "title": "Scenario 4: Chain of Custody Gap",
        "description": "Missing airport cargo clearance sign-off event. Incomplete custody lineage forces manual review; automated payment release withheld.",
        "expected_outcome": "CUSTODY_GAP & REVIEW_REQUIRED",
        "tracking_prefix": "CHALLENGE-04-CUSTODY",
    },
]


def reset_challenge(db: Session, org_id: str, user_id: str) -> List[ChallengeScenarioResponse]:
    """Deterministically seed the 4 reproducible Sentinel Challenge scenarios."""
    # Ensure profile exists
    profile = db.scalar(
        select(ProductProfile).where(
            ProductProfile.organization_id == org_id,
            ProductProfile.name == "Sentinel Challenge Profile (2-8C)",
        )
    )
    if not profile:
        profile = product_profile_service.create_profile(
            db=db,
            org_id=org_id,
            name="Sentinel Challenge Profile (2-8C)",
            min_temp=Decimal("2.00"),
            max_temp=Decimal("8.00"),
            max_excursion_seconds=600,
            expected_sampling_seconds=300,
            max_gap_seconds=900,
            user_id=user_id,
        )

    now = datetime.now(timezone.utc)
    scenarios: List[ChallengeScenarioResponse] = []

    # 1. SCENARIO 1: Clean Shipment
    trk_1 = "CHALLENGE-01-CLEAN"
    s1 = db.scalar(select(Shipment).where(Shipment.tracking_number == trk_1))
    if not s1:
        s1 = shipment_service.create_shipment(
            db=db, org_id=org_id, product_profile_id=profile.id,
            tracking_number=trk_1, origin="Basel Pharma Depot", destination="London Guy's Hospital",
            created_by_user_id=user_id,
        )
        shipment_service.update_shipment_status(db=db, org_id=org_id, shipment_id=s1.id, new_status=ShipmentStatus.IN_TRANSIT)
        shipment_service.update_shipment_status(db=db, org_id=org_id, shipment_id=s1.id, new_status=ShipmentStatus.DELIVERED)

        csv_clean = (
            b"timestamp,temperature,sensor_id\n"
            b"2026-11-01T08:00:00Z,4.2,LOGGER-A1\n"
            b"2026-11-01T08:05:00Z,4.8,LOGGER-A1\n"
            b"2026-11-01T08:10:00Z,5.1,LOGGER-A1\n"
        )
        evidence_service.upload_evidence(
            db=db, org_id=org_id, shipment_id=s1.id, file_type=EvidenceType.LOGGER_CSV,
            original_filename="clean_telemetry.csv", content=csv_clean, uploaded_by_user_id=user_id,
        )
        custody_service.record_custody_transfer(
            db=db, org_id=org_id, shipment_id=s1.id, event_type=CustodyEventType.DISPATCH,
            carrier_name="Swiss WorldCargo", custodian_name="M. Blanc", location="Basel Hub",
            actor_user_id=user_id,
        )
        custody_service.record_custody_transfer(
            db=db, org_id=org_id, shipment_id=s1.id, event_type=CustodyEventType.DELIVERY_HANDOVER,
            carrier_name="Swiss WorldCargo", custodian_name="Dr. Taylor", location="London Hospital",
            actor_user_id=user_id,
        )
        dec_1 = temperature_service.evaluate_shipment_compliance(db=db, org_id=org_id, shipment_id=s1.id, decided_by_user_id=user_id)
        p1 = payment_service.create_payment(
            db=db, org_id=org_id, shipment_id=s1.id, amount=Decimal("12500.00"), currency="USD", user_id=user_id,
        )
        # Capture clean payment
        payment_service.execute_capture(db=db, payment_id=p1.id, idempotency_key=f"IDEMP-{trk_1}-DEMO")
        dec_1_str = dec_1.decision.value
        p1_status = "CAPTURED"
    else:
        dec_1_str = "PASSED"
        p1_status = "CAPTURED"

    scenarios.append(
        ChallengeScenarioResponse(
            scenario_id="clean-shipment",
            title=SCENARIO_METADATA[0]["title"],
            description=SCENARIO_METADATA[0]["description"],
            expected_outcome=SCENARIO_METADATA[0]["expected_outcome"],
            shipment_id=s1.id,
            tracking_number=trk_1,
            status=s1.status.value,
            verification_decision=dec_1_str,
            payment_status=p1_status,
        )
    )

    # 2. SCENARIO 2: Thermal Excursion
    trk_2 = "CHALLENGE-02-EXCURSION"
    s2 = db.scalar(select(Shipment).where(Shipment.tracking_number == trk_2))
    if not s2:
        s2 = shipment_service.create_shipment(
            db=db, org_id=org_id, product_profile_id=profile.id,
            tracking_number=trk_2, origin="Munich Biotech Hub", destination="Rome Policlinico",
            created_by_user_id=user_id,
        )
        shipment_service.update_shipment_status(db=db, org_id=org_id, shipment_id=s2.id, new_status=ShipmentStatus.IN_TRANSIT)
        shipment_service.update_shipment_status(db=db, org_id=org_id, shipment_id=s2.id, new_status=ShipmentStatus.DELIVERED)

        csv_excursion = (
            b"timestamp,temperature,sensor_id\n"
            b"2026-11-01T08:00:00Z,13.8,LOGGER-B2\n"
            b"2026-11-01T08:05:00Z,14.5,LOGGER-B2\n"
            b"2026-11-01T08:10:00Z,14.0,LOGGER-B2\n"
        )
        evidence_service.upload_evidence(
            db=db, org_id=org_id, shipment_id=s2.id, file_type=EvidenceType.LOGGER_CSV,
            original_filename="excursion_telemetry.csv", content=csv_excursion, uploaded_by_user_id=user_id,
        )
        custody_service.record_custody_transfer(
            db=db, org_id=org_id, shipment_id=s2.id, event_type=CustodyEventType.DISPATCH,
            carrier_name="Alitalia Cargo", custodian_name="G. Rossi", location="Munich Airport",
            actor_user_id=user_id,
        )
        dec_2 = temperature_service.evaluate_shipment_compliance(db=db, org_id=org_id, shipment_id=s2.id, decided_by_user_id=user_id)
        payment_service.create_payment(
            db=db, org_id=org_id, shipment_id=s2.id, amount=Decimal("8000.00"), currency="USD", user_id=user_id,
        )
        investigation_service.create_investigation(
            db=db,
            org_id=org_id,
            shipment_id=s2.id,
            priority=InvestigationPriority.HIGH,
            findings="Thermal spike to 14.5°C during Munich-Rome tarmac transit. Excursion duration 900s exceeded permitted 600s ceiling. Automated verification failed; payment capture halted.",
            actor_user_id=user_id,
        )
        dec_2_str = dec_2.decision.value
        p2_status = "AUTHORIZED (CAPTURE_BLOCKED)"
    else:
        dec_2_str = "FAILED"
        p2_status = "AUTHORIZED (CAPTURE_BLOCKED)"
        inv = db.scalar(select(Investigation).where(Investigation.shipment_id == s2.id))
        if not inv:
            investigation_service.create_investigation(
                db=db,
                org_id=org_id,
                shipment_id=s2.id,
                priority=InvestigationPriority.HIGH,
                findings="Thermal spike to 14.5°C during Munich-Rome tarmac transit. Excursion duration 900s exceeded permitted 600s ceiling. Automated verification failed; payment capture halted.",
                actor_user_id=user_id,
            )

    scenarios.append(
        ChallengeScenarioResponse(
            scenario_id="thermal-excursion",
            title=SCENARIO_METADATA[1]["title"],
            description=SCENARIO_METADATA[1]["description"],
            expected_outcome=SCENARIO_METADATA[1]["expected_outcome"],
            shipment_id=s2.id,
            tracking_number=trk_2,
            status=s2.status.value,
            verification_decision=dec_2_str,
            payment_status=p2_status,
        )
    )

    # 3. SCENARIO 3: Evidence Tamper Anomaly
    trk_3 = "CHALLENGE-03-TAMPER"
    s3 = db.scalar(select(Shipment).where(Shipment.tracking_number == trk_3))
    if not s3:
        s3 = shipment_service.create_shipment(
            db=db, org_id=org_id, product_profile_id=profile.id,
            tracking_number=trk_3, origin="Copenhagen Lab", destination="Stockholm Karolinska",
            created_by_user_id=user_id,
        )
        payment_service.create_payment(
            db=db, org_id=org_id, shipment_id=s3.id, amount=Decimal("9500.00"), currency="USD", user_id=user_id,
        )
    scenarios.append(
        ChallengeScenarioResponse(
            scenario_id="evidence-tamper",
            title=SCENARIO_METADATA[2]["title"],
            description=SCENARIO_METADATA[2]["description"],
            expected_outcome=SCENARIO_METADATA[2]["expected_outcome"],
            shipment_id=s3.id,
            tracking_number=trk_3,
            status=s3.status.value,
            verification_decision="TAMPER_DETECTED",
            payment_status="HELD_FOR_REVIEW",
        )
    )

    # 4. SCENARIO 4: Custody Gap
    trk_4 = "CHALLENGE-04-CUSTODY"
    s4 = db.scalar(select(Shipment).where(Shipment.tracking_number == trk_4))
    if not s4:
        s4 = shipment_service.create_shipment(
            db=db, org_id=org_id, product_profile_id=profile.id,
            tracking_number=trk_4, origin="Seoul Central Medical", destination="Tokyo Todai Hospital",
            created_by_user_id=user_id,
        )
        payment_service.create_payment(
            db=db, org_id=org_id, shipment_id=s4.id, amount=Decimal("11000.00"), currency="USD", user_id=user_id,
        )
    scenarios.append(
        ChallengeScenarioResponse(
            scenario_id="custody-gap",
            title=SCENARIO_METADATA[3]["title"],
            description=SCENARIO_METADATA[3]["description"],
            expected_outcome=SCENARIO_METADATA[3]["expected_outcome"],
            shipment_id=s4.id,
            tracking_number=trk_4,
            status=s4.status.value,
            verification_decision="MANUAL_REVIEW_REQUIRED",
            payment_status="HELD_FOR_REVIEW",
        )
    )

    return scenarios
