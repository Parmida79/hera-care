from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas.chat import ChatMessage, ChatResponse, PredictionResult
from app.services import ConversationManager
from app.services.pcos_predictor import PCOSPredictor
from app.db.database import get_db
from app.models import Patient, PatientDisease, Disease, MedicalHistory, ChatSession
from app.utils import get_current_user
from app.utils.enums import (
    Gender, MaritalStatus, EntryType,
    DiseaseType, DiseaseSeverity, PatientDiseaseStatus
)

chat_router = APIRouter()
predictor = PCOSPredictor()


@chat_router.post('/', response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    current_user: Patient = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Main chat endpoint for PCOS assessment"""

    # ---- Start new conversation ----
    if not message.session_id:
        state = ConversationManager.create()
        question = state.get_next_question()
        state.add_to_history("assistant", question)

        return ChatResponse(
            session_id=state.session_id,
            message=question,
            step=state.current_step,
            progress=state.get_progress(),
            finished=False,
            section_summary=state.get_section_summary()
        )

    # ---- Continue existing conversation ----
    state = ConversationManager.get(message.session_id)
    if not state:
        raise HTTPException(404, "جلسه یافت نشد. لطفاً دوباره شروع کنید.")

    # Add user message to history
    state.add_to_history("user", message.message)

    # Validate answer
    is_valid, error_or_exit_message = state.validate_answer(message.message)

    # ---- Invalid answer ----
    if not is_valid:
        current_question = state.get_next_question()
        error_response = f"❌ {error_or_exit_message}\n\n{current_question}"
        state.add_to_history("assistant", error_response)

        return ChatResponse(
            session_id=state.session_id,
            message=error_response,
            step=state.current_step,
            progress=state.get_progress(),
            finished=False,
            section_summary=state.get_section_summary()
        )

    # ---- User wants to exit ----
    if state.should_exit():
        state.add_to_history("assistant", error_or_exit_message)
        ConversationManager.delete(message.session_id)

        return ChatResponse(
            session_id=state.session_id,
            message=error_or_exit_message,
            step=state.current_step,
            progress=state.get_progress(),
            finished=True,
            section_summary=state.get_section_summary()
        )

    # Move to next question
    state.advance()

    # ---- All questions answered - make prediction ----
    if state.is_complete():
        # Calculate BMI if not already calculated
        if 'BMI' not in state.data:
            weight = state.data.get('Weight (Kg)')
            height = state.data.get('Height(Cm)')
            if weight and height:
                state.data['BMI'] = weight / ((height / 100) ** 2)

        # Make prediction
        prediction, probability, feature_importance = predictor.predict(state.data)

        # Get personalized advice
        advice = predictor.get_advice(prediction, probability, state.data)

        # Format final response
        response_message = format_final_response(advice)
        state.add_to_history("assistant", response_message)

        # Save to database in background
        background_tasks.add_task(
            save_assessment_results,
            db,
            current_user.id,
            prediction,
            probability,
            state.data,
            advice,
            message.session_id,
            state.conversation_history
        )

        # Clean up session after delay
        background_tasks.add_task(
            cleanup_session_delayed,
            message.session_id
        )

        return ChatResponse(
            session_id=state.session_id,
            message=response_message,
            step=state.current_step,
            progress=state.get_progress(),
            finished=True,
            prediction=PredictionResult(
                has_pcos=bool(prediction),
                confidence=probability,
                risk_level=advice["risk_level"],
                recommendations=advice["recommendations"]
            ),
            section_summary=state.get_section_summary()
        )

    # ---- Get next question ----
    next_question = state.get_next_question()
    state.add_to_history("assistant", next_question)

    return ChatResponse(
        session_id=state.session_id,
        message=next_question,
        step=state.current_step,
        progress=state.get_progress(),
        finished=False,
        section_summary=state.get_section_summary()
    )


def format_final_response(advice: dict) -> str:
    """Format the final assessment results"""
    message = f"""
🔍 **نتیجه ارزیابی**

📊 **تشخیص**: {advice['diagnosis']}
📈 **احتمال**: {advice['confidence']}
⚠️ **سطح ریسک**: {advice['risk_level']}

💡 **توصیه‌ها**:
"""
    for i, rec in enumerate(advice['recommendations'], 1):
        message += f"\n{i}. {rec}"

    message += "\n\n🎯 **مراحل بعدی**:"
    for i, step in enumerate(advice['next_steps'], 1):
        message += f"\n{i}. {step}"

    message += "\n\n🌱 **نکات سبک زندگی**:"
    for i, tip in enumerate(advice['lifestyle_tips'][:5], 1):
        message += f"\n{i}. {tip}"

    message += f"\n\n{advice['warning']}"

    return message


async def save_assessment_results(
    db: Session,
    patient_id: int,
    prediction: int,
    probability: float,
    patient_data: dict,
    advice: dict,
    session_id: str = None,
    conversation_history: list = None
):
    """Save assessment results to database"""
    try:
        # 1. Clean patient_data for JSON serialization (do this FIRST)
        clean_patient_data = {}
        for key, value in patient_data.items():
            if isinstance(value, (date, datetime)):
                clean_patient_data[key] = value.isoformat()
            else:
                clean_patient_data[key] = value

        # 2. Update Patient table
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            # PCOS only affects women
            patient.gender = Gender.FEMALE

            # Set date_of_birth
            if 'date_of_birth' in patient_data:
                dob = patient_data['date_of_birth']
                if isinstance(dob, str):
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                patient.date_of_birth = dob

            # Update weight
            if 'Weight (Kg)' in patient_data:
                patient.weight_kg = float(patient_data['Weight (Kg)'])

            # Update height
            if 'Height(Cm)' in patient_data:
                patient.height_cm = float(patient_data['Height(Cm)'])

            # Calculate and save BMI
            if patient.weight_kg and patient.height_cm:
                patient.bmi = patient.weight_kg / ((patient.height_cm / 100) ** 2)
                clean_patient_data['BMI'] = patient.bmi

            # Set marital status
            if 'Marraige Status (Yrs)' in patient_data:
                marriage_years = float(patient_data['Marraige Status (Yrs)'])
                if marriage_years > 0:
                    patient.marital_status = MaritalStatus.MARRIED
                else:
                    patient.marital_status = MaritalStatus.SINGLE

            # Update timestamp
            patient.updated_at = datetime.now(timezone.utc)

        # 3. Clean conversation history for JSON
        clean_conversation_history = []
        if conversation_history:
            for msg in conversation_history:
                clean_msg = {}
                for k, v in msg.items():
                    if isinstance(v, (date, datetime)):
                        clean_msg[k] = v.isoformat()
                    else:
                        clean_msg[k] = v
                clean_conversation_history.append(clean_msg)

        # 4. Save ChatSession
        if session_id:
            chat_session = ChatSession(
                session_id=session_id,
                patient_id=patient_id,
                current_step=len(clean_conversation_history),
                total_steps=len(clean_conversation_history),
                is_completed=True,
                conversation_data={
                    "messages": clean_conversation_history,
                    "collected_data": clean_patient_data
                },
                prediction_result={
                    "prediction": prediction,
                    "probability": float(probability),
                    "advice": advice
                },
                completed_at=datetime.now(timezone.utc)
            )
            db.add(chat_session)

        # 5. Save medical history - main assessment
        history_entry = MedicalHistory(
            patient_id=patient_id,
            entry_type=EntryType.NOTE,
            value={
                "assessment_type": "PCOS_screening",
                "prediction": prediction,
                "probability": float(probability),
                "patient_data": clean_patient_data,
                "advice": advice,
                "assessment_date": datetime.now(timezone.utc).isoformat()
            },
            source="chatbot_assessment"
        )
        db.add(history_entry)

        # 6. Save vital signs
        # Blood pressure
        if 'BP _Systolic (mmHg)' in patient_data and 'BP_ Diastolic (mmHg)' in patient_data:
            systolic = patient_data.get('BP _Systolic (mmHg)')
            diastolic = patient_data.get('BP_ Diastolic (mmHg)')
            if systolic and diastolic:
                bp_entry = MedicalHistory(
                    patient_id=patient_id,
                    entry_type=EntryType.VITAL,
                    value={
                        "type": "blood_pressure",
                        "systolic": systolic,
                        "diastolic": diastolic,
                        "unit": "mmHg"
                    },
                    source="chatbot_assessment"
                )
                db.add(bp_entry)

        # BMI
        if patient and patient.bmi:
            bmi_entry = MedicalHistory(
                patient_id=patient_id,
                entry_type=EntryType.VITAL,
                value={
                    "type": "bmi",
                    "value": float(patient.bmi),
                    "weight_kg": patient.weight_kg,
                    "height_cm": patient.height_cm,
                    "unit": "kg/m²"
                },
                source="chatbot_assessment"
            )
            db.add(bmi_entry)

        # Pulse rate
        if 'Pulse rate(bpm)' in patient_data and patient_data['Pulse rate(bpm)']:
            pulse_entry = MedicalHistory(
                patient_id=patient_id,
                entry_type=EntryType.VITAL,
                value={
                    "type": "pulse_rate",
                    "value": patient_data['Pulse rate(bpm)'],
                    "unit": "bpm"
                },
                source="chatbot_assessment"
            )
            db.add(pulse_entry)

        # Respiratory rate
        if 'RR (breaths/min)' in patient_data and patient_data['RR (breaths/min)']:
            rr_entry = MedicalHistory(
                patient_id=patient_id,
                entry_type=EntryType.VITAL,
                value={
                    "type": "respiratory_rate",
                    "value": patient_data['RR (breaths/min)'],
                    "unit": "breaths/min"
                },
                source="chatbot_assessment"
            )
            db.add(rr_entry)

        # 7. Save lab results
        lab_tests = [
            'FSH(mIU/mL)', 'LH(mIU/mL)', 'TSH (mIU/L)',
            'AMH(ng/mL)', 'PRL(ng/mL)', 'Vit D3 (ng/mL)',
            'PRG(ng/mL)', 'RBS(mg/dl)', 'Hb(g/dl)',
            'Beta_HCG_I(mIU/mL)', 'Beta_HCG_II(mIU/mL)'
        ]

        for test_name in lab_tests:
            value = patient_data.get(test_name)
            if value is not None:
                lab_entry = MedicalHistory(
                    patient_id=patient_id,
                    entry_type=EntryType.LAB_RESULT,
                    value={
                        "test_name": test_name,
                        "value": float(value),
                        "unit": test_name.split('(')[1].rstrip(')') if '(' in test_name else ""
                    },
                    source="chatbot_assessment"
                )
                db.add(lab_entry)

        # 8. Save symptom report
        symptom_fields = {
            'Weight gain(Y/N)': 'افزایش وزن',
            'hair growth(Y/N)': 'رشد موهای زائد',
            'Skin darkening (Y/N)': 'تیره شدن پوست',
            'Hair loss(Y/N)': 'ریزش مو',
            'Pimples(Y/N)': 'آکنه',
        }

        reported_symptoms = []
        for field, symptom_fa in symptom_fields.items():
            if field in patient_data and patient_data[field] == 1:
                reported_symptoms.append(symptom_fa)

        if patient_data.get('Cycle(R/I)') == 1:
            reported_symptoms.append('قاعدگی نامنظم')

        if reported_symptoms:
            symptom_entry = MedicalHistory(
                patient_id=patient_id,
                entry_type=EntryType.SYMPTOM_REPORT,
                value={
                    "symptoms": reported_symptoms,
                    "context": "PCOS_screening"
                },
                source="chatbot_assessment"
            )
            db.add(symptom_entry)

        # 9. If PCOS detected, create disease records
        if prediction == 1:
            pcos_disease = db.query(Disease).filter(
                Disease.code == "E28.2"
            ).first()

            if not pcos_disease:
                pcos_disease = Disease(
                    code="E28.2",
                    name="Polycystic Ovarian Syndrome",
                    type=DiseaseType.PHYSICAL,
                    description="سندرم تخمدان پلی‌کیستیک"
                )
                pcos_disease.is_active = True
                db.add(pcos_disease)
                db.flush()

            # Check existing record
            existing_patient_disease = db.query(PatientDisease).filter(
                PatientDisease.patient_id == patient_id,
                PatientDisease.disease_id == pcos_disease.id,
                PatientDisease.is_active == True
            ).first()

            if not existing_patient_disease:
                # Determine severity
                if probability > 0.8:
                    severity = DiseaseSeverity.SEVERE
                elif probability > 0.6:
                    severity = DiseaseSeverity.MODERATE
                else:
                    severity = DiseaseSeverity.MILD

                patient_disease = PatientDisease(
                    patient_id=patient_id,
                    disease_id=pcos_disease.id,
                    diagnosis_date=date.today(),
                    severity=severity,
                    status=PatientDiseaseStatus.ACTIVE,
                    notes=(
                        f"تشخیص از طریق سیستم هوشمند با اطمینان {probability * 100:.1f}٪.\n"
                        f"علائم: {', '.join(reported_symptoms) if reported_symptoms else 'هیچ'}\n"
                        f"BMI: {patient.bmi:.2f}" if patient and patient.bmi else ""
                    )
                )
                db.add(patient_disease)

        db.commit()
        print(f"✅ Successfully saved assessment for patient {patient_id}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error saving assessment results: {e}")
        import traceback
        traceback.print_exc()


async def cleanup_session_delayed(session_id: str):
    """Clean up session after delay"""
    import asyncio
    await asyncio.sleep(300)  # Wait 5 minutes
    ConversationManager.delete(session_id)
