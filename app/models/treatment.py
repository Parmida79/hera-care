from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import relationship, Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.mixins import ModifiedMixin, ActivationMixin


class Treatment(ActivationMixin, ModifiedMixin, Base):
    __tablename__ = 'treatment'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # evidence_level
    type: Mapped[str] = mapped_column(String)

    diseases = relationship('DiseaseTreatment', back_populates='treatment')

    __mapper_args__ = {
        'polymorphic_identity': 'treatment',
        'polymorphic_on': type,
    }


class Medication(Treatment):

    dosage_form: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., 'tablet', 'syrup'
    typical_dosage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # e.g., '500mg daily'
    side_effects: Mapped[Optional[list]] = mapped_column(nullable=True)  # e.g., ["nausea", "headache"]

    __mapper_args__ = {
        'polymorphic_identity': 'medication',
    }


class LifeStyle(Treatment):

    routine: Mapped[str] = mapped_column(Text, nullable=True)  # e.g., '30min yoga weekly' (NULL for medication)

    __mapper_args__ = {
        'polymorphic_identity': 'life-style',
    }
