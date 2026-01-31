[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wordhelpers.svg)](https://img.shields.io/pypi/pyversions/wordhelpers)
[![PyPI](https://img.shields.io/pypi/v/wordhelpers.svg)](https://pypi.python.org/pypi/wordhelpers)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# wordhelpers
=============
Helper functions for [python-docx](https://python-docx.readthedocs.io/en/latest/). I found myself re-learning docx every time I wanted to use it in a project, so this provides and abstraction. You represent Word tables as a properly-formatted Python dictionary and the helper function converts it to a docx table.

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
    from wordhelpers import build_table, replace_placeholder_with_table
    ```
1. Create the docx Word document object with something like:
    ```python
    doc_obj = Document("a_word_template.docx")
    ```
1. Manipulate the document object as required (see the next section of this README for info on how to do that)
1. When all changes to your document object are complete, write them with:
    ```python
    doc_obj.save("output_file.docx")
    ```
# Manipulating the document object
wordhelpers provides two main functions available to your scripts:
1. build_table(<doc_obj>, <table_dict>, <remove_leading_para>)
1. replace_placeholder_with_table(<doc_obj>, <search_string>, <table_obj>)

### build_table(<doc_obj>, <table_dict>, <remove_leading_para>)
The purpose of this function is to allow the script author to model Word tables using Python dictionaries. If formatted properly, the module will translate the Python dictionary to the appropriate python-docx syntax and create the Word table object.

The build_table function has the following arguments:
- **<doc_obj>** - The python-docx Word document object created in step 3 of the "Usage" section above.
- **<table_dict>** - The Word table model (Python dictionary). The expected Python dictionary format to model a Word table is:
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
- **<remove_leading_para>** - This is an optional argument. If not set it will default to True. MS Word tables when created automatically have an empty paragraph at the top/beginning of the table cell. This can create unwanted spacing at the top of the table. By default (value set to "True") the paragraph will be deleted. If you want to keep the paragraph (to add text to it), set this to "False".

**IMPORTANT NOTE:** This adds the table object to very end of your Word file. If you want to relocate it, use the provided `replace_placeholder_with_table()` function (see below). 

### replace_placeholder_with_table(<doc_obj>, <search_string>, <table_obj>)
The purpose of this function is to search a Word file for a given string (the placeholder) and replace the string with a Word table object.

The replace_placeholder_with_table function has the following arguments:
- **<doc_obj>** - The python-docx Word document object created in step 2 of the "USING PYTHON-DOCX LIBRARY" section above.
- **<search_string>** - The string to search for in the document object (doc_obj)
- **<table_obj>** - The python-docx Word Table object that will replace the <search_string> in the document object (odc_obj)

It will relocate the table to the placeholder and remove the placeholder.-

### EXAMPLE
We start with a Microsoft Word template named "source-template.docx" that looks like this:

![Word Template](artwork/word_template.jpg)

Our sample Python script looks like this:
```python
from docx import Document
from dcnet_msofficetools.docx_extensions import build_table, replace_placeholder_with_table

doc_obj = Document("source-template.docx")

my_dictionary = {
    "style": None,
    "rows": [
        {
            "cells": [
                {
                    "paragraphs": [],
                    "table": {
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
                }
            ]
        }
    ]
}

my_table = build_table(doc_obj, my_dictionary)

replace_placeholder_with_table(doc_obj, '\[py_placeholder1\]', my_table)

doc_obj.save("output_word_doc.docx")
```

We run the Python script and it produces a new Word document named "output_word_doc.docx" that looks like this:

![Word Template](artwork/word_output.jpg)


The project provides some additional docx functions that may be useful to your project:
- ```get_para_by_string(doc_obj: _Document, search: str)```: Searches for a keyword in the docx object and returns there paragraph where the keyword is found
- ```insert_paragraph_after(paragraph: Paragraph, text: str = None, style: str = None)```: Searches for a keyword in the docx object and inserts a new paragraph immediately after it with the supplied text
- ```delete_paragraph(paragraph: Paragraph)```: Deletes a given paragraph (after you've inserted text after it for example)

As well as the following helper functions for the dictionary table models:
- ```insert_text_into_row(cell_text: list)```: Builds a row (dictionary) from a list of text where each list item is a column in the row. Supports "merge"
-```insert_text_by_table_coords(table: dict, row: int, col: int, text: str)```: Inserts text into a table dictionary given the row & column numbers.
- ```generate_table(num_rows: int, num_cols: int, header_row: list, style: str = None)```: Generates a basic table dictionary and populates the headers from a list of text (strings).