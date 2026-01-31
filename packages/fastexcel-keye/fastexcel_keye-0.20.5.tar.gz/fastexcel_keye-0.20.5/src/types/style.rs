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
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
#[derive(Debug, Clone, PartialEq)]
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
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
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
#[derive(Debug, Clone, PartialEq)]
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

impl Style {
    /// Compare styles by their visual properties (ignoring style_id)
    pub fn style_equals(&self, other: &Self) -> bool {
        self.font == other.font
            && self.fill == other.fill
            && self.borders == other.borders
            && self.alignment == other.alignment
            && self.number_format == other.number_format
            && self.protection == other.protection
    }
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

/// A hashable key for style deduplication (converts f64 to bits for hashing)
#[derive(PartialEq, Eq, Hash)]
struct StyleKey {
    font_name: Option<String>,
    font_size_bits: Option<u64>,
    font_bold: bool,
    font_italic: bool,
    font_underline: String,
    font_strikethrough: bool,
    font_color: Option<(u8, u8, u8, u8)>,
    fill_pattern: String,
    fill_fg: Option<(u8, u8, u8, u8)>,
    fill_bg: Option<(u8, u8, u8, u8)>,
    borders: Option<(String, String, String, String, String, String)>, // left, right, top, bottom, diag_down, diag_up styles
    alignment: Option<(String, String, bool, Option<u64>, Option<u64>, bool)>, // h, v, wrap, rotation_bits, indent_bits, shrink
    number_format: Option<(String, Option<u32>)>,
    protection: Option<(bool, bool)>,
}

impl StyleKey {
    fn from_calamine(s: &CalStyle) -> Self {
        let font_color = s.font.as_ref().and_then(|f| {
            f.color.as_ref().map(|c| (c.alpha, c.red, c.green, c.blue))
        });

        let (fill_pattern, fill_fg, fill_bg) = s.fill.as_ref().map(|f| {
            let pattern = format!("{:?}", f.pattern);
            let fg = f.foreground_color.as_ref().map(|c| (c.alpha, c.red, c.green, c.blue));
            let bg = f.background_color.as_ref().map(|c| (c.alpha, c.red, c.green, c.blue));
            (pattern, fg, bg)
        }).unwrap_or_else(|| (String::new(), None, None));

        let borders = s.borders.as_ref().map(|b| {
            (
                format!("{:?}", b.left.style),
                format!("{:?}", b.right.style),
                format!("{:?}", b.top.style),
                format!("{:?}", b.bottom.style),
                format!("{:?}", b.diagonal_down.style),
                format!("{:?}", b.diagonal_up.style),
            )
        });

        let alignment = s.alignment.as_ref().map(|a| {
            let rotation_bits = match a.text_rotation {
                CalTextRotation::None => None,
                CalTextRotation::Degrees(n) => Some((n as f64).to_bits()),
                CalTextRotation::Stacked => Some(255f64.to_bits()),
            };
            (
                format!("{:?}", a.horizontal),
                format!("{:?}", a.vertical),
                a.wrap_text,
                rotation_bits,
                a.indent.map(|i| (i as f64).to_bits()),
                a.shrink_to_fit,
            )
        });

        let number_format = s.number_format.as_ref().map(|n| {
            (n.format_code.clone(), n.format_id)
        });

        let protection = s.protection.as_ref().map(|p| (p.locked, p.hidden));

        Self {
            font_name: s.font.as_ref().and_then(|f| f.name.clone()),
            font_size_bits: s.font.as_ref().and_then(|f| f.size.map(|sz| sz.to_bits())),
            font_bold: s.font.as_ref().map(|f| f.weight == CalFontWeight::Bold).unwrap_or(false),
            font_italic: s.font.as_ref().map(|f| f.style == CalFontStyle::Italic).unwrap_or(false),
            font_underline: s.font.as_ref().map(|f| format!("{:?}", f.underline)).unwrap_or_default(),
            font_strikethrough: s.font.as_ref().map(|f| f.strikethrough).unwrap_or(false),
            font_color,
            fill_pattern,
            fill_fg,
            fill_bg,
            borders,
            alignment,
            number_format,
            protection,
        }
    }
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

        // O(1) content-based deduplication using a hashable key
        let mut key_to_id: HashMap<StyleKey, u32> = HashMap::new();
        let mut next_id: u32 = 0;

        // Use calamine's cells() iterator which handles RLE decompression
        for (row, col, cal_style) in style_range.cells() {
            let key = StyleKey::from_calamine(cal_style);

            let id = *key_to_id.entry(key).or_insert_with(|| {
                let id = next_id;
                next_id += 1;
                palette.insert(id, Style::from(cal_style));
                id
            });

            style_ids[row][col] = id;
        }

        // Ensure palette has at least one entry (default style at id 0)
        if palette.is_empty() {
            palette.insert(0, Style::from(&CalStyle::default()));
        }

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

// ============================================================================
// Merged cells
// ============================================================================

use calamine::Dimensions as CalDimensions;

/// A merged cell region
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyclass(name = "MergedCell", get_all))]
pub struct MergedCell {
    /// Start row (0-based)
    pub start_row: u32,
    /// Start column (0-based)
    pub start_col: u32,
    /// End row (0-based, inclusive)
    pub end_row: u32,
    /// End column (0-based, inclusive)
    pub end_col: u32,
}

#[cfg(feature = "python")]
#[pymethods]
impl MergedCell {
    fn __repr__(&self) -> String {
        format!(
            "MergedCell(start=({}, {}), end=({}, {}))",
            self.start_row, self.start_col, self.end_row, self.end_col
        )
    }

    /// Get the number of rows spanned by this merged cell
    pub fn row_span(&self) -> u32 {
        self.end_row - self.start_row + 1
    }

    /// Get the number of columns spanned by this merged cell
    pub fn col_span(&self) -> u32 {
        self.end_col - self.start_col + 1
    }

    /// Check if a cell position is within this merged region
    pub fn contains(&self, row: u32, col: u32) -> bool {
        row >= self.start_row && row <= self.end_row && col >= self.start_col && col <= self.end_col
    }
}

impl From<&CalDimensions> for MergedCell {
    fn from(dim: &CalDimensions) -> Self {
        Self {
            start_row: dim.start.0,
            start_col: dim.start.1,
            end_row: dim.end.0,
            end_col: dim.end.1,
        }
    }
}
