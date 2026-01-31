// Style types for exposing calamine's style information to Python

#[cfg(feature = "python")]
use pyo3::{pyclass, pymethods};

use calamine::{
    Alignment as CalAlignment, Border as CalBorder, BorderStyle as CalBorderStyle,
    Borders as CalBorders, Color as CalColor, ColumnWidth as CalColumnWidth, Fill as CalFill,
    FillPattern as CalFillPattern, Font as CalFont, FontStyle as CalFontStyle,
    FontWeight as CalFontWeight, HorizontalAlignment as CalHorizontalAlignment,
    NumberFormat as CalNumberFormat, Protection as CalProtection, RowHeight as CalRowHeight,
    Style as CalStyle, StyleRange as CalStyleRange, TextRotation as CalTextRotation,
    UnderlineStyle as CalUnderlineStyle, VerticalAlignment as CalVerticalAlignment,
    WorksheetLayout as CalWorksheetLayout,
};
use std::collections::HashMap;

/// ARGB Color
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "Color", get_all))]
pub struct Color {
    pub alpha: u8,
    pub red: u8,
    pub green: u8,
    pub blue: u8,
}

#[cfg(feature = "python")]
#[pymethods]
impl Color {
    fn __repr__(&self) -> String {
        format!(
            "Color(alpha={}, red={}, green={}, blue={})",
            self.alpha, self.red, self.green, self.blue
        )
    }

    /// Returns the color as a hex string (e.g., "#FF0000" for red)
    pub fn to_hex(&self) -> String {
        format!("#{:02X}{:02X}{:02X}", self.red, self.green, self.blue)
    }

    /// Returns the color as an ARGB integer
    pub fn to_argb(&self) -> u32 {
        ((self.alpha as u32) << 24)
            | ((self.red as u32) << 16)
            | ((self.green as u32) << 8)
            | (self.blue as u32)
    }
}

impl From<&CalColor> for Color {
    fn from(c: &CalColor) -> Self {
        Self {
            alpha: c.alpha,
            red: c.red,
            green: c.green,
            blue: c.blue,
        }
    }
}

/// Border style
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "BorderStyle", get_all))]
pub struct BorderStyle {
    pub style: String,
    pub color: Option<Color>,
}

#[cfg(feature = "python")]
#[pymethods]
impl BorderStyle {
    fn __repr__(&self) -> String {
        format!(
            "BorderStyle(style='{}', color={:?})",
            self.style,
            self.color.as_ref().map(|c| c.to_hex())
        )
    }
}

impl From<&CalBorder> for BorderStyle {
    fn from(b: &CalBorder) -> Self {
        let style = match b.style {
            CalBorderStyle::None => "none",
            CalBorderStyle::Thin => "thin",
            CalBorderStyle::Medium => "medium",
            CalBorderStyle::Thick => "thick",
            CalBorderStyle::Double => "double",
            CalBorderStyle::Hair => "hair",
            CalBorderStyle::Dashed => "dashed",
            CalBorderStyle::Dotted => "dotted",
            CalBorderStyle::MediumDashed => "mediumDashed",
            CalBorderStyle::DashDot => "dashDot",
            CalBorderStyle::DashDotDot => "dashDotDot",
            CalBorderStyle::SlantDashDot => "slantDashDot",
        }
        .to_string();
        Self {
            style,
            color: b.color.as_ref().map(Color::from),
        }
    }
}

/// All borders for a cell
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "Borders", get_all))]
pub struct Borders {
    pub left: BorderStyle,
    pub right: BorderStyle,
    pub top: BorderStyle,
    pub bottom: BorderStyle,
    pub diagonal_down: BorderStyle,
    pub diagonal_up: BorderStyle,
}

#[cfg(feature = "python")]
#[pymethods]
impl Borders {
    fn __repr__(&self) -> String {
        format!(
            "Borders(left={}, right={}, top={}, bottom={})",
            self.left.style, self.right.style, self.top.style, self.bottom.style
        )
    }
}

impl From<&CalBorders> for Borders {
    fn from(b: &CalBorders) -> Self {
        Self {
            left: BorderStyle::from(&b.left),
            right: BorderStyle::from(&b.right),
            top: BorderStyle::from(&b.top),
            bottom: BorderStyle::from(&b.bottom),
            diagonal_down: BorderStyle::from(&b.diagonal_down),
            diagonal_up: BorderStyle::from(&b.diagonal_up),
        }
    }
}

