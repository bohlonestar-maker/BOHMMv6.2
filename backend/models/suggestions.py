# Suggestion-related Pydantic models
from pydantic import BaseModel


class SuggestionCreate(BaseModel):
    title: str
    description: str
    is_anonymous: bool = False


class SuggestionStatusUpdate(BaseModel):
    status: str


class SuggestionVote(BaseModel):
    vote_type: str
