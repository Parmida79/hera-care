from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import ConversationManager

chat_router = APIRouter()

@router.post('/')
async def chat(message: ChatMessage):
    if not message.session_id:
        state = ConversationManager.create()
        question = state.get_next_question()
        return {
            "session_id": state.session_id,
            "message": question,
            "step": state.current_step
        }

    state = ConversationManager.get(message.session_id)
    if not state:
        raise HTTPException(404, "جلسه یافت نشد")

    # we should think about how to prcoess user's message
    state.update(f"step_{state.current_step}", message.message)

    # go to next question
    state.advance()
    next_q = state.get_next_question()

    # if it is the last step, then it should start predicting
    if state.current_step >= 14:  # e.g.
        # call predictor.py here
        result = {"probability": 0.72, "message": "احتمال نسبتاً بالا است. لطفاً به متخصص مراجعه کنید."}
        return {"message": result["message"], "finished": True}

    return {
        "session_id": state.session_id,
        "message": next_q,
        "step": state.current_step
    }