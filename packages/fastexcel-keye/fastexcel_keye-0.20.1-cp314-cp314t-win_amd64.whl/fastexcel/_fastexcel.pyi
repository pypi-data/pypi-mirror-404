from __future__ import annotations

import typing
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import pyarrow as pa

DType = Literal["null", "int", "float", "string", "boolean", "datetime", "date", "duration"]
DTypeMap = dict[str | int, DType]
ColumnNameFrom = Literal["provided", "looked_up", "generated"]
DTypeFrom = Literal["provided_for_all", "provided_by_index", "provided_by_name", "guessed"]
SheetVisible = Literal["visible", "hidden", "veryhidden"]

class ColumnInfoNoDtype:
    def __init__(
        self,
        *,
        name: str,
        index: int,
        absolute_index: int,
        column_name_from: ColumnNameFrom,
    ) -> None: ...
    @property
    def name(self) -> str: ...
    @property
    def index(self) -> int: ...
    @property
    def absolute_index(self) -> int: ...
    @property
    def column_name_from(self) -> ColumnNameFrom: ...

class ColumnInfo:
    def __init__(
        self,
        *,
        name: str,
        index: int,
        absolute_index: int,
        column_name_from: ColumnNameFrom,
        dtype: DType,
        dtype_from: DTypeFrom,
    ) -> None: ...
    @property
    def name(self) -> str: ...
    @property
    def index(self) -> int: ...
    @property
    def absolute_index(self) -> int: ...
    @property
    def dtype(self) -> DType: ...
    @property
    def column_name_from(self) -> ColumnNameFrom: ...
    @property
    def dtype_from(self) -> DTypeFrom: ...

class DefinedName:
    def __init__(
        self,
        *,
        name: str,
        formula: str,
    ) -> None: ...
    @property
    def name(self) -> str: ...
    @property
    def formula(self) -> str: ...

class CellError:
    @property
    def position(self) -> tuple[int, int]: ...
    @property
    def row_offset(self) -> int: ...
    @property
    def offset_position(self) -> tuple[int, int]: ...
    @property
    def detail(self) -> str: ...

class CellErrors:
    @property
    def errors(self) -> list[CellError]: ...

class _ExcelSheet:
    @property
    def name(self) -> str:
        """The name of the sheet"""
    @property
    def width(self) -> int:
        """The sheet's width"""
    @property
    def height(self) -> int:
        """The sheet's height"""
    @property
    def total_height(self) -> int:
        """The sheet's total height"""
    @property
    def offset(self) -> int:
        """The sheet's offset before data starts"""
    @property
    def selected_columns(self) -> list[ColumnInfo]:
        """The sheet's selected columns"""
    def available_columns(self) -> list[ColumnInfo]:
        """The columns available for the given sheet"""
    @property
    def specified_dtypes(self) -> DTypeMap | None:
        """The dtypes specified for the sheet"""
    @property
    def visible(self) -> SheetVisible:
        """The visibility of the sheet"""
    def to_arrow(self) -> pa.RecordBatch:
        """Converts the sheet to a pyarrow `RecordBatch`

        Requires the `pyarrow` extra to be installed.
        """
    def to_arrow_with_errors(self) -> tuple[pa.RecordBatch, CellErrors]:
        """Converts the sheet to a pyarrow `RecordBatch` with error information.

        Stores the positions of any values that cannot be parsed as the specified type and were
        therefore converted to None.

        Requires the `pyarrow` extra to be installed.
        """
    def __arrow_c_schema__(self) -> object:
        """Export the schema as an `ArrowSchema` `PyCapsule`.

        https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html#arrowschema-export

        The Arrow PyCapsule Interface enables zero-copy data exchange with
        Arrow-compatible libraries without requiring PyArrow as a dependency.
        """
    def __arrow_c_array__(self, requested_schema: object = None) -> tuple[object, object]:
        """Export the schema and data as a pair of `ArrowSchema` and `ArrowArray` `PyCapsules`.

        The optional `requested_schema` parameter allows for potential schema conversion.

        https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html#arrowarray-export

        The Arrow PyCapsule Interface enables zero-copy data exchange with
        Arrow-compatible libraries without requiring PyArrow as a dependency.
        """

