from typing import Optional

from sqlalchemy import String, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.enums import DiseaseType
from app.utils.mixins import ModifiedMixin, ActivationMixin


class Disease(ActivationMixin, ModifiedMixin, Base):
    __tablename__ = 'disease'

    id: Mapped[int] = mapped_column(primary_key=True)

    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey('disease.id'), nullable=True)

    code: Mapped[str] = mapped_column(String(100), unique=True) # e.g. ICD-10 code or custom
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(Enum(DiseaseType), name='disease_type')
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # target_group: str = Column(String(255), nullable=False)

    symptoms = relationship('DiseaseSymptom', back_populates='disease')
    anatomies = relationship('DiseaseAnatomy', back_populates='disease')
    treatments = relationship('DiseaseTreatment', back_populates='disease')
