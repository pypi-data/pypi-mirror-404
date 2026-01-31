# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import TYPE_CHECKING, Dict, List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Tool", "Output", "Parameters"]


class Output(BaseModel):
    """JSON Schema for agent input parameters"""

    default: Optional[object] = None
    """Default value for the property"""

    description: Optional[str] = None
    """Description of the schema"""

    enum: Optional[List[Optional[object]]] = None
    """Enumeration of allowed values"""

    items: Optional[object] = None
    """Schema for array items"""

    properties: Optional[Dict[str, Optional[object]]] = None
    """Property definitions for object types"""

    required: Optional[List[str]] = None
    """List of required property names"""

    title: Optional[str] = None
    """Human-readable title"""

    type: Optional[str] = None
    """JSON Schema type (e.g., "object", "string", "array")"""

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, Optional[object]] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> Optional[object]: ...
    else:
        __pydantic_extra__: Dict[str, Optional[object]]


class Parameters(BaseModel):
    """JSON Schema for agent input parameters"""

    default: Optional[object] = None
    """Default value for the property"""

    description: Optional[str] = None
    """Description of the schema"""

    enum: Optional[List[Optional[object]]] = None
    """Enumeration of allowed values"""

    items: Optional[object] = None
    """Schema for array items"""

    properties: Optional[Dict[str, Optional[object]]] = None
    """Property definitions for object types"""

    required: Optional[List[str]] = None
    """List of required property names"""

    title: Optional[str] = None
    """Human-readable title"""

    type: Optional[str] = None
    """JSON Schema type (e.g., "object", "string", "array")"""

    if TYPE_CHECKING:
        # Some versions of Pydantic <2.8.0 have a bug and don’t allow assigning a
        # value to this field, so for compatibility we avoid doing it at runtime.
        __pydantic_extra__: Dict[str, Optional[object]] = FieldInfo(init=False)  # pyright: ignore[reportIncompatibleVariableOverride]

        # Stub to indicate that arbitrary properties are accepted.
        # To access properties that are not valid identifiers you can use `getattr`, e.g.
        # `getattr(obj, '$type')`
        def __getattr__(self, attr: str) -> Optional[object]: ...
    else:
        __pydantic_extra__: Dict[str, Optional[object]]


class Tool(BaseModel):
    id: str
    """Unique tool ID"""

    created_at: str = FieldInfo(alias="createdAt")
    """Creation timestamp"""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """User who created the tool (for managed tools)"""

    description: Optional[str] = None
    """Tool description"""

    discovered_at: Optional[str] = FieldInfo(alias="discoveredAt", default=None)
    """When the tool was discovered"""

    name: str
    """Tool name"""

    output: Optional[Output] = None
    """JSON Schema for agent input parameters"""

    parameters: Optional[Parameters] = None
    """JSON Schema for agent input parameters"""

    project_id: str = FieldInfo(alias="projectId")
    """Project ID"""

    status: Literal["active", "inactive"]
    """Tool status"""

    type: str
    """
    Tool type: "managed" for platform-provided, or "{language}" for custom tools
    (e.g., "python", "typescript")
    """

    updated_at: str = FieldInfo(alias="updatedAt")
    """Last update timestamp"""