class _ExcelTable:
    @property
    def name(self) -> str:
        """The name of the table"""
    @property
    def sheet_name(self) -> str:
        """The name of the sheet this table belongs to"""
    @property
    def width(self) -> int:
        """The table's width"""
    @property
    def height(self) -> int:
        """The table's height"""
    @property
    def total_height(self) -> int:
        """The table's total height"""
    @property
    def offset(self) -> int:
        """The table's offset before data starts"""
    @property
    def selected_columns(self) -> list[ColumnInfo]:
        """The table's selected columns"""
    def available_columns(self) -> list[ColumnInfo]:
        """The columns available for the given table"""
    @property
    def specified_dtypes(self) -> DTypeMap | None:
        """The dtypes specified for the table"""
    def to_arrow(self) -> pa.RecordBatch:
        """Converts the table to a pyarrow `RecordBatch`

        Requires the `pyarrow` extra to be installed.
        """
    def __arrow_c_schema__(self) -> object:
        """Export the schema as an `ArrowSchema` `PyCapsule`.

        https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html#arrowschema-export

        The Arrow PyCapsule Interface enables zero-copy data exchange with
        Arrow-compatible libraries without requiring PyArrow as a dependency.
        """

    def __arrow_c_array__(self, requested_schema: object = None) -> tuple[object, object]:
        """Export the schema and data as a pair of `ArrowSchema` and `ArrowArray` `PyCapsules`.

        The optional `requested_schema` parameter allows for potential schema conversion.

        https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html#arrowarray-export

        The Arrow PyCapsule Interface enables zero-copy data exchange with
        Arrow-compatible libraries without requiring PyArrow as a dependency.
        """

# Style types

class Color:
    """ARGB Color"""

    @property
    def alpha(self) -> int: ...
    @property
    def red(self) -> int: ...
    @property
    def green(self) -> int: ...
    @property
    def blue(self) -> int: ...
    def to_hex(self) -> str:
        """Returns the color as a hex string (e.g., '#FF0000' for red)"""
    def to_argb(self) -> int:
        """Returns the color as an ARGB integer"""

class BorderStyle:
    """Border style for a single side"""

    @property
    def style(self) -> str:
        """Border style: 'none', 'thin', 'medium', 'thick', 'double', 'hair', etc."""
    @property
    def color(self) -> Color | None: ...

class Borders:
    """All borders for a cell"""

    @property
    def left(self) -> BorderStyle: ...
    @property
    def right(self) -> BorderStyle: ...
    @property
    def top(self) -> BorderStyle: ...
    @property
    def bottom(self) -> BorderStyle: ...
    @property
    def diagonal_down(self) -> BorderStyle: ...
    @property
    def diagonal_up(self) -> BorderStyle: ...

class Font:
    """Font properties"""

    @property
    def name(self) -> str | None: ...
    @property
    def size(self) -> float | None: ...
    @property
    def bold(self) -> bool: ...
    @property
    def italic(self) -> bool: ...
    @property
    def underline(self) -> str:
        """Underline style: 'none', 'single', 'double', 'singleAccounting', 'doubleAccounting'"""
    @property
    def strikethrough(self) -> bool: ...
    @property
    def color(self) -> Color | None: ...

class Alignment:
    """Cell alignment properties"""

    @property
    def horizontal(self) -> str:
        """Horizontal alignment: 'left', 'center', 'right', 'justify', 'fill', etc."""
    @property
    def vertical(self) -> str:
        """Vertical alignment: 'top', 'center', 'bottom', 'justify', 'distributed'"""
    @property
    def text_rotation(self) -> int | None:
        """Text rotation in degrees (0-180), or 255 for stacked text"""
    @property
    def wrap_text(self) -> bool: ...
    @property
    def indent(self) -> int | None: ...
    @property
    def shrink_to_fit(self) -> bool: ...

