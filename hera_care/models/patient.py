from datetime import date

from sqlalchemy import String, Enum
from sqlalchemy.orm import relationship, Mapped

from hera_care.utils.enums import Gender, MaritalStatus, BloodGroup
from hera_care.utils.mixins import AutoActivationMixin, ModifiedMixin
from hera_care.db.database import Base
from hera_care.models import mapped_column


class Patient(AutoActivationMixin, ModifiedMixin, Base):
    __tablename__ = 'patient'

    id: Mapped[int] = mapped_column(primary_key=True)  # might change to UUID later

    username: Mapped[str] = mapped_column(String(255), unique=True)  # for login/chatbot auth
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)  #unique + validation
    phone_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)  # optional but unique if provided

    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[date]
    gender: Mapped[str] = mapped_column(Enum(Gender), name='gender')
    marital_status: Mapped[str] = mapped_column(Enum(MaritalStatus), name='marital_status', default='Unknown')
    blood_group: Mapped[str] = mapped_column(Enum(BloodGroup), name='blood_group', default='unknown')
    weight_kg: Mapped[float]  # decimal  NUMERIC(6,2)
    height_cm: Mapped[float]  # decimal  NUMERIC(5,2)
    # BMI should be calculated based on weight and height
    # age could be calculated based on DOB

    medical_histories = relationship('MedicalHistory', back_populates='patient')
