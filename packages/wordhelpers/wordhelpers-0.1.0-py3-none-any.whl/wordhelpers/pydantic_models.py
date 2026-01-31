# Built-In Imports
import re
from enum import Enum
from typing import Optional

# Third-Party Imports
from pydantic import BaseModel, field_validator, Field


class AlignmentEnum(str, Enum):
    left = "left"
    center = "center"
    right = "right"
    justify = "justify"
    distribute = "distribute"


class WordParagraphModel(BaseModel):
    style: str | None = None
    alignment: AlignmentEnum | None = None
    text: list[str] = Field(default_factory=list)


class WordCellModel(BaseModel):
    width: int | None = None
    background_color: str | None = None
    paragraphs: list[WordParagraphModel] = Field(default_factory=list)
    table: Optional["WordTableModel"] | None = None  # forward reference

    @field_validator("background_color")
    @classmethod
    def validate_hex_color(cls, v):
        if v is None:
            return v  # allow None
        if not isinstance(v, str):
            raise ValueError("background_color must be a string")
        # regex: # followed by 3 or 6 hex digits
        if not re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", v):
            raise ValueError(f"'{v}' is not a valid hex color")
        return v


class WordRowModel(BaseModel):
    cells: list[WordCellModel | str] = Field(default_factory=list)

    @field_validator("cells")
    @classmethod
    def validate_cells(cls, v):
        if isinstance(v, str):
            if not v.strip().lower() == "merge":
                raise ValueError("If a cell is a string, it must be 'merge'")
        return v


class WordTableModel(BaseModel):
    style: str | None = None
    rows: list[WordRowModel] = Field(default_factory=list)
