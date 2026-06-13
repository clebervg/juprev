import uuid

from sqlalchemy import Boolean, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """Usuário vinculado a um tenant (escritório). tenant_id é obrigatório."""

    __tablename__ = "users"

    # MULTI-TENANCY: tenant_id garante isolamento total entre escritórios.
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # LGPD: senha armazenada apenas como hash bcrypt (custo 12).
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")  # noqa: F821
