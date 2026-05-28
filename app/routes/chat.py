from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas.chat import ChatMessage, ChatResponse, PredictionResult
from app.services import ConversationManager
from app.services.pcos_predictor import PCOSPredictor
from app.db.database import get_db
from app.models import Patient, PatientDisease, Disease, MedicalHistory
from app.utils import get_current_user
from app.utils.enums import EntryType, PatientDiseaseStatus, DiseaseSeverity

chat_router = APIRouter()
predictor = PCOSPredictor()


@chat_router.post('/', response_model=ChatResponse)
async def chat(
        message: ChatMessage,
        background_tasks: BackgroundTasks,
        current_user: Patient = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Main chat endpoint for PCOS assessment
    """
    # Start new conversation
    if not message.session_id:
        state = ConversationManager.create()
        question = state.get_next_question()
        state.add_to_history("assistant", question)

        return ChatResponse(
            session_id=state.session_id,
            message=question,
            step=state.current_step,
            progress=state.get_progress(),
            finished=False
        )

    # Continue existing conversation
    state = ConversationManager.get(message.session_id)
    if not state:
        raise HTTPException(404, "جلسه یافت نشد. لطفاً دوباره شروع کنید.")

    # Add user message to history
    state.add_to_history("user", message.message)

    # Validate answer
    is_valid, error_message = state.validate_answer(message.message)

    if not is_valid:
        state.add_to_history("assistant", f"❌ {error_message}")
        return ChatResponse(
            session_id=state.session_id,
            message=f"❌ {error_message}\n\n{state.get_next_question()}",
            step=state.current_step,
            progress=state.get_progress(),
            finished=False
        )

    # Move to next question
    state.advance()

    # Check if conversation is complete
    if state.is_complete():
        # Calculate BMI if not provided
        if 'BMI' not in state.data:
            weight = state.data.get('Weight (Kg)')
            height = state.data.get('Height(Cm)')
            if weight and height:
                state.data['BMI'] = weight / ((height / 100) ** 2)

        # Make prediction
        prediction, probability, feature_importance = predictor.predict(
            state.data)

        # Get personalized advice
        advice = predictor.get_advice(prediction, probability, state.data)

        # Save to database in background
        background_tasks.add_task(
            save_assessment_results,
            db,
            current_user.id,
            prediction,
            probability,
            state.data,
            advice
        )

        # Format final response
        response_message = format_final_response(advice)

        state.add_to_history("assistant", response_message)

        # Clean up session after a delay
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
            )
        )

    # Get next question
    next_question = state.get_next_question()
    state.add_to_history("assistant", next_question)

    return ChatResponse(
        session_id=state.session_id,
        message=next_question,
        step=state.current_step,
        progress=state.get_progress(),
        finished=False
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
    for i, tip in enumerate(advice['lifestyle_tips'][:5], 1):  # Show top 5
        message += f"\n{i}. {tip}"

    message += f"\n\n{advice['warning']}"

    return message


async def save_assessment_results(
        db: Session,
        patient_id: int,
        prediction: int,
        probability: float,
        patient_data: dict,
        advice: dict
):
    """Save assessment results to database"""
    try:
        # Save medical history entry
        history_entry = MedicalHistory(
            patient_id=patient_id,
            entry_type=EntryType.NOTE,
            value={
                "assessment_type": "PCOS_screening",
                "prediction": prediction,
                "probability": float(probability),
                "patient_data": patient_data,
                "advice": advice
            },
            source="chatbot_assessment"
        )
        db.add(history_entry)

        # If PCOS detected, create patient_disease record
        if prediction == 1:
            # Get or create PCOS disease
            pcos_disease = db.query(Disease).filter(
                Disease.code == "PCOS-001"
            ).first()

            if not pcos_disease:
                pcos_disease = Disease(
                    code="PCOS-001",
                    name="Polycystic Ovary Syndrome",
                    type="physical",
                    description="سندرم تخمدان پلی‌کیستیک"
                )
                db.add(pcos_disease)
                db.flush()

            # Create patient disease record
            patient_disease = PatientDisease(
                patient_id=patient_id,
                disease_id=pcos_disease.id,
                severity=DiseaseSeverity.MODERATE if probability > 0.7 else DiseaseSeverity.MILD,
                status=PatientDiseaseStatus.ACTIVE,
                notes=f"Detected via chatbot assessment with {probability * 100:.1f}% confidence"
            )
            db.add(patient_disease)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving assessment results: {e}")


async def cleanup_session_delayed(session_id: str):
    """Clean up session after delay"""
    import asyncio
    await asyncio.sleep(300)  # Wait 5 minutes
    ConversationManager.delete(session_id)