/// Font properties
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "Font", get_all))]
pub struct Font {
    pub name: Option<String>,
    pub size: Option<f64>,
    pub bold: bool,
    pub italic: bool,
    pub underline: String,
    pub strikethrough: bool,
    pub color: Option<Color>,
}

#[cfg(feature = "python")]
#[pymethods]
impl Font {
    fn __repr__(&self) -> String {
        format!(
            "Font(name={:?}, size={:?}, bold={}, italic={})",
            self.name, self.size, self.bold, self.italic
        )
    }
}

impl From<&CalFont> for Font {
    fn from(f: &CalFont) -> Self {
        let underline = match f.underline {
            CalUnderlineStyle::None => "none",
            CalUnderlineStyle::Single => "single",
            CalUnderlineStyle::Double => "double",
            CalUnderlineStyle::SingleAccounting => "singleAccounting",
            CalUnderlineStyle::DoubleAccounting => "doubleAccounting",
        }
        .to_string();
        Self {
            name: f.name.clone(),
            size: f.size,
            bold: f.weight == CalFontWeight::Bold,
            italic: f.style == CalFontStyle::Italic,
            underline,
            strikethrough: f.strikethrough,
            color: f.color.as_ref().map(Color::from),
        }
    }
}

/// Cell alignment
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "Alignment", get_all))]
pub struct Alignment {
    pub horizontal: String,
    pub vertical: String,
    pub text_rotation: Option<u16>,
    pub wrap_text: bool,
    pub indent: Option<u8>,
    pub shrink_to_fit: bool,
}

#[cfg(feature = "python")]
#[pymethods]
impl Alignment {
    fn __repr__(&self) -> String {
        format!(
            "Alignment(horizontal='{}', vertical='{}', wrap_text={})",
            self.horizontal, self.vertical, self.wrap_text
        )
    }
}

impl From<&CalAlignment> for Alignment {
    fn from(a: &CalAlignment) -> Self {
        let horizontal = match a.horizontal {
            CalHorizontalAlignment::Left => "left",
            CalHorizontalAlignment::Center => "center",
            CalHorizontalAlignment::Right => "right",
            CalHorizontalAlignment::Justify => "justify",
            CalHorizontalAlignment::Distributed => "distributed",
            CalHorizontalAlignment::Fill => "fill",
            CalHorizontalAlignment::General => "general",
        }
        .to_string();
        let vertical = match a.vertical {
            CalVerticalAlignment::Top => "top",
            CalVerticalAlignment::Center => "center",
            CalVerticalAlignment::Bottom => "bottom",
            CalVerticalAlignment::Justify => "justify",
            CalVerticalAlignment::Distributed => "distributed",
        }
        .to_string();
        let text_rotation = match a.text_rotation {
            CalTextRotation::None => None,
            CalTextRotation::Degrees(d) => Some(d),
            CalTextRotation::Stacked => Some(255), // Special value for stacked
        };
        Self {
            horizontal,
            vertical,
            text_rotation,
            wrap_text: a.wrap_text,
            indent: a.indent,
            shrink_to_fit: a.shrink_to_fit,
        }
    }
}

/// Fill properties
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "Fill", get_all))]
pub struct Fill {
    pub pattern: String,
    pub foreground_color: Option<Color>,
    pub background_color: Option<Color>,
}

#[cfg(feature = "python")]
#[pymethods]
impl Fill {
    fn __repr__(&self) -> String {
        format!(
            "Fill(pattern='{}', fg={:?}, bg={:?})",
            self.pattern,
            self.foreground_color.as_ref().map(|c| c.to_hex()),
            self.background_color.as_ref().map(|c| c.to_hex())
        )
    }
}

impl From<&CalFill> for Fill {
    fn from(f: &CalFill) -> Self {
        let pattern = match f.pattern {
            CalFillPattern::None => "none",
            CalFillPattern::Solid => "solid",
            CalFillPattern::DarkGray => "darkGray",
            CalFillPattern::MediumGray => "mediumGray",
            CalFillPattern::LightGray => "lightGray",
            CalFillPattern::Gray125 => "gray125",
            CalFillPattern::Gray0625 => "gray0625",
            CalFillPattern::DarkHorizontal => "darkHorizontal",
            CalFillPattern::DarkVertical => "darkVertical",
            CalFillPattern::DarkDown => "darkDown",
            CalFillPattern::DarkUp => "darkUp",
            CalFillPattern::DarkGrid => "darkGrid",
            CalFillPattern::DarkTrellis => "darkTrellis",
            CalFillPattern::LightHorizontal => "lightHorizontal",
            CalFillPattern::LightVertical => "lightVertical",
            CalFillPattern::LightDown => "lightDown",
            CalFillPattern::LightUp => "lightUp",
            CalFillPattern::LightGrid => "lightGrid",
            CalFillPattern::LightTrellis => "lightTrellis",
        }
        .to_string();
        Self {
            pattern,
            foreground_color: f.foreground_color.as_ref().map(Color::from),
            background_color: f.background_color.as_ref().map(Color::from),
        }
    }
}

