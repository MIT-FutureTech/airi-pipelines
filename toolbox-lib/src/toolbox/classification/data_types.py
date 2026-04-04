from pydantic import BaseModel


class Category(BaseModel, frozen=True):
    name: str
    description: str = ""


class ClassificationResult(BaseModel, frozen=True):
    category: str
    reasoning: str
    confidence: float | None = None
