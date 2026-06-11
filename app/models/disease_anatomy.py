from typing import Optional

from sqlalchemy import ForeignKey, Enum, String
from sqlalchemy.orm import relationship, Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.enums import DiseaseAnatomySeverity
from app.utils.mixins import ActivationMixin, TimestampMixin


# disease affected anatomy
class DiseaseAnatomy(ActivationMixin, TimestampMixin, Base):
    __tablename__ = 'disease_anatomy'

    id: Mapped[int] = mapped_column(primary_key=True)

    disease_id: Mapped[int] = mapped_column(ForeignKey('disease.id'))
    anatomy_id: Mapped[int] = mapped_column(ForeignKey('anatomy.id'))

    is_primary_affected: Mapped[bool] = mapped_column(default=None)
    effect_type: Mapped[str] = mapped_column(String(255))  # e.g., inflammation, dysfunction, hyperplasia, atrophy
    severity: Mapped[str] = mapped_column(Enum(DiseaseAnatomySeverity), name='disease_anatomy_severity')
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    disease = relationship('Disease', back_populates='anatomies')
    anatomy = relationship('Anatomy', back_populates='diseases')
