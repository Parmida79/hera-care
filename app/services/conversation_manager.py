from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class ConversationState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.current_step = 0
        self.data: Dict[str, Any] = {}
        self.patient_id: Optional[str] = None
        self.last_active = datetime.utcnow()

    def update(self, key: str, value: Any):
        self.data[key] = value
        self.last_active = datetime.utcnow()

    def get_next_question(self) -> str:
        # منطق درخت سؤالات بر اساس current_step و data
        questions = [
            "سلام! آیا موافقید اطلاعات وارد کنید؟ (بله/خیر)",
            "لطفاً نام کاربری یا ایمیل وارد کنید",
            "جنسیت شما؟ (زن/مرد/دیگر)",
            "سن شما چند سال است؟",
            "قد شما (سانتی‌متر) و وزن شما (کیلوگرم)؟",
            # ... بقیه سؤالات
        ]
        if self.current_step < len(questions):
            return questions[self.current_step]
        return "ممنون! اطلاعات کافی جمع شد. در حال بررسی هستم..."

    def advance(self):
        self.current_step += 1


class ConversationManager:
    _sessions: Dict[str, ConversationState] = {}

    @classmethod
    def create(cls) -> ConversationState:
        session_id = str(uuid.uuid4())
        state = ConversationState(session_id)
        cls._sessions[session_id] = state
        return state

    @classmethod
    def get(cls, session_id: str) -> Optional[ConversationState]:
        return cls._sessions.get(session_id)

    @classmethod
    def cleanup_old(cls, max_age_minutes: int = 60):
        now = datetime.utcnow()
        to_remove = [
            sid for sid, state in cls._sessions.items()
            if (now - state.last_active).total_seconds() > max_age_minutes * 60
        ]
        for sid in to_remove:
            del cls._sessions[sid]