from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid
from enum import Enum


class AssessmentSection(Enum):
    ONBOARDING = "onboarding"           # Basic info everyone knows
    SYMPTOMS = "symptoms"               # Observable symptoms
    LIFESTYLE = "lifestyle"             # Daily habits
    VITALS = "vitals"                   # BP, pulse (optional)
    LAB_RESULTS = "lab_results"         # Blood tests (optional)
    ULTRASOUND = "ultrasound"           # Imaging (optional)
    # Future sections:
    # MEDICATION = "medication"         # Current medications
    # MENTAL_HEALTH = "mental_health"   # Stress, sleep, mood


class ConversationState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.current_step = 0
        self.data: Dict[str, Any] = {}
        self.patient_id: Optional[str] = None
        self.last_active = datetime.utcnow()
        self.conversation_history: List[Dict[str, str]] = []
        self.skipped_steps: List[int] = []
        self.completed_sections: List[str] = []
        self.skipped_sections: List[str] = []

        self.questions = self._build_questions()

    def _build_questions(self) -> List[Dict[str, Any]]:
        """Build question flow organized by sections"""
        questions = []
        questions.extend(self._onboarding_questions())
        questions.extend(self._symptom_questions())
        questions.extend(self._lifestyle_questions())
        questions.extend(self._vitals_questions())
        questions.extend(self._lab_questions())
        questions.extend(self._ultrasound_questions())
        return questions

    def _onboarding_questions(self) -> List[Dict[str, Any]]:
        """Basic info that everyone knows"""
        return [
            {
                "key": "consent",
                "question": """
                سلام! من دستیار سلامت هِرا کِر هستم. 🌸
                برای بررسی احتمال سندرم تخمدان پلی‌کیستیک (PCOS) نیاز به پاسخ چند سوال دارم.
                اطلاعات شما کاملاً محرمانه خواهد ماند.
                ⏱ زمان تقریبی: ۳ تا ۵ دقیقه
                آیا آماده‌اید؟ (بله/خیر)""",
                "type": "boolean",
                "section": AssessmentSection.ONBOARDING,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: x.strip().lower(),
                "error_message": "لطفاً فقط 'بله' یا 'خیر' وارد کنید",
                "exit_on": lambda x: x.strip().lower() in ['خیر', 'no'],
                "exit_message": "ممنون از وقتتون. هر زمان آماده بودید، دوباره تشریف بیارید! 🌸"
            },
            {
                "key": "date_of_birth",
                "question": "📅 تاریخ تولد شما؟\n(فرمت: YYYY-MM-DD مثلاً 1999-03-15)",
                "type": "date",
                "section": AssessmentSection.ONBOARDING,
                "validation": lambda x: self._validate_date(x),
                "transform": lambda x: self._parse_date(x),
                "error_message": "لطفاً تاریخ معتبر وارد کنید (مثال: 1999-03-15)\nسن باید بین ۱۵ تا ۶۰ سال باشد"
            },
            {
                "key": "Weight (Kg)",
                "question": "⚖️ وزن شما چند کیلوگرم است؟",
                "type": "numeric",
                "section": AssessmentSection.ONBOARDING,
                "validation": lambda x: 30 <= float(x) <= 200,
                "transform": lambda x: float(x),
                "error_message": "لطفاً وزن معتبر (۳۰-۲۰۰ کیلوگرم) وارد کنید"
            },
            {
                "key": "Height(Cm)",
                "question": "📏 قد شما چند سانتی‌متر است؟",
                "type": "numeric",
                "section": AssessmentSection.ONBOARDING,
                "validation": lambda x: 130 <= float(x) <= 220,
                "transform": lambda x: float(x),
                "error_message": "لطفاً قد معتبر (۱۳۰-۲۲۰ سانتی‌متر) وارد کنید"
            },
            {
                "key": "Marraige Status (Yrs)",
                "question": "💍 وضعیت تأهل شما؟\n"
                            "اگر مجرد هستید عدد ۰ را وارد کنید.\n"
                            "اگر متأهل هستید تعداد سال‌های ازدواج را وارد کنید.",
                "type": "numeric",
                "section": AssessmentSection.ONBOARDING,
                "validation": lambda x: 0 <= float(x) <= 40,
                "transform": lambda x: float(x),
                "error_message": "لطفاً عدد معتبر وارد کنید"
            },
            {
                "key": "Pregnant(Y/N)",
                "question": "🤰 آیا تا به حال باردار شده‌اید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.ONBOARDING,
                "condition": lambda data: data.get('Marraige Status (Yrs)', 0) > 0,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
            {
                "key": "No. of aborptions",
                "question": "تعداد سقط (اگر داشته‌اید)؟ اگر نداشته‌اید عدد ۰ وارد کنید.",
                "type": "numeric",
                "section": AssessmentSection.ONBOARDING,
                "condition": lambda data: data.get('Pregnant(Y/N)') == 1,
                "validation": lambda x: 0 <= float(x) <= 10,
                "transform": lambda x: float(x),
            },
            {
                "key": "Cycle(R/I)",
                "question": "📅 آیا چرخه قاعدگی شما منظم است؟\n(بله: منظم / خیر: نامنظم)",
                "type": "boolean",
                "section": AssessmentSection.ONBOARDING,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 0 if x.strip().lower() in ['بله', 'yes'] else 1,
            },
            {
                "key": "Cycle length(days)",
                "question": "📅 طول چرخه قاعدگی شما معمولاً چند روز است؟\n(طبیعی: ۲۱ تا ۳۵ روز | در PCOS ممکن است بیشتر از ۳۵ روز باشد)",
                "type": "numeric",
                "section": AssessmentSection.ONBOARDING,
                "validation": lambda x: 10 <= float(x) <= 180,
                "transform": lambda x: float(x),
                "error_message": "لطفاً عدد معتبر بین ۱۰ تا ۱۸۰ وارد کنید"
            },
        ]

    def _symptom_questions(self) -> List[Dict[str, Any]]:
        """Observable symptoms the patient can identify"""
        return [
            {
                "key": "_symptom_intro",
                "question": "✅ اطلاعات پایه ثبت شد!"
                            "📋 بخش ۲: علائم ظاهری\n"
                            "حالا چند سوال درباره علائمی که ممکنه داشته باشید می‌پرسم.\n"
                            "ادامه می‌دهید؟ (بله/خیر)",
                "type": "section_intro",
                "section": AssessmentSection.SYMPTOMS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: x.strip().lower(),
                "skip_section_on": lambda x: x.strip().lower() in ['خیر', 'no'],
            },
            {
                "key": "Weight gain(Y/N)",
                "question": "⚖️ آیا اخیراً افزایش وزن غیرمعمول داشته‌اید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.SYMPTOMS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
            {
                "key": "hair growth(Y/N)",
                "question": "💇‍♀️ آیا رشد موهای زائد در صورت، سینه یا شکم دارید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.SYMPTOMS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
            {
                "key": "Skin darkening (Y/N)",
                "question": "🔲 آیا تیره شدن پوست در گردن، زیر بغل یا کشاله ران دارید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.SYMPTOMS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
            {
                "key": "Hair loss(Y/N)",
                "question": "💇 آیا ریزش مو یا نازک شدن مو دارید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.SYMPTOMS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
            {
                "key": "Pimples(Y/N)",
                "question": "😟 آیا آکنه یا جوش صورت مداوم دارید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.SYMPTOMS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
        ]

    def _lifestyle_questions(self) -> List[Dict[str, Any]]:
        """Daily habits and lifestyle"""
        return [
            {
                "key": "_lifestyle_intro",
                "question": "✅ علائم ثبت شد!\n\n"
                            "━━━━━━━━━━━━━━━\n"
                            "📋 بخش ۳: سبک زندگی\n"
                            "━━━━━━━━━━━━━━━\n\n"
                            "چند سوال کوتاه درباره عادات روزانه.\n"
                            "ادامه می‌دهید؟ (بله/خیر)",
                "type": "section_intro",
                "section": AssessmentSection.LIFESTYLE,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: x.strip().lower(),
                "skip_section_on": lambda x: x.strip().lower() in ['خیر', 'no'],
            },
            {
                "key": "Fast food (Y/N)",
                "question": "🍔 آیا بیش از ۳ بار در هفته فست‌فود مصرف می‌کنید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.LIFESTYLE,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
            {
                "key": "Reg.Exercise(Y/N)",
                "question": "🏃‍♀️ آیا حداقل ۳ بار در هفته ورزش می‌کنید؟ (بله/خیر)",
                "type": "boolean",
                "section": AssessmentSection.LIFESTYLE,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: 1 if x.strip().lower() in ['بله', 'yes'] else 0,
            },
        ]

    def _vitals_questions(self) -> List[Dict[str, Any]]:
        """Blood pressure, pulse - many people know these"""
        return [
            {
                "key": "_vitals_intro",
                "question": "✅ سبک زندگی ثبت شد!\n\n"
                            "━━━━━━━━━━━━━━━\n"
                            "📋 بخش ۴: علائم حیاتی (اختیاری)\n"
                            "━━━━━━━━━━━━━━━\n\n"
                            "اگر فشار خون و ضربان قلب خود را می‌دانید، دقت تشخیص بالاتر می‌رود.\n\n"
                            "آیا این اطلاعات را دارید؟ (بله/خیر)",
                "type": "section_intro",
                "section": AssessmentSection.VITALS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: x.strip().lower(),
                "skip_section_on": lambda x: x.strip().lower() in ['خیر', 'no'],
            },
            {
                "key": "BP _Systolic (mmHg)",
                "question": "🩺 فشار خون سیستولیک (عدد بالا)؟\n(مثلاً ۱۲۰)",
                "type": "numeric",
                "section": AssessmentSection.VITALS,
                "validation": lambda x: 70 <= float(x) <= 200,
                "transform": lambda x: float(x),
            },
            {
                "key": "BP_ Diastolic (mmHg)",
                "question": "🩺 فشار خون دیاستولیک (عدد پایین)؟\n(مثلاً ۸۰)",
                "type": "numeric",
                "section": AssessmentSection.VITALS,
                "validation": lambda x: 40 <= float(x) <= 130,
                "transform": lambda x: float(x),
            },
            {
                "key": "Pulse rate(bpm)",
                "question": "💓 ضربان قلب (تعداد در دقیقه)؟\n(طبیعی: ۶۰-۱۰۰)",
                "type": "numeric",
                "section": AssessmentSection.VITALS,
                "validation": lambda x: 40 <= float(x) <= 150,
                "transform": lambda x: float(x),
            },
            {
                "key": "RR (breaths/min)",
                "question": "🫁 تعداد تنفس در دقیقه؟\n(طبیعی: ۱۲-۲۰)\n(اگر نمی‌دانید 'نمیدانم' بنویسید)",
                "type": "numeric_optional",
                "section": AssessmentSection.VITALS,
                "validation": lambda x: x.strip() in ['نمیدانم', 'نمی دانم'] or 8 <= float(x) <= 40,
                "transform": lambda x: None if x.strip() in ['نمیدانم', 'نمی دانم'] else float(x),
            },
            {
                "key": "Hip(inch)",
                "question": "📐 دور باسن (اینچ)؟\n(اگر نمی‌دانید 'نمیدانم' بنویسید)",
                "type": "numeric_optional",
                "section": AssessmentSection.VITALS,
                "validation": lambda x: x.strip() in ['نمیدانم', 'نمی دانم'] or 25 <= float(x) <= 60,
                "transform": lambda x: None if x.strip() in ['نمیدانم', 'نمی دانم'] else float(x),
            },
            {
                "key": "Waist(inch)",
                "question": "📐 دور کمر (اینچ)؟\n(اگر نمی‌دانید 'نمیدانم' بنویسید)",
                "type": "numeric_optional",
                "section": AssessmentSection.VITALS,
                "validation": lambda x: x.strip() in ['نمیدانم', 'نمی دانم'] or 20 <= float(x) <= 55,
                "transform": lambda x: None if x.strip() in ['نمیدانم', 'نمی دانم'] else float(x),
            },
        ]

    def _lab_questions(self) -> List[Dict[str, Any]]:
        """Blood test results - most users won't have these"""
        return [
            {
                "key": "_lab_intro",
                "question": "━━━━━━━━━━━━━━━\n"
                            "📋 بخش ۵: نتایج آزمایش خون (اختیاری)\n"
                            "━━━━━━━━━━━━━━━\n\n"
                            "اگر اخیراً آزمایش خون داده‌اید، نتایج آن دقت تشخیص را تا ۹۵٪ افزایش می‌دهد.\n\n"
                            "⚠️ اگر ندارید نگران نباشید - سیستم با اطلاعات فعلی هم تشخیص می‌دهد.\n\n"
                            "آیا نتایج آزمایش خون دارید؟ (بله/خیر)",
                "type": "section_intro",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: x.strip().lower(),
                "skip_section_on": lambda x: x.strip().lower() in ['خیر', 'no'],
            },
            {
                "key": "Hb(g/dl)",
                "question": "🔬 هموگلوبین (Hb)؟\n(واحد: g/dL | طبیعی زنان: ۱۲-۱۶)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 5 <= float(x) <= 20,
                "transform": lambda x: float(x),
            },
            {
                "key": "RBS(mg/dl)",
                "question": "🔬 قند خون (RBS)؟\n(واحد: mg/dL | طبیعی: ۷۰-۱۴۰)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 40 <= float(x) <= 400,
                "transform": lambda x: float(x),
            },
            {
                "key": "FSH(mIU/mL)",
                "question": "🔬 FSH (هورمون محرک فولیکول)؟\n(واحد: mIU/mL | طبیعی: ۳-۱۰)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.1 <= float(x) <= 50,
                "transform": lambda x: float(x),
            },
            {
                "key": "LH(mIU/mL)",
                "question": "🔬 LH (هورمون لوتئینیزه‌کننده)؟\n(واحد: mIU/mL | طبیعی: ۲-۱۵)\n⚠️ در PCOS معمولاً نسبت LH/FSH بالاست",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.1 <= float(x) <= 50,
                "transform": lambda x: float(x),
            },
            {
                "key": "TSH (mIU/L)",
                "question": "🔬 TSH (هورمون تیروئید)؟\n(واحد: mIU/L | طبیعی: ۰.۵-۴.۵)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.01 <= float(x) <= 20,
                "transform": lambda x: float(x),
            },
            {
                "key": "AMH(ng/mL)",
                "question": "🔬 AMH (آنتی‌مولرین)؟\n(واحد: ng/mL | طبیعی: ۱-۴)\n⚠️ در PCOS معمولاً بالای ۴ است",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.01 <= float(x) <= 30,
                "transform": lambda x: float(x),
            },
            {
                "key": "PRL(ng/mL)",
                "question": "🔬 پرولاکتین (PRL)؟\n(واحد: ng/mL | طبیعی: ۲-۲۹)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.1 <= float(x) <= 100,
                "transform": lambda x: float(x),
            },
            {
                "key": "Vit D3 (ng/mL)",
                "question": "🔬 ویتامین D3؟\n(واحد: ng/mL | طبیعی: ۳۰-۱۰۰)\n💡 کمبود ویتامین D در PCOS شایع است",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 1 <= float(x) <= 150,
                "transform": lambda x: float(x),
            },
            {
                "key": "PRG(ng/mL)",
                "question": "🔬 پروژسترون (PRG)؟\n(واحد: ng/mL | طبیعی فاز فولیکولار: ۰.۱-۰.۷)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.01 <= float(x) <= 50,
                "transform": lambda x: float(x),
            },
            {
                "key": "Beta_HCG_I(mIU/mL)",
                "question": "🔬 Beta-HCG اول؟\n(واحد: mIU/mL)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.01 <= float(x) <= 300,
                "transform": lambda x: float(x),
            },
            {
                "key": "Beta_HCG_II(mIU/mL)",
                "question": "🔬 Beta-HCG دوم؟\n(واحد: mIU/mL)",
                "type": "numeric",
                "section": AssessmentSection.LAB_RESULTS,
                "validation": lambda x: 0.01 <= float(x) <= 300,
                "transform": lambda x: float(x),
            },
        ]

    def _ultrasound_questions(self) -> List[Dict[str, Any]]:
        """Ultrasound results - least common"""
        return [
            {
                "key": "_ultrasound_intro",
                "question": "━━━━━━━━━━━━━━━\n"
                            "📋 بخش ۶: نتایج سونوگرافی (اختیاری)\n"
                            "━━━━━━━━━━━━━━━\n\n"
                            "نتایج سونوگرافی تخمدان دقیق‌ترین اطلاعات برای تشخیص PCOS هستند.\n\n"
                            "آیا نتایج سونوگرافی دارید؟ (بله/خیر)",
                "type": "section_intro",
                "section": AssessmentSection.ULTRASOUND,
                "validation": lambda x: x.strip().lower() in ['بله', 'خیر', 'yes', 'no'],
                "transform": lambda x: x.strip().lower(),
                "skip_section_on": lambda x: x.strip().lower() in ['خیر', 'no'],
            },
            {
                "key": "Follicle No. (L)",
                "question": "🔍 تعداد فولیکول در تخمدان چپ؟\n(PCOS: معمولاً بیشتر از ۱۲)",
                "type": "numeric",
                "section": AssessmentSection.ULTRASOUND,
                "validation": lambda x: 0 <= float(x) <= 30,
                "transform": lambda x: float(x),
            },
            {
                "key": "Follicle No. (R)",
                "question": "🔍 تعداد فولیکول در تخمدان راست؟",
                "type": "numeric",
                "section": AssessmentSection.ULTRASOUND,
                "validation": lambda x: 0 <= float(x) <= 30,
                "transform": lambda x: float(x),
            },
            {
                "key": "Avg. F size (L) (mm)",
                "question": "🔍 میانگین اندازه فولیکول چپ (mm)؟",
                "type": "numeric",
                "section": AssessmentSection.ULTRASOUND,
                "validation": lambda x: 1 <= float(x) <= 30,
                "transform": lambda x: float(x),
            },
            {
                "key": "Avg. F size (R) (mm)",
                "question": "🔍 میانگین اندازه فولیکول راست (mm)؟",
                "type": "numeric",
                "section": AssessmentSection.ULTRASOUND,
                "validation": lambda x: 1 <= float(x) <= 30,
                "transform": lambda x: float(x),
            },
            {
                "key": "Endometrium (mm)",
                "question": "🔍 ضخامت آندومتر (mm)؟",
                "type": "numeric",
                "section": AssessmentSection.ULTRASOUND,
                "validation": lambda x: 1 <= float(x) <= 25,
                "transform": lambda x: float(x),
            },
        ]

    # ---- Helper Methods ----

    def _validate_date(self, date_str: str) -> bool:
        try:
            date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            today = datetime.now().date()
            age = (today - date_obj).days / 365.25
            return 15 <= age <= 60
        except (ValueError, TypeError):
            return False

    def _parse_date(self, date_str: str):
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()

    # ---- Core Methods ----

    def update(self, key: str, value: Any):
        self.data[key] = value
        self.last_active = datetime.utcnow()

    def add_to_history(self, role: str, message: str):
        self.conversation_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_next_question(self) -> Optional[str]:
        """Get next applicable question, skipping conditional ones and skipped sections"""
        while self.current_step < len(self.questions):
            question_config = self.questions[self.current_step]
            current_section = question_config.get('section')

            # Skip if this section was skipped by user
            if current_section and current_section.value in self.skipped_sections:
                self.skipped_steps.append(self.current_step)
                self.current_step += 1
                continue

            # Check if this question has a condition
            if 'condition' in question_config:
                if not question_config['condition'](self.data):
                    self.skipped_steps.append(self.current_step)
                    self.current_step += 1
                    continue

            return question_config["question"]

        return None

    def validate_answer(self, answer: str) -> Tuple[bool, Optional[str]]:
        """Validate user's answer for current question"""
        if self.current_step >= len(self.questions):
            return False, "سوالات تمام شده است"

        question_config = self.questions[self.current_step]

        try:
            if not question_config["validation"](answer):
                return False, question_config.get("error_message",
                                                  "پاسخ نامعتبر است")

            # Check exit condition
            if 'exit_on' in question_config and question_config['exit_on'](
                    answer):
                self.update(question_config["key"], answer)
                return True, question_config.get('exit_message')

            # Check section skip
            if 'skip_section_on' in question_config and question_config[
                'skip_section_on'](answer):
                current_section = question_config.get('section')
                if current_section:
                    self.skipped_sections.append(current_section.value)
                    # Track completed section even if skipped
                    if current_section.value not in self.completed_sections:
                        self.completed_sections.append(
                            current_section.value)
                return True, None

            # Transform and store
            if "transform" in question_config:
                value = question_config["transform"](answer)
            else:
                value = answer

            # Only store non-intro keys
            if not question_config["key"].startswith("_"):
                self.update(question_config["key"], value)

            # Track section completion
            current_section = question_config.get('section')
            if current_section and current_section.value not in self.completed_sections:
                self.completed_sections.append(current_section.value)

            # Calculate derived values
            self._calculate_derived_values()

            return True, None

        except (ValueError, TypeError):
            return False, question_config.get("error_message",
                                              "پاسخ نامعتبر است")

    def _calculate_derived_values(self):
        """Auto-calculate BMI, Waist:Hip ratio, FSH/LH"""
        weight = self.data.get('Weight (Kg)')
        height = self.data.get('Height(Cm)')
        if weight and height:
            self.data['BMI'] = weight / ((height / 100) ** 2)

        waist = self.data.get('Waist(inch)')
        hip = self.data.get('Hip(inch)')
        if waist and hip:
            self.data['Waist:Hip Ratio'] = waist / hip

        fsh = self.data.get('FSH(mIU/mL)')
        lh = self.data.get('LH(mIU/mL)')
        if fsh and lh and lh > 0:
            self.data['FSH/LH'] = fsh / lh

    def advance(self):
        self.current_step += 1

    def should_exit(self) -> bool:
        consent = self.data.get('consent', '')
        return consent in ['خیر', 'no']

    def is_complete(self) -> bool:
        return self.get_next_question() is None

    def get_progress(self) -> Dict[str, Any]:
        total = len(self.questions) - len(self.skipped_steps)
        answered = self.current_step - len(self.skipped_steps)
        return {
            "current_step": max(0, answered),
            "total_steps": max(1, total),
            "percentage": min(100, int((answered / total) * 100)) if total > 0 else 0
        }

    def get_section_summary(self) -> Dict[str, str]:
        """Get summary of which sections were completed/skipped"""
        summary = {}
        for section in AssessmentSection:
            if section.value in self.completed_sections:
                if section.value in self.skipped_sections:
                    summary[section.value] = "رد شده"
                else:
                    summary[section.value] = "تکمیل شده"
            else:
                summary[section.value] = "نرسیده"
        return summary


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
    def delete(cls, session_id: str):
        if session_id in cls._sessions:
            del cls._sessions[session_id]

    @classmethod
    def cleanup_old(cls, max_age_minutes: int = 60):
        now = datetime.utcnow()
        to_remove = [
            sid for sid, state in cls._sessions.items()
            if (now - state.last_active).total_seconds() > max_age_minutes * 60
        ]
        for sid in to_remove:
            del cls._sessions[sid]

