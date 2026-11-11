"""Temperature intelligence API router."""

from typing import List
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    require_operator_or_above,
    get_client_ip,
)
from app.models.user import User
from app.models.temperature import TemperatureReading
from app.schemas.temperature import (
    TemperatureReadingResponse,
    TemperatureSummaryResponse,
)
from app.schemas.decision import VerificationDecisionResponse
from app.services import temperature_service

router = APIRouter(prefix="/shipments/{shipment_id}/temperature", tags=["Temperature Intelligence"])


@router.get("/readings", response_model=List[TemperatureReadingResponse])
def get_temperature_readings(
    shipment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve temperature readings for a shipment."""
    return list(
        db.scalars(
            select(TemperatureReading)
            .where(TemperatureReading.shipment_id == shipment_id)
            .order_by(TemperatureReading.recorded_at.asc())
        ).all()
    )


@router.get("/summary", response_model=TemperatureSummaryResponse)
def get_temperature_summary(
    shipment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Calculate and return aggregate temperature metrics and excursion summary."""
    return temperature_service.get_temperature_summary(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
    )


@router.post("/evaluate", response_model=VerificationDecisionResponse)
def evaluate_compliance(
    request: Request,
    shipment_id: str,
    current_user: User = Depends(require_operator_or_above),
    db: Session = Depends(get_db),
):
    """Evaluate temperature compliance against immutable rule snapshot and record a verification decision."""
    client_ip = get_client_ip(request)
    return temperature_service.evaluate_shipment_compliance(
        db=db,
        org_id=current_user.organization_id,
        shipment_id=shipment_id,
        decided_by_user_id=current_user.id,
        client_ip=client_ip,
    )
