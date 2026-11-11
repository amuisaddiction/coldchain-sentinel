"""Payment schemas for authorization, capture, and display."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PaymentStatus


class PaymentCreate(BaseModel):
    shipment_id: str = Field(..., description="UUID of the shipment")
    amount: Decimal = Field(..., gt=0, description="Payment amount in decimal format (e.g. 5000.00)")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO-4217 3-letter currency code")
    paypal_order_id: Optional[str] = Field(None, description="PayPal Order ID if authorized via PayPal checkout")
    paypal_authorization_id: Optional[str] = Field(None, description="PayPal Authorization ID")


class PaymentCaptureRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Approval notes for payment capture")


class PaymentResponse(BaseModel):
    id: str
    shipment_id: str
    organization_id: str
    payment_provider: str
    paypal_order_id: Optional[str]
    paypal_authorization_id: Optional[str]
    paypal_capture_id: Optional[str]
    amount_minor: int
    amount_decimal: str
    currency: str
    currency_exponent: int
    status: PaymentStatus
    authorized_at: Optional[datetime]
    settled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
