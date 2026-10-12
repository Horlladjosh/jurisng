from typing import List, Optional
from pydantic import BaseModel, Field


class Section(BaseModel):
    section_number: str = Field(description="Section number as string, e.g., '1' or '35A'")
    section_title: str = Field(description="Title or marginal note of the section")
    chapter: Optional[str] = Field(default=None, description="Chapter hierarchy if applicable")
    part: Optional[str] = Field(default=None, description="Part hierarchy if applicable")
    full_text: str = Field(description="Complete verbatim text of the section")
    subsections: List[str] = Field(default_factory=list, description="Array of individual subsection strings")
    searchable_chunk: str = Field(description="Contextualized string optimized for vector embeddings and search")


class Statute(BaseModel):
    statute_id: str = Field(description="Unique snake_case identifier, e.g., 'cfrn_1999'")
    statute_title: str = Field(description="Full official name of the Act")
    short_title: str = Field(description="Commonly recognized abbreviation")
    year: int = Field(description="Year of enactment or principal amendment")
    total_sections_expected: int = Field(description="Official total section count")
    sections: List[Section] = Field(description="List of all parsed sections")
