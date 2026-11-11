"""Carrier intelligence service computing transparent performance metrics from recorded shipment data."""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, distinct

from app.models.custody import CustodyEvent
from app.models.shipment import Shipment
from app.models.decision import VerificationDecision
from app.models.enums import DecisionType
from app.schemas.carrier import CarrierScoreResponse, CarrierIntelligenceSummary


def get_carrier_scores(db: Session, org_id: str) -> CarrierIntelligenceSummary:
    """Compute transparent performance statistics for all carriers operating in the organization."""
    # Find all carriers in custody events
    events = list(
        db.scalars(
            select(CustodyEvent)
            .where(CustodyEvent.organization_id == org_id)
        ).all()
    )

    if not events:
        return CarrierIntelligenceSummary(total_carriers_tracked=0, carriers=[])

    # Map carrier -> set of shipment_ids
    carrier_shipments: Dict[str, set] = {}
    for ev in events:
        c_name = ev.carrier_name.strip()
        if c_name not in carrier_shipments:
            carrier_shipments[c_name] = set()
        carrier_shipments[c_name].add(ev.shipment_id)

    # Get decisions for all shipments in this org
    decisions = list(
        db.scalars(
            select(VerificationDecision)
            .where(VerificationDecision.organization_id == org_id)
        ).all()
    )
    decision_map = {d.shipment_id: d.decision for d in decisions}

    carrier_results: List[CarrierScoreResponse] = []
    for c_name, ship_ids in carrier_shipments.items():
        total = len(ship_ids)
        passed_count = sum(1 for s_id in ship_ids if decision_map.get(s_id) == DecisionType.PASSED)
        failed_count = sum(1 for s_id in ship_ids if decision_map.get(s_id) == DecisionType.FAILED)

        rate = round((passed_count / total) * 100.0, 1) if total > 0 else 100.0
        score = rate
        is_low_sample = total < 5
        note = "Reliable historical sample" if not is_low_sample else f"Low sample size warning: based on {total} recorded shipment(s)"

        carrier_results.append(
            CarrierScoreResponse(
                carrier_name=c_name,
                total_shipments=total,
                compliant_shipments=passed_count,
                excursion_shipments=failed_count,
                compliance_rate_percent=rate,
                reliability_score=score,
                sample_size_warning=is_low_sample,
                sample_size_note=note,
            )
        )

    carrier_results.sort(key=lambda c: c.reliability_score, reverse=True)
    return CarrierIntelligenceSummary(
        total_carriers_tracked=len(carrier_results),
        carriers=carrier_results,
    )
