from typing import Optional, List

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.mixins import ModifiedMixin, ActivationMixin


class Treatment(ActivationMixin, ModifiedMixin, Base):
    __tablename__ = 'treatment'

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50))

    diseases = relationship('DiseaseTreatment', back_populates='treatment')

    __mapper_args__ = {
        'polymorphic_identity': 'treatment',
        'polymorphic_on': type,
    }


class Medication(Treatment):
    """
    # Creating a medication with side effects
    medication = Medication(
        name="Metformin",
        dosage_form="tablet",
        typical_dosage="500mg twice daily",
        side_effects=["nausea", "diarrhea", "stomach upset"]
    )

    # Querying
    meds = session.query(Medication).filter(
        Medication.side_effects.contains(["nausea"])
    ).all()
    """
    __tablename__ = 'medication'

    id: Mapped[int] = mapped_column(ForeignKey('treatment.id'), primary_key=True)

    dosage_form: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., 'tablet', 'syrup'
    typical_dosage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # e.g., '500mg daily'

    side_effects: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)  # e.g., ["nausea", "headache"]

    __mapper_args__ = {
        'polymorphic_identity': 'medication',
    }


class LifeStyle(Treatment):
    __tablename__ = 'lifestyle'

    id: Mapped[int] = mapped_column(ForeignKey('treatment.id'), primary_key=True)

    routine: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'life-style',
    }