/// Number format
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "NumberFormat", get_all))]
pub struct NumberFormat {
    pub format_code: String,
    pub format_id: Option<u32>,
}

#[cfg(feature = "python")]
#[pymethods]
impl NumberFormat {
    fn __repr__(&self) -> String {
        format!(
            "NumberFormat(code='{}', id={:?})",
            self.format_code, self.format_id
        )
    }
}

impl From<&CalNumberFormat> for NumberFormat {
    fn from(n: &CalNumberFormat) -> Self {
        Self {
            format_code: n.format_code.clone(),
            format_id: n.format_id,
        }
    }
}

/// Cell protection
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "Protection", get_all))]
pub struct Protection {
    pub locked: bool,
    pub hidden: bool,
}

#[cfg(feature = "python")]
#[pymethods]
impl Protection {
    fn __repr__(&self) -> String {
        format!("Protection(locked={}, hidden={})", self.locked, self.hidden)
    }
}

impl From<&CalProtection> for Protection {
    fn from(p: &CalProtection) -> Self {
        Self {
            locked: p.locked,
            hidden: p.hidden,
        }
    }
}

/// Complete cell style
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "Style", get_all))]
pub struct Style {
    pub style_id: Option<u32>,
    pub font: Option<Font>,
    pub fill: Option<Fill>,
    pub borders: Option<Borders>,
    pub alignment: Option<Alignment>,
    pub number_format: Option<NumberFormat>,
    pub protection: Option<Protection>,
}

#[cfg(feature = "python")]
#[pymethods]
impl Style {
    fn __repr__(&self) -> String {
        format!(
            "Style(id={:?}, font={}, fill={}, borders={}, alignment={})",
            self.style_id,
            self.font.is_some(),
            self.fill.is_some(),
            self.borders.is_some(),
            self.alignment.is_some()
        )
    }
}

impl From<&CalStyle> for Style {
    fn from(s: &CalStyle) -> Self {
        Self {
            style_id: s.style_id,
            font: s.font.as_ref().map(Font::from),
            fill: s.fill.as_ref().map(Fill::from),
            borders: s.borders.as_ref().map(Borders::from),
            alignment: s.alignment.as_ref().map(Alignment::from),
            number_format: s.number_format.as_ref().map(NumberFormat::from),
            protection: s.protection.as_ref().map(Protection::from),
        }
    }
}

/// A collection of styles for a worksheet, with style IDs for each cell
///
/// Note: We rebuild the palette from calamine's StyleRange because the palette
/// field is private in calamine. This is somewhat redundant work, but necessary
/// until calamine exposes a `palette()` getter. The `.cells()` iterator is used
/// to leverage calamine's RLE decompression.
#[derive(Debug)]
pub struct SheetStyles {
    /// The styles palette (style_id -> Style)
    pub palette: HashMap<u32, Style>,
    /// 2D array of style IDs (row-major order), matching the data range
    pub style_ids: Vec<Vec<u32>>,
    /// Start position of the style range (row, col)
    pub start: (u32, u32),
    /// End position of the style range (row, col)
    pub end: (u32, u32),
}

impl SheetStyles {
    pub fn from_calamine(style_range: &CalStyleRange) -> Self {
        let (start, end) = match (style_range.start(), style_range.end()) {
            (Some(s), Some(e)) => (s, e),
            _ => ((0, 0), (0, 0)),
        };

        let height = style_range.height();
        let width = style_range.width();

        // Pre-allocate the 2D style_ids array
        let mut style_ids: Vec<Vec<u32>> = vec![vec![0u32; width]; height];
        let mut palette: HashMap<u32, Style> = HashMap::new();

        // Use calamine's cells() iterator which handles RLE decompression
        for (row, col, style) in style_range.cells() {
            let id = style.style_id.unwrap_or(0);
            style_ids[row][col] = id;

            // Only insert if we haven't seen this style_id yet
            palette.entry(id).or_insert_with(|| Style::from(style));
        }

        // Ensure palette has default style at id 0
        palette
            .entry(0)
            .or_insert_with(|| Style::from(&CalStyle::default()));

        Self {
            palette,
            style_ids,
            start,
            end,
        }
    }
}

