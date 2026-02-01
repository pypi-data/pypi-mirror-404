[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wordhelpers.svg)](https://img.shields.io/pypi/pyversions/wordhelpers)
[![PyPI](https://img.shields.io/pypi/v/wordhelpers.svg)](https://pypi.python.org/pypi/wordhelpers)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# wordhelpers
Helper functions for [python-docx](https://python-docx.readthedocs.io/en/latest/). I found myself re-learning docx every time I wanted to use it in a project, so this provides and abstraction. You represent Word tables as a properly-formatted Python dictionary or with the provided WordTableModel class and the helper function converts it to a docx table.

# Installation
wordhelpers can be installed via poetry with: ```poetry add wordhelpers```
or via pip with: ```pip install wordhelpers```

# Usage
For detailed documentation of the python-docx library see [python-docx](https://python-docx.readthedocs.io/en/latest/)

1. Import the python-docx library into your script with:
    ```python
    from docx import Document
    ```
1. Import the helpers from this project with:
    ```python
    from wordhelpers import WordTableModel, inject_table
    ```
1. Create the docx Word document object with something like:
    ```python
    doc_obj = Document("a_word_template.docx")
    ```
1. Add tables to the document object as required (see the next section of this README for info on how to do that)
1. When all changes to your document object are complete, write them with the docx `save()` method:
    ```python
    doc_obj.save("output_file.docx")
    ```
# Adding tables to the document object
There are two methods available for creating tables for addition to a word document:
1. The provided `WordTablesModel` class
1. A properly-formatted python dictionary

The WordTablesModel class has a number of methods available to help you build the table:
- ```add_row(width: int, text: list[str] = [], merge_cols: list[int] = [], background_color: str | None = None, style: str | None = None, alignment: AlignmentEnum | None = None)```
- ```add_text_to_row(row_index: int, text: list[str], style: str | None = None, alignment: AlignmentEnum | None = None)```
- ```add_text_to_cell(row_index: int, col_index: int, text: str, style: str | None = None, alignment: AlignmentEnum | None = None)```
- ```style_row(row_index: int, text_style: str)```
- ```style_cell(row_index: int, col_index: int, text_style: str)```
- ```color_row(row_index: int, background_color: str)```
- ```color_cell(row_index: int, col_index: int, background_color: str)```
- ```align_row(row_index: int, alignment: AlignmentEnum)```
- ```align_cell(row_index: int, col_index: int, alignment: AlignmentEnum)```
- ```add_table_to_cell(row_index: int, col_index: int, table: WordTableModel)```
- ```delete_row(row_index: int)```
- ```model_dump()```
- ```pretty_print()```
- ```write()```

If you prefer to create the tables manually via Python dictionary, the dictionary must follow a strict schema that looks something like this:
```python
{
    "style": None,
    "rows": [
        {
            "cells": [
                {
                    "width": None,
                    "background": None,
                    "paragraphs": [{"style":None,"alignment": "center", "text":"Some Text"}],
                    "table": {optional child table}
                },
                {
                    "merge": None
                },
            ]
        }
    ]
}
```
The cell **background** attribute is optional. If supplied with a hexidecimal color code, the cell will be shaded that color.

The cell **width** attribute is optional. If supplied with a decimal number (inches), it will hard-code that column's width to the supplied value.

The cell **table** attribute is optional. It can be used to nest tables within table cells. If "table" is provided, no other keys are required (background, paragraphs, etc).

The paragraph **style** attribute is optional. If set to anything besides None it will use the Word style referenced. The style must already exist in the source/template Word document.

The paragraph **alignment** attribute is optional. If set to ```"center"``` it will center-align the text within a cell, if set to ```"right"``` it will right-align the text within a cell

The **merge** key is optional. If used the cell will be merged with the cell above (from a dictionary view, to the left from a table view). Multiple merges can be used in a row to merge multiple cells.

By default a paragraph's **text** property will create a single-line (but wrapped) entry in the cell if the value is a string. If you would like to create a multi-line cell entry, supply the value as a list instead of a string. This will instruct the module to add a line break after each list item.

Schema enforcement of the dictionary is done through Pydantic v2 validations.

Injection of the table model (either via the class or a raw dictionary) is done via the provided ```inject_table()``` function.  
The function has the following parameters:
- doc_obj: _Document
- table: dict
- placeholder: str
- remove_leading_para: bool = True
- remove_placeholder: bool = True

Notice the table parameter must be a python dictionary. So if you've created the table via the provided ```WordTableModel``` class you pass it to ```inject_table()``` with: ```my_table.model_dump()```

- **<remove_leading_para>** - This is an optional argument. If not set it will default to True. MS Word tables when created automatically have an empty paragraph at the top/beginning of the table cell. This can create unwanted spacing at the top of the table. By default (value set to "True") the paragraph will be deleted. If you want to keep the paragraph (to add text to it), set this to "False".
- **<remove_placeholder>** - This is an optional argument. You can leave the placeholder (```remove_placeholder=False```) if you need to keep injecting tables below the placeholder before final deletion

### EXAMPLE
We start with a Microsoft Word template named "source-template.docx" that looks like this:

![Word Template](artwork/word_template.jpg)

Our sample Python script looks like this:
```python
from docx import Document
from wordhelpers import inject_table

doc_obj = Document("source-template.docx")

my_dictionary = {
    "style": "plain",
    "rows": [
        {
            "cells": [
                {
                    "background": "#506279",
                    "paragraphs":[{"style": "regularbold", "text": "Header 1:"}]
                },
                {
                    "background": "#506279",
                    "paragraphs":[{"style": "regularbold", "text": "Header 2:"}]
                },
                {
                    "background": "#506279",
                    "paragraphs":[{"style": "regularbold", "text": "Header 3:"}]
                }
            ]
        },
        {
            "cells": [
                {
                    "background": "#D5DCE4",
                    "paragraphs":[{"style": "No Spacing", "text": "Row 1 Data 1:"}]
                },
                {
                    "background": "#D5DCE4",
                    "paragraphs":[{"style": "No Spacing", "text": "Row 1 Data 2:"}]
                },
                {
                    "background": "#D5DCE4",
                    "paragraphs":[{"style": "No Spacing", "text": "Row 1 Data 3:"}]
                }
            ]
        },
        {
            "cells": [
                {
                    "paragraphs":[{"style": "No Spacing", "text": "Row 2 Data 1:"}]
                },
                {
                    "paragraphs":[{"style": "No Spacing", "text": "Row 2 Data 2:"}]
                },
                {
                    "paragraphs":[{"style": "No Spacing", "text": "Row 2 Data 3:"}]
                }
            ]
        },
        {
            "cells": [
                {
                    "background": "#D5DCE4",
                    "paragraphs":[{"style": "No Spacing", "text": "Row 3 Data 1:"}]
                },
                {
                    "background": "#D5DCE4",
                    "paragraphs":[{"style": "No Spacing", "text": "Row 3 Data 2:"}]
                },
                {
                    "background": "#D5DCE4",
                    "paragraphs":[{"style": "No Spacing", "text": "Row 3 Data 3:"}]
                }
            ]
        }
    ]                
}

inject_table(doc_obj, my_dictionary, "\[py_placeholder1\]")
doc_obj.save("output_word_doc.docx")
```

Using the provided ```WordTableModel``` class instead of the raw dictionary, the python code would look like this:
```python
from docx import Document
from wordhelpers import WordTableModel, inject_table

doc_obj = Document("source-template.docx")

my_table = WordTableModel()
my_table.style = "plain"
my_table.add_row(
    3,
    text=[
        "Header 1:",
        "Header 2:",
        "Header 3:",
    ],
    background_color="#506279",
    style="regularbold",
)
my_table.add_row(
    3,
    text=[
        "Row 1 Data 1:",
        "Row 1 Data 2:",
        "Row 1 Data 3:",
    ],
    background_color="#D5DCE4",
    style="No Spacing",
)
my_table.add_row(
    3,
    text=[
        "Row 2 Data 1:",
        "Row 2 Data 2:",
        "Row 2 Data 3:",
    ],
    style="No Spacing",
)
my_table.add_row(
    3,
    text=[
        "Row 3 Data 1:",
        "Row 3 Data 2:",
        "Row 3 Data 3:",
    ],
    background_color="#D5DCE4",
    style="No Spacing",
)

inject_table(doc_obj, my_table.model_dump(), "\[py_placeholder1\]")
doc_obj.save("output_word_doc.docx")
```

We run the Python script and it produces a new Word document named "output_word_doc.docx" that looks like this:

![Word Template](artwork/word_output.jpg)


The project provides some additional docx functions that may be useful to your project:
- ```get_para_by_string(doc_obj: _Document, search: str)```: Searches for a keyword in the docx object and returns there paragraph where the keyword is found
- ```insert_paragraph_after(paragraph: Paragraph, text: str = None, style: str = None)```: Searches for a keyword in the docx object and inserts a new paragraph immediately after it with the supplied text
- ```delete_paragraph(paragraph: Paragraph)```: Deletes a given paragraph (after you've inserted text after it for example)

As well as the following helper functions for building raw dictionary table models:
- ```insert_text_into_row(cell_text: list)```: Builds a row (dictionary) from a list of text where each list item is a column in the row. Supports "merge"
- ```insert_text_by_table_coords(table: dict, row: int, col: int, text: str)```: Inserts text into a table dictionary given the row & column numbers.
- ```generate_table(num_rows: int, num_cols: int, header_row: list, style: str = None)```: Generates a basic table dictionary and populates the headers from a list of text (strings).