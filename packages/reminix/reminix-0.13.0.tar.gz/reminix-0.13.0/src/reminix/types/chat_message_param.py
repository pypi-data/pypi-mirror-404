# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = [
    "ChatMessageParam",
    "ContentMultimodalContent",
    "ContentMultimodalContentImageURL",
    "ToolCall",
    "ToolCallFunction",
]


class ContentMultimodalContentImageURL(TypedDict, total=False):
    url: Required[str]


class ContentMultimodalContent(TypedDict, total=False):
    type: Required[Literal["text", "image_url"]]

    image_url: ContentMultimodalContentImageURL

    text: str


class ToolCallFunction(TypedDict, total=False):
    arguments: Required[str]

    name: Required[str]


class ToolCall(TypedDict, total=False):
    id: Required[str]

    function: Required[ToolCallFunction]

    type: Required[Literal["function"]]


class ChatMessageParam(TypedDict, total=False):
    content: Required[Union[str, Iterable[ContentMultimodalContent], Dict[str, Optional[object]], None]]
    """Message content.

    Can be string, array (multimodal), object (tool), or null (when tool_calls
    present).
    """

    role: Required[Literal["system", "user", "assistant", "tool"]]
    """Message role"""

    name: str
    """Tool name (required when role is "tool")"""

    tool_call_id: str
    """Tool call ID (for tool role messages)"""

    tool_calls: Iterable[ToolCall]
    """Tool calls requested by assistant (for assistant role messages)"""
