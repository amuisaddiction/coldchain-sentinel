"""User model for authenticated operators, auditors, and administrators."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from app.core.database import Base, UTCDateTime
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = sa.Column(
        sa.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    organization_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = sa.Column(sa.String(255), unique=True, index=True, nullable=False)
    hashed_password = sa.Column(sa.String(255), nullable=False)
    full_name = sa.Column(sa.String(255), nullable=False)
    role = sa.Column(
        sa.Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.OPERATOR,
    )
    is_active = sa.Column(sa.Boolean, nullable=False, default=True)
    token_version = sa.Column(sa.Integer, nullable=False, default=1)
    created_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = sa.Column(
        UTCDateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        sa.UniqueConstraint("id", "organization_id", name="uq_users_id_org"),
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
