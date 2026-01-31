from typing import List, Any, Tuple, Dict
from openpyxl.cell import Cell  # type: ignore
from openpyxl.utils import range_boundaries  # type: ignore
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore


def openpyx_get_dimensions(sheet: Worksheet) -> Tuple[int, int]:
    """Returns number of columns, rows."""
    cols, rows = range_boundaries(sheet.dimensions)[2:4]
    return cols, rows


def openpyxl_get_row_values(sheet: Worksheet, row: int) -> List[Any]:
    cols = openpyx_get_dimensions(sheet)[0]
    out: List[Any] = []
    for col in range(1, cols + 1):
        cell = sheet.cell(row, col)
        out.append(cell.value)
    return out


def openpyxl_get_cell_by_column_label(sheet: Worksheet, row: int, col_label: str, col_label_to_col_number: Dict[str, int]) -> Cell:
    col = col_label_to_col_number[col_label]
    return sheet.cell(row, col)
