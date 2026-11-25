from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SupportedLanguage = Literal[
    "c",
    "cpp",
    "python",
    "java",
    "javascript"
]


class SnippetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    language: SupportedLanguage
    code: str = Field(max_length=50000)


class SnippetUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    language: SupportedLanguage
    code: str = Field(max_length=50000)


class SnippetResponse(BaseModel):
    id: int
    name: str
    language: str
    code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)