// ============================================================================
// Layout types (column widths, row heights)
// ============================================================================

/// Column width information
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "ColumnWidth", get_all))]
pub struct ColumnWidth {
    /// Column index (0-based)
    pub column: u32,
    /// Width in Excel character units
    pub width: f64,
    /// Whether the width is custom (manually set)
    pub custom_width: bool,
    /// Whether the column is hidden
    pub hidden: bool,
    /// Best fit width
    pub best_fit: bool,
}

#[cfg(feature = "python")]
#[pymethods]
impl ColumnWidth {
    fn __repr__(&self) -> String {
        format!(
            "ColumnWidth(column={}, width={:.2}, hidden={})",
            self.column, self.width, self.hidden
        )
    }
}

impl From<&CalColumnWidth> for ColumnWidth {
    fn from(c: &CalColumnWidth) -> Self {
        Self {
            column: c.column,
            width: c.width,
            custom_width: c.custom_width,
            hidden: c.hidden,
            best_fit: c.best_fit,
        }
    }
}

/// Row height information
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "RowHeight", get_all))]
pub struct RowHeight {
    /// Row index (0-based)
    pub row: u32,
    /// Height in points
    pub height: f64,
    /// Whether the height is custom (manually set)
    pub custom_height: bool,
    /// Whether the row is hidden
    pub hidden: bool,
}

#[cfg(feature = "python")]
#[pymethods]
impl RowHeight {
    fn __repr__(&self) -> String {
        format!(
            "RowHeight(row={}, height={:.2}, hidden={})",
            self.row, self.height, self.hidden
        )
    }
}

impl From<&CalRowHeight> for RowHeight {
    fn from(r: &CalRowHeight) -> Self {
        Self {
            row: r.row,
            height: r.height,
            custom_height: r.custom_height,
            hidden: r.hidden,
        }
    }
}

/// Worksheet layout information (column widths and row heights)
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "SheetLayout", get_all))]
pub struct SheetLayout {
    /// Default column width (in Excel character units)
    pub default_column_width: Option<f64>,
    /// Default row height (in points)
    pub default_row_height: Option<f64>,
    /// Column widths (only columns with custom widths)
    pub column_widths: HashMap<u32, ColumnWidth>,
    /// Row heights (only rows with custom heights)
    pub row_heights: HashMap<u32, RowHeight>,
}

#[cfg(feature = "python")]
#[pymethods]
impl SheetLayout {
    fn __repr__(&self) -> String {
        format!(
            "SheetLayout(default_col_width={:?}, default_row_height={:?}, columns={}, rows={})",
            self.default_column_width,
            self.default_row_height,
            self.column_widths.len(),
            self.row_heights.len()
        )
    }

    /// Get the effective width for a column (custom or default)
    pub fn get_column_width(&self, column: u32) -> f64 {
        self.column_widths
            .get(&column)
            .map(|cw| cw.width)
            .or(self.default_column_width)
            .unwrap_or(8.43) // Excel default for Calibri 11pt
    }

    /// Get the effective height for a row (custom or default)
    pub fn get_row_height(&self, row: u32) -> f64 {
        self.row_heights
            .get(&row)
            .map(|rh| rh.height)
            .or(self.default_row_height)
            .unwrap_or(15.0) // Excel default for Calibri 11pt
    }
}

impl From<&CalWorksheetLayout> for SheetLayout {
    fn from(layout: &CalWorksheetLayout) -> Self {
        let column_widths: HashMap<u32, ColumnWidth> = layout
            .column_widths
            .iter()
            .map(|(&col, cw)| (col, ColumnWidth::from(cw)))
            .collect();

        let row_heights: HashMap<u32, RowHeight> = layout
            .row_heights
            .iter()
            .map(|(&row, rh)| (row, RowHeight::from(rh)))
            .collect();

        Self {
            default_column_width: layout.default_column_width,
            default_row_height: layout.default_row_height,
            column_widths,
            row_heights,
        }
    }
}
