# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .chat_message import ChatMessage

__all__ = ["AgentChatResponse"]


class AgentChatResponse(BaseModel):
    messages: List[ChatMessage]
    """Array of assistant response messages"""

    conversation_id: Optional[str] = None
    """Conversation ID (present when conversation persistence is enabled)"""
