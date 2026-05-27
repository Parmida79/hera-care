from app.schemas import BaseSerializer


class ChatMessage(BaseSerializer):
    session_id: str | None = None
    message: str
