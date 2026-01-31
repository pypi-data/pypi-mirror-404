# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = [
    "ChatMessage",
    "ContentMultimodalContent",
    "ContentMultimodalContentImageURL",
    "ToolCall",
    "ToolCallFunction",
]


class ContentMultimodalContentImageURL(BaseModel):
    url: str


class ContentMultimodalContent(BaseModel):
    type: Literal["text", "image_url"]

    image_url: Optional[ContentMultimodalContentImageURL] = None

    text: Optional[str] = None


class ToolCallFunction(BaseModel):
    arguments: str

    name: str


class ToolCall(BaseModel):
    id: str

    function: ToolCallFunction

    type: Literal["function"]


class ChatMessage(BaseModel):
    content: Union[str, List[ContentMultimodalContent], Dict[str, Optional[object]], None] = None
    """Message content.

    Can be string, array (multimodal), object (tool), or null (when tool_calls
    present).
    """

    role: Literal["system", "user", "assistant", "tool"]
    """Message role"""

    name: Optional[str] = None
    """Tool name (required when role is "tool")"""

    tool_call_id: Optional[str] = None
    """Tool call ID (for tool role messages)"""

    tool_calls: Optional[List[ToolCall]] = None
    """Tool calls requested by assistant (for assistant role messages)"""
