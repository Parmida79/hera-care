from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Mapped

from app.db.database import Base
from app.models import mapped_column
from app.utils.mixins import ActivationMixin, TimestampMixin


class DiseaseTreatment(ActivationMixin, TimestampMixin, Base):
    __tablename__ = 'disease_treatment'

    id: Mapped[int] = mapped_column(primary_key=True)

    disease_id: Mapped[int] = mapped_column(ForeignKey('disease.id'))
    treatment_id: Mapped[int] = mapped_column(ForeignKey('treatment.id'))

    is_recommended: Mapped[bool] = mapped_column(default=True)

    disease = relationship('Disease', back_populates='treatments')
    treatment = relationship('Treatment', back_populates='diseases')
