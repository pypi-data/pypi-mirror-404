# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ...._models import BaseModel
from .knowledge_document import KnowledgeDocument

__all__ = ["DocumentProcessResponse"]


class DocumentProcessResponse(BaseModel):
    document: KnowledgeDocument

    message: str
