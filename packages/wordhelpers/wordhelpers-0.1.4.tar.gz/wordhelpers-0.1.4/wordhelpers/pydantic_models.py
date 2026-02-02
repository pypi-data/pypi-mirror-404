# Built-In Imports
from __future__ import annotations
import re
from enum import Enum
from typing import Optional
import json

# Third-Party Imports
from pydantic import BaseModel, field_validator, Field, ConfigDict


class AlignmentEnum(str, Enum):
    left = "left"
    center = "center"
    right = "right"
    justify = "justify"
    distribute = "distribute"


class WordParagraphModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    style: str | None = None
    alignment: AlignmentEnum | None = None
    text: list[str] | str = Field(default_factory=list)


class WordCellModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
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
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    cells: list[WordCellModel | str] = Field(default_factory=list)

    @field_validator("cells")
    @classmethod
    def validate_cells(cls, v):
        # The only valid string value is "merge"
        if isinstance(v, str):
            if not v.strip().lower() == "merge":
                raise ValueError("If a cell is a string, it must be 'merge'")
        return v


class WordTableModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=False)
    style: str | None = None
    rows: list[WordRowModel] = Field(default_factory=list)

    def add_row(
        self,
        width: int,
        text: list[str] = [],
        merge_cols: list[int] = [],
        background_color: str | None = None,
        style: str | None = None,
        alignment: AlignmentEnum | None = None,
    ) -> None:

        # Make sure width is same as existing rows if any
        if self.rows:
            existing_width = len(self.rows[0].cells)
            if width != existing_width:
                raise ValueError(
                    f"New row width {width} does not match existing row width {existing_width}"
                )

        # Make sure text length is less than the row width minus merged columns
        num_merge_cols = len(merge_cols)
        if len(text) > width - num_merge_cols:
            raise ValueError(
                f"Text length {len(text)} exceeded expected length {width - num_merge_cols} based on width and merge_cols"
            )

        # Make sure merge_cols are valid
        for col in merge_cols:
            if not isinstance(col, int):
                raise ValueError(f"merge_cols must contain integers, got: {type(col)}")
            if col < 0 or col >= width:
                raise ValueError(f"merge_cols contains invalid column index: {col}")

        # Build the cells
        cells: list = []
        for i in range(width):
            if i in merge_cols:
                # Insert a merge placeholder
                cells.append("merge")
            else:
                # Build a normal cell
                paragraphs: list = []
                if text:
                    paragraphs = [
                        WordParagraphModel(
                            style=style, alignment=alignment, text=[text.pop(0)]
                        )
                    ]
                cells.append(
                    WordCellModel(
                        background_color=background_color, paragraphs=paragraphs
                    )
                )
        # Re-build the rows
        rows: list = self.rows.copy()
        rows.append(WordRowModel(cells=cells))
        self.rows = rows

    def add_text_to_row(
        self,
        row_index: int,
        text: list[str],
        style: str | None = None,
        alignment: AlignmentEnum | None = None,
    ) -> None:
        # Validate row_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")

        # Make sure text length is less than the row width minus merged columns
        num_merge_cols = len(
            [
                cell
                for cell in self.rows[row_index].cells
                if isinstance(cell, str) and cell == "merge"
            ]
        )
        width = len(self.rows[row_index].cells)
        if len(text) > width - num_merge_cols:
            raise ValueError(
                f"Text length {len(text)} exceeded expected length {width - num_merge_cols} based on width and merge_cols"
            )

        rows = self.rows.copy()
        row = rows[row_index]
        for cell in row.cells:
            if isinstance(cell, str) and cell == "merge":
                continue  # Skip merge cells
            if text:
                cell.paragraphs.append(
                    WordParagraphModel(
                        style=style, alignment=alignment, text=[text.pop(0)]
                    )
                )

        self.rows = rows

    def add_text_to_cell(
        self,
        row_index: int,
        col_index: int,
        text: str,
        style: str | None = None,
        alignment: AlignmentEnum | None = None,
    ) -> None:
        # Validate row_index and col_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")
        rows = self.rows.copy()
        row = rows[row_index]
        if col_index < 0 or col_index >= len(row.cells):
            raise IndexError(f"Column index {col_index} out of range")

        cell = row.cells[col_index]
        if isinstance(cell, str) and cell == "merge":
            raise ValueError("Cannot add text to a merged cell")

        cell.paragraphs.append(
            WordParagraphModel(style=style, alignment=alignment, text=[text])
        )

        self.rows = rows

    def style_row(self, row_index: int, text_style: str) -> None:
        # Validate row_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")

        rows = self.rows.copy()
        row = rows[row_index]

        for cell in row.cells:
            if isinstance(cell, str) and cell == "merge":
                continue  # Skip merge cells
            for paragraph in cell.paragraphs:
                paragraph.style = text_style

        self.rows = rows

    def style_cell(self, row_index: int, col_index: int, text_style: str) -> None:
        # Validate row_index and col_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")
        rows = self.rows.copy()
        row = rows[row_index]
        if col_index < 0 or col_index >= len(row.cells):
            raise IndexError(f"Column index {col_index} out of range")

        cell = row.cells[col_index]
        if isinstance(cell, str) and cell == "merge":
            raise ValueError("Cannot style a merged cell")

        for paragraph in cell.paragraphs:
            paragraph.style = text_style

        self.rows = rows

    def color_row(self, row_index: int, background_color: str) -> None:
        # Validate row_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")

        rows = self.rows.copy()
        row = rows[row_index]

        for cell in row.cells:
            if isinstance(cell, str) and cell == "merge":
                continue  # Skip merge cells
            cell.background_color = background_color

        self.rows = rows

    def color_cell(self, row_index: int, col_index: int, background_color: str) -> None:
        # Validate row_index and col_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")
        rows = self.rows.copy()
        row = rows[row_index]
        if col_index < 0 or col_index >= len(row.cells):
            raise IndexError(f"Column index {col_index} out of range")

        cell = row.cells[col_index]
        if isinstance(cell, str) and cell == "merge":
            raise ValueError("Cannot color a merged cell")

        cell.background_color = background_color

        self.rows = rows

    def align_row(self, row_index: int, alignment: AlignmentEnum) -> None:
        # Validate row_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")

        rows = self.rows.copy()
        row = rows[row_index]

        for cell in row.cells:
            if isinstance(cell, str) and cell == "merge":
                continue  # Skip merge cells
            for paragraph in cell.paragraphs:
                paragraph.alignment = alignment

        self.rows = rows

    def align_cell(
        self, row_index: int, col_index: int, alignment: AlignmentEnum
    ) -> None:
        # Validate row_index and col_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")
        rows = self.rows.copy()
        row = rows[row_index]
        if col_index < 0 or col_index >= len(row.cells):
            raise IndexError(f"Column index {col_index} out of range")

        cell = row.cells[col_index]
        if isinstance(cell, str) and cell == "merge":
            raise ValueError("Cannot align a merged cell")

        for paragraph in cell.paragraphs:
            paragraph.alignment = alignment

        self.rows = rows

    def add_table_to_cell(
        self, row_index: int, col_index: int, table: WordTableModel
    ) -> None:
        # Validate row_index and col_index
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")
        rows = self.rows.copy()
        row = rows[row_index]
        if col_index < 0 or col_index >= len(row.cells):
            raise IndexError(f"Column index {col_index} out of range")
        cell = row.cells[col_index]

        if isinstance(cell, str) and cell == "merge":
            raise ValueError("Cannot add table to a merged cell")

        cell.table = table

        self.rows = rows

    def delete_row(self, row_index: int) -> None:
        if row_index < 0 or row_index >= len(self.rows):
            raise IndexError(f"Row index {row_index} out of range")
        rows = self.rows.copy()
        del rows[row_index]
        self.rows = rows

    def pretty_print(self) -> None:
        print(json.dumps(self.model_dump(), indent=4))

    def write(self, filepath: str) -> None:
        with open(filepath, "w") as f:
            json.dump(self.model_dump(), f, indent=4)
