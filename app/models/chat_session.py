from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, relationship

from app.db.database import Base
from app.models import mapped_column
from app.utils.mixins import TimestampMixin


class ChatSession(TimestampMixin, Base):
    __tablename__ = 'chat_session'

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey('patient.id'))

    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer)
    is_completed: Mapped[bool] = mapped_column(default=False)

    # Store the conversation
    conversation_data: Mapped[dict] = mapped_column(JSON)

    # Store prediction results
    prediction_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    patient = relationship('Patient', backref='chat_sessions')
