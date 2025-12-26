from pydantic import BaseModel, Field

class BookAnalysis(BaseModel):
    title: str = Field(description="The book's title")
    author: str = Field(description="The book's author")
    genre: str = Field(description="Primary genre")
    summary: str = Field(description="Brief summary")
    rating: int = Field(ge=1, le=10, description="Rating 1‑10")