class Fill:
    """Fill properties"""

    @property
    def pattern(self) -> str:
        """Fill pattern: 'none', 'solid', 'darkGray', 'mediumGray', 'lightGray', etc."""
    @property
    def foreground_color(self) -> Color | None: ...
    @property
    def background_color(self) -> Color | None: ...

class NumberFormat:
    """Number format"""

    @property
    def format_code(self) -> str:
        """The format code string (e.g., 'General', '0.00', 'yyyy-mm-dd')"""
    @property
    def format_id(self) -> int | None:
        """The format ID"""

class Protection:
    """Cell protection properties"""

    @property
    def locked(self) -> bool: ...
    @property
    def hidden(self) -> bool: ...

class Style:
    """Complete cell style"""

    @property
    def style_id(self) -> int | None:
        """The Excel style ID"""
    @property
    def font(self) -> Font | None: ...
    @property
    def fill(self) -> Fill | None: ...
    @property
    def borders(self) -> Borders | None: ...
    @property
    def alignment(self) -> Alignment | None: ...
    @property
    def number_format(self) -> NumberFormat | None: ...
    @property
    def protection(self) -> Protection | None: ...

# Layout types

class ColumnWidth:
    """Column width information"""

    @property
    def column(self) -> int:
        """Column index (0-based)"""
    @property
    def width(self) -> float:
        """Width in Excel character units"""
    @property
    def custom_width(self) -> bool:
        """Whether the width is custom (manually set)"""
    @property
    def hidden(self) -> bool:
        """Whether the column is hidden"""
    @property
    def best_fit(self) -> bool:
        """Best fit width"""

class RowHeight:
    """Row height information"""

    @property
    def row(self) -> int:
        """Row index (0-based)"""
    @property
    def height(self) -> float:
        """Height in points"""
    @property
    def custom_height(self) -> bool:
        """Whether the height is custom (manually set)"""
    @property
    def hidden(self) -> bool:
        """Whether the row is hidden"""

class SheetLayout:
    """Worksheet layout information (column widths and row heights)"""

    @property
    def default_column_width(self) -> float | None:
        """Default column width in Excel character units"""
    @property
    def default_row_height(self) -> float | None:
        """Default row height in points"""
    @property
    def column_widths(self) -> dict[int, ColumnWidth]:
        """Column widths (only columns with custom widths)"""
    @property
    def row_heights(self) -> dict[int, RowHeight]:
        """Row heights (only rows with custom heights)"""
    def get_column_width(self, column: int) -> float:
        """Get the effective width for a column (custom or default)"""
    def get_row_height(self, row: int) -> float:
        """Get the effective height for a row (custom or default)"""

