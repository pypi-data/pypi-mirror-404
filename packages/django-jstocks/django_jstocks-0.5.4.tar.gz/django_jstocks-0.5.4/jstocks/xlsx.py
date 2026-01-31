from datetime import datetime, date
from decimal import Decimal
from typing import Any, List
from django.utils.html import strip_tags
from openpyxl import Workbook  # type: ignore
from openpyxl.cell import Cell  # type: ignore
from openpyxl.styles import Alignment, NamedStyle  # type: ignore
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore


def set_cell_value(sheet: Worksheet, row_index: int, column_index: int, val: Any):
    assert row_index is not None
    assert column_index is not None
    assert isinstance(sheet, Worksheet)

    c = sheet.cell(row_index + 1, column_index + 1)
    assert isinstance(c, Cell)
    if isinstance(val, int):
        c.number_format = "0"
        c.alignment = Alignment(horizontal="right")
    elif isinstance(val, Decimal):
        c.number_format = "0.00"
        c.alignment = Alignment(horizontal="right")
    elif isinstance(val, (datetime, date)):
        c.style = NamedStyle(name="datetime", number_format="YYYY-MM-DD")
    else:
        val = strip_tags(str(val if val is not None else ""))
    c.value = val
    return c


def create_workbook_from_rows(rows: List[List[Any]]) -> Workbook:
    book = Workbook()
    sheet = book.active
    assert isinstance(sheet, Worksheet)
    for row_ix, row in enumerate(list(rows)):
        for col_ix, val in enumerate(list(row)):
            set_cell_value(sheet, row_ix, col_ix, val)
    return book
