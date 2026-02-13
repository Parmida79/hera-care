from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped

from hera_care.db.database import Base
from hera_care.models import mapped_column
from hera_care.utils.mixins import ActivationMixin, TimestampMixin


class DiseaseTreatment(ActivationMixin, TimestampMixin, Base):
    __tablename__ = 'disease_treatment'

    id: Mapped[int] = mapped_column(primary_key=True)

    disease_id: Mapped[int] = mapped_column(ForeignKey('disease.id'))
    treatment_id: Mapped[int] = mapped_column(ForeignKey('treatment.id'))

    is_recommended: Mapped[bool] = mapped_column(default=True)

    disease = relationship('Disease', back_populates='treatments')
    treatment = relationship('Treatment', back_populates='diseases')