class _ExcelReader:
    """A class representing an open Excel file and allowing to read its sheets"""

    @typing.overload
    def load_sheet(
        self,
        idx_or_name: str | int,
        *,
        header_row: int | None = 0,
        column_names: list[str] | None = None,
        skip_rows: int | list[int] | Callable[[int], bool] | None = None,
        n_rows: int | None = None,
        schema_sample_rows: int | None = 1_000,
        dtype_coercion: Literal["coerce", "strict"] = "coerce",
        use_columns: list[str]
        | list[int]
        | str
        | Callable[[ColumnInfoNoDtype], bool]
        | None = None,
        dtypes: DType | DTypeMap | None = None,
        eager: Literal[False] = ...,
        skip_whitespace_tail_rows: bool = False,
        whitespace_as_null: bool = False,
    ) -> _ExcelSheet: ...
    @typing.overload
    def load_sheet(
        self,
        idx_or_name: str | int,
        *,
        header_row: int | None = 0,
        column_names: list[str] | None = None,
        skip_rows: int | list[int] | Callable[[int], bool] | None = None,
        n_rows: int | None = None,
        schema_sample_rows: int | None = 1_000,
        dtype_coercion: Literal["coerce", "strict"] = "coerce",
        use_columns: list[str]
        | list[int]
        | str
        | Callable[[ColumnInfoNoDtype], bool]
        | None = None,
        dtypes: DType | DTypeMap | None = None,
        eager: Literal[True] = ...,
        skip_whitespace_tail_rows: bool = False,
        whitespace_as_null: bool = False,
    ) -> pa.RecordBatch: ...
    @typing.overload
    def load_sheet(
        self,
        idx_or_name: str | int,
        *,
        header_row: int | None = 0,
        column_names: list[str] | None = None,
        skip_rows: int | list[int] | Callable[[int], bool] | None = None,
        n_rows: int | None = None,
        schema_sample_rows: int | None = 1_000,
        dtype_coercion: Literal["coerce", "strict"] = "coerce",
        use_columns: list[str]
        | list[int]
        | str
        | Callable[[ColumnInfoNoDtype], bool]
        | None = None,
        dtypes: DType | DTypeMap | None = None,
        eager: bool = False,
        skip_whitespace_tail_rows: bool = False,
        whitespace_as_null: bool = False,
    ) -> pa.RecordBatch: ...
    @typing.overload
    def load_table(
        self,
        name: str,
        *,
        header_row: int | None = None,
        column_names: list[str] | None = None,
        skip_rows: int | list[int] | Callable[[int], bool] | None = None,
        n_rows: int | None = None,
        schema_sample_rows: int | None = 1_000,
        dtype_coercion: Literal["coerce", "strict"] = "coerce",
        use_columns: list[str]
        | list[int]
        | str
        | Callable[[ColumnInfoNoDtype], bool]
        | None = None,
        dtypes: DType | DTypeMap | None = None,
        eager: Literal[False] = ...,
        skip_whitespace_tail_rows: bool = False,
        whitespace_as_null: bool = False,
    ) -> _ExcelTable: ...
    @typing.overload
    def load_table(
        self,
        name: str,
        *,
        header_row: int | None = None,
        column_names: list[str] | None = None,
        skip_rows: int | list[int] | Callable[[int], bool] | None = None,
        n_rows: int | None = None,
        schema_sample_rows: int | None = 1_000,
        dtype_coercion: Literal["coerce", "strict"] = "coerce",
        use_columns: list[str]
        | list[int]
        | str
        | Callable[[ColumnInfoNoDtype], bool]
        | None = None,
        dtypes: DType | DTypeMap | None = None,
        eager: Literal[True] = ...,
        skip_whitespace_tail_rows: bool = False,
        whitespace_as_null: bool = False,
    ) -> pa.RecordBatch: ...
    @property
    def sheet_names(self) -> list[str]: ...
    def table_names(self, sheet_name: str | None = None) -> list[str]: ...
    def defined_names(self) -> list[DefinedName]: ...
    def get_style_ids(self, idx_or_name: str | int) -> list[list[int]]:
        """Get a 2D array of style IDs for each cell in the sheet.

        Use with `get_style_palette()` to look up the style for each cell.
        """
    def get_style_palette(self, idx_or_name: str | int) -> dict[int, Style]:
        """Get a mapping of style ID to Style object for the sheet.

        Use with `get_style_ids()` to look up the style for each cell.
        """
    def get_layout(self, idx_or_name: str | int) -> SheetLayout:
        """Get the layout information (column widths, row heights) for the sheet."""

def read_excel(source: str | bytes) -> _ExcelReader:
    """Reads an excel file and returns an ExcelReader"""

__version__: str

# Exceptions
class FastExcelError(Exception): ...
class UnsupportedColumnTypeCombinationError(FastExcelError): ...
class CannotRetrieveCellDataError(FastExcelError): ...
class CalamineCellError(FastExcelError): ...
class CalamineError(FastExcelError): ...
class SheetNotFoundError(FastExcelError): ...
class ColumnNotFoundError(FastExcelError): ...
class ArrowError(FastExcelError): ...
class InvalidParametersError(FastExcelError): ...
