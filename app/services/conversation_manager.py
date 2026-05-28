from typing import Dict, Any, Optional, List, Tuple
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
        self.conversation_history: List[Dict[str, str]] = []

        # Question flow configuration
        self.questions = self._initialize_questions()

    def _initialize_questions(self) -> List[Dict[str, Any]]:
        """
        Define the conversation flow with questions and validation
        """
        return [
            {
                "key": "consent",
                "question": "سلام! من دستیار سلامت شما هستم. 🌸\n\nبرای بررسی احتمال سندرم تخمدان پلی‌کیستیک (PCOS)، نیاز به پاسخ چند سوال دارم.\n\nآیا آماده‌اید؟ (بله/خیر)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no']
            },
            {
                "key": "Age (yrs)",
                "question": "سن شما چند سال است؟",
                "type": "numeric",
                "required": True,
                "validation": lambda x: 15 <= float(x) <= 60,
                "error_message": "لطفاً سن معتبر (15-60) وارد کنید"
            },
            {
                "key": "Weight (Kg)",
                "question": "وزن شما چند کیلوگرم است؟",
                "type": "numeric",
                "required": True,
                "validation": lambda x: 30 <= float(x) <= 200,
                "error_message": "لطفاً وزن معتبر وارد کنید"
            },
            {
                "key": "Height(Cm)",
                "question": "قد شما چند سانتی‌متر است؟",
                "type": "numeric",
                "required": True,
                "validation": lambda x: 130 <= float(x) <= 220,
                "error_message": "لطفاً قد معتبر وارد کنید"
            },
            {
                "key": "Cycle(R/I)",
                "question": "چرخه قاعدگی شما منظم است؟ (بله: منظم / خیر: نامنظم)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no'],
                "transform": lambda x: 0 if x.lower() in ['بله', 'yes'] else 1
                # 0=Regular, 1=Irregular
            },
            {
                "key": "Cycle length(days)",
                "question": "چرخه قاعدگی شما معمولاً چند روز است؟ (معمولاً 21-35 روز)",
                "type": "numeric",
                "required": True,
                "validation": lambda x: 15 <= float(x) <= 60
            },
            {
                "key": "Weight gain(Y/N)",
                "question": "آیا اخیراً افزایش وزن ناخواسته داشته‌اید؟ (بله/خیر)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no'],
                "transform": lambda x: 1 if x.lower() in ['بله', 'yes'] else 0
            },
            {
                "key": "hair growth(Y/N)",
                "question": "آیا رشد موهای زائد (صورت، سینه، شکم) دارید؟ (بله/خیر)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no'],
                "transform": lambda x: 1 if x.lower() in ['بله', 'yes'] else 0
            },
            {
                "key": "Skin darkening (Y/N)",
                "question": "آیا تیره شدن پوست در نواحی گردن، زیر بغل یا کشاله ران دارید؟ (بله/خیر)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no'],
                "transform": lambda x: 1 if x.lower() in ['بله', 'yes'] else 0
            },
            {
                "key": "Pimples(Y/N)",
                "question": "آیا آکنه یا جوش صورت مداوم دارید؟ (بله/خیر)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no'],
                "transform": lambda x: 1 if x.lower() in ['بله', 'yes'] else 0
            },
            {
                "key": "Fast food (Y/N)",
                "question": "آیا بیش از 3 بار در هفته فست‌فود مصرف می‌کنید؟ (بله/خیر)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no'],
                "transform": lambda x: 1 if x.lower() in ['بله', 'yes'] else 0
            },
            {
                "key": "Reg.Exercise(Y/N)",
                "question": "آیا به طور منظم ورزش می‌کنید؟ (حداقل 3 بار در هفته) (بله/خیر)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ['بله', 'خیر', 'yes',
                                                      'no'],
                "transform": lambda x: 1 if x.lower() in ['بله', 'yes'] else 0
            },
            # Add more questions as needed for all 41 features
        ]

    def update(self, key: str, value: Any):
        """Update conversation data with validation"""
        self.data[key] = value
        self.last_active = datetime.utcnow()

    def add_to_history(self, role: str, message: str):
        """Track conversation history"""
        self.conversation_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_next_question(self) -> Optional[str]:
        """Get the next question in the flow"""
        if self.current_step >= len(self.questions):
            return None

        question_config = self.questions[self.current_step]
        return question_config["question"]

    def validate_answer(self, answer: str) -> Tuple[bool, Optional[str]]:
        """Validate user's answer for current question"""
        if self.current_step >= len(self.questions):
            return False, "سوالات تمام شده است"

        question_config = self.questions[self.current_step]

        try:
            if question_config["validation"](answer):
                # Transform if needed
                if "transform" in question_config:
                    transformed_value = question_config["transform"](answer)
                    self.update(question_config["key"], transformed_value)
                else:
                    # Store as numeric or string
                    if question_config["type"] == "numeric":
                        self.update(question_config["key"], float(answer))
                    else:
                        self.update(question_config["key"], answer)

                return True, None
            else:
                return False, question_config.get("error_message",
                                                  "پاسخ نامعتبر است")
        except:
            return False, question_config.get("error_message",
                                              "پاسخ نامعتبر است")

    def advance(self):
        """Move to next question"""
        self.current_step += 1

    def is_complete(self) -> bool:
        """Check if all questions are answered"""
        return self.current_step >= len(self.questions)

    def get_progress(self) -> Dict[str, Any]:
        """Get conversation progress"""
        return {
            "current_step": self.current_step,
            "total_steps": len(self.questions),
            "percentage": int(
                (self.current_step / len(self.questions)) * 100) if len(
                self.questions) > 0 else 0
        }


class ConversationManager:
    _sessions: Dict[str, ConversationState] = {}

    @classmethod
    def create(cls) -> ConversationState:
        """Create new conversation session"""
        session_id = str(uuid.uuid4())
        state = ConversationState(session_id)
        cls._sessions[session_id] = state
        return state

    @classmethod
    def get(cls, session_id: str) -> Optional[ConversationState]:
        """Retrieve existing session"""
        return cls._sessions.get(session_id)

    @classmethod
    def cleanup_old(cls, max_age_minutes: int = 60):
        """Remove old inactive sessions"""
        now = datetime.utcnow()
        to_remove = [
            sid for sid, state in cls._sessions.items()
            if (now - state.last_active).total_seconds() > max_age_minutes * 60
        ]
        for sid in to_remove:
            del cls._sessions[sid]

    @classmethod
    def delete(cls, session_id: str):
        """Delete a specific session"""
        if session_id in cls._sessions:
            del cls._sessions[session_id]
