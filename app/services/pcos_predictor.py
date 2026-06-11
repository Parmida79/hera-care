import json
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd


class PCOSPredictor:
    """PCOS prediction service using trained XGBoost model"""

    def __init__(self):
        model_path = Path(
            __file__).parent.parent.parent / "ml/data/processed/pcos_xgb_model.pkl"
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

        # Feature names MUST match the exact order from training
        self.feature_names = [
            'Age (yrs)', 'Weight (Kg)', 'Height(Cm)', 'BMI', 'Blood Group',
            'Pulse rate(bpm)', 'RR (breaths/min)', 'Hb(g/dl)', 'Cycle(R/I)',
            'Cycle length(days)', 'Marraige Status (Yrs)', 'Pregnant(Y/N)',
            'No. of aborptions',
            'Beta_HCG_I(mIU/mL)', 'Beta_HCG_II(mIU/mL)',
            'FSH(mIU/mL)', 'LH(mIU/mL)', 'FSH/LH',
            'Hip(inch)', 'Waist(inch)', 'Waist:Hip Ratio', 'TSH (mIU/L)',
            'AMH(ng/mL)', 'PRL(ng/mL)', 'Vit D3 (ng/mL)', 'PRG(ng/mL)',
            'RBS(mg/dl)', 'Weight gain(Y/N)', 'hair growth(Y/N)',
            'Skin darkening (Y/N)', 'Hair loss(Y/N)', 'Pimples(Y/N)',
            'Fast food (Y/N)', 'Reg.Exercise(Y/N)', 'BP _Systolic (mmHg)',
            'BP _Diastolic (mmHg)', 'Follicle No. (L)', 'Follicle No. (R)',
            'Avg. F size (L) (mm)', 'Avg. F size (R) (mm)',
            'Endometrium (mm)'
        ]

        # Load median values from training
        medians_path = Path(
            __file__).parent.parent.parent / "ml/data/processed/feature_medians.json"
        if medians_path.exists():
            with open(medians_path, 'r') as f:
                self.default_values = json.load(f)
        else:
            # Fallback default values
            self.default_values = {
                'Age (yrs)': 25,
                'Weight (Kg)': 60,
                'Height(Cm)': 160,
                'BMI': 23.4,
                'Blood Group': 11,
                'Pulse rate(bpm)': 75,
                'RR (breaths/min)': 16,
                'Hb(g/dl)': 12.5,
                'Cycle(R/I)': 0,
                'Cycle length(days)': 28,
                'Marraige Status (Yrs)': 0,
                'Pregnant(Y/N)': 0,
                'No. of aborptions': 0,
                'Beta_HCG_I(mIU/mL)': 1.5,
                'Beta_HCG_II(mIU/mL)': 1.5,
                'FSH(mIU/mL)': 6.0,
                'LH(mIU/mL)': 8.0,
                'FSH/LH': 0.75,
                'Hip(inch)': 36,
                'Waist(inch)': 30,
                'Waist:Hip Ratio': 0.83,
                'TSH (mIU/L)': 2.5,
                'AMH(ng/mL)': 4.5,
                'PRL(ng/mL)': 15,
                'Vit D3 (ng/mL)': 25,
                'PRG(ng/mL)': 1.0,
                'RBS(mg/dl)': 90,
                'Weight gain(Y/N)': 0,
                'hair growth(Y/N)': 0,
                'Skin darkening (Y/N)': 0,
                'Hair loss(Y/N)': 0,
                'Pimples(Y/N)': 0,
                'Fast food (Y/N)': 0,
                'Reg.Exercise(Y/N)': 0,
                'BP _Systolic (mmHg)': 120,
                'BP _Diastolic (mmHg)': 80,
                'Follicle No. (L)': 8,
                'Follicle No. (R)': 8,
                'Avg. F size (L) (mm)': 10,
                'Avg. F size (R) (mm)': 10,
                'Endometrium (mm)': 8,
            }


    def prepare_features(self, patient_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert conversation data to model-ready features"""
        # Start with default values
        features = self.default_values.copy()

        # Calculate age from date_of_birth if provided
        if 'date_of_birth' in patient_data:
            from datetime import date
            dob = patient_data['date_of_birth']
            if isinstance(dob, str):
                from datetime import datetime
                dob = datetime.strptime(dob, '%Y-%m-%d').date()

            today = date.today()
            age = today.year - dob.year - (
                        (today.month, today.day) < (dob.month, dob.day))
            features['Age (yrs)'] = float(age)

        # Calculate BMI if not provided but weight and height are available
        if 'BMI' not in patient_data or patient_data['BMI'] is None:
            if 'Weight (Kg)' in patient_data and 'Height(Cm)' in patient_data:
                weight = float(patient_data['Weight (Kg)'])
                height = float(patient_data['Height(Cm)'])
                features['BMI'] = weight / ((height / 100) ** 2)

        # Override with provided patient data
        for key, value in patient_data.items():
            if key in features and value is not None and key != 'date_of_birth':
                features[key] = value

        # Create DataFrame with correct column order
        df = pd.DataFrame([features])[self.feature_names]

        # Ensure all columns are numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Fill any remaining NaN with default values
        for col in df.columns:
            if df[col].isna().any():
                df[col] = df[col].fillna(self.default_values.get(col, 0))

        return df

    def predict(self, patient_data: Dict[str, Any]) -> Tuple[
        int, float, Dict[str, Any]]:
        """
        Make PCOS prediction

        Returns:
            prediction: 0 or 1 (No PCOS / Has PCOS)
            probability: Confidence score (0-1)
            explanation: Feature importance for this prediction
        """
        features_df = self.prepare_features(patient_data)

        # Get prediction
        prediction = self.model.predict(features_df)[0]
        probability = self.model.predict_proba(features_df)[0][
            1]  # Probability of PCOS

        # Get feature importance for explanation
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))

        return int(prediction), float(probability), feature_importance

    def get_advice(self, prediction: int, probability: float,
                   patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized advice based on prediction and patient data
        """
        advice = {
            "diagnosis": "PCOS احتمالی" if prediction == 1 else "بدون علائم PCOS",
            "confidence": f"{probability * 100:.1f}%",
            "risk_level": self._get_risk_level(probability),
            "recommendations": self._generate_recommendations(prediction,
                                                              probability,
                                                              patient_data),
            "next_steps": self._get_next_steps(prediction, probability),
            "lifestyle_tips": self._get_lifestyle_tips(patient_data),
            "warning": "⚠️ این تشخیص کمکی است و جایگزین مشاوره پزشکی نیست."
        }

        return advice

    def _get_risk_level(self, probability: float) -> str:
        """Categorize risk level"""
        if probability < 0.3:
            return "کم"
        elif probability < 0.6:
            return "متوسط"
        elif probability < 0.8:
            return "بالا"
        else:
            return "بسیار بالا"

    def _generate_recommendations(self, prediction: int, probability: float,
                                  patient_data: Dict[str, Any]) -> list:
        """Generate personalized recommendations"""
        recommendations = []

        if prediction == 1:
            recommendations.append("🏥 مشاوره با متخصص زنان و زایمان")
            recommendations.append("🔬 انجام آزمایشات هورمونی کامل")

            # BMI-based advice
            if patient_data.get('BMI', 0) > 25:
                recommendations.append("⚖️ کاهش وزن تدریجی (5-10% وزن فعلی)")

            # Irregular cycle
            if patient_data.get('Cycle(R/I)', 0) == 1:
                recommendations.append("📅 پیگیری منظم چرخه قاعدگی")

            # High follicle count
            if patient_data.get('Follicle No. (R)',
                                0) > 12 or patient_data.get('Follicle No. (L)',
                                                            0) > 12:
                recommendations.append("🔍 سونوگرافی تخمدان‌ها")

        else:
            recommendations.append("✅ علائم PCOS مشاهده نشد")
            recommendations.append("🔄 پیگیری سالانه برای سلامت زنان")

        return recommendations

    def _get_next_steps(self, prediction: int, probability: float) -> list:
        """Get next steps based on diagnosis"""
        if prediction == 1:
            if probability > 0.7:
                return [
                    "هر چه سریع‌تر به پزشک مراجعه کنید",
                    "آزمایش خون برای سطح هورمون‌ها",
                    "سونوگرافی تخمدان"
                ]
            else:
                return [
                    "در صورت تداوم علائم به پزشک مراجعه کنید",
                    "سبک زندگی سالم را حفظ کنید",
                    "علائم را پیگیری کنید"
                ]
        else:
            return [
                "معاینات دوره‌ای سالانه",
                "حفظ وزن سالم",
                "پیگیری تغییرات چرخه قاعدگی"
            ]

    def _get_lifestyle_tips(self, patient_data: Dict[str, Any]) -> list:
        """Generate lifestyle modification tips"""
        tips = []

        # Exercise
        if patient_data.get('Reg.Exercise(Y/N)', 0) == 0:
            tips.append("🏃‍♀️ ورزش منظم 30 دقیقه‌ای، 5 روز در هفته")

        # Fast food
        if patient_data.get('Fast food (Y/N)', 0) == 1:
            tips.append("🥗 کاهش مصرف فست‌فود و غذاهای فرآوری شده")

        # Weight management
        if patient_data.get('Weight gain(Y/N)', 0) == 1:
            tips.append("⚖️ مدیریت وزن با رژیم غذایی متعادل")

        # General tips
        tips.extend([
            "💧 نوشیدن 8 لیوان آب در روز",
            "😴 خواب کافی (7-8 ساعت)",
            "🧘‍♀️ کاهش استرس با یوگا یا مدیتیشن",
            "🚭 اجتناب از سیگار و الکل"
        ])

        return tips
