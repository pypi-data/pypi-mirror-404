#! /usr/local/bin/python3
"""Extension of the MultiFormat class for DOCX files."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from typing import Optional, Callable
from docx import Document
from docx.document import Document as DocumentObject
from docx.text.paragraph import Paragraph
from docx.shared import Inches, Twips
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from mformat.mformat import FormatterDescriptor, MultiFormat
from mformat.mformat_state import MultiFormatState, Formatting


class MultiFormatDocx(MultiFormat):
    """Extension of the MultiFormat class for DOCX files."""

    def __init__(self, file_name: str, url_as_text: bool = False,
                 file_exists_callback: Optional[Callable[[str], None]] = None):
        """Initialize the MultiFormatDocx class.

        Args:
            file_name: The name of the file to write to.
            url_as_text: Format URLs as text not clickable URLs.
            file_exists_callback: A callback function to call if the file
                                  already exists. Return to allow the file to
                                  be overwritten. Raise an exception to prevent
                                  the file from being overwritten.
                                  (May for instance save existing file as
                                  backup.)
                                  (Default is to raise an exception.)
        """
        self.doc: DocumentObject = Document()
        self.current_paragraph: Optional[Paragraph] = None
        super().__init__(file_name=file_name, url_as_text=url_as_text,
                         file_exists_callback=file_exists_callback)

    @classmethod
    def file_name_extension(cls) -> str:
        """Get the file name extension for the formatter."""
        return '.docx'

    @classmethod
    def get_arg_desciption(cls) -> FormatterDescriptor:
        """Get the description of the arguments for the formatter."""
        return FormatterDescriptor(name='docx', mandatory_args=[],
                                   optional_args=[])

    def open(self) -> None:
        """Open the file.

        Avoid using this method directly.
        Use as a context manager instead, using a with statement.
        """
        self.doc.save(self.file_name)

    def _close(self) -> None:
        """Close the file.

        Avoid using this method directly.
        Use as a context manager instead, using a with statement.
        """
        if self.state == MultiFormatState.EMPTY:
            return
        self.doc.save(self.file_name)

    def _write_file_prefix(self) -> None:
        """Write the file prefix.

        For DOCX files, this is a no-op since the document
        structure is handled by python-docx.
        """

    def _write_file_suffix(self) -> None:
        """Write the file suffix.

        For DOCX files, this is a no-op since the document
        structure is handled by python-docx.
        """

    def _start_paragraph(self) -> None:
        """Start a paragraph."""
        self.current_paragraph = self.doc.add_paragraph()

    def _end_paragraph(self) -> None:
        """End a paragraph."""
        self.current_paragraph = None

    def _start_heading(self, level: int) -> None:
        """Start a heading.

        Args:
            level: The level of the heading (1-9).
        """
        self.current_paragraph = self.doc.add_heading(level=level)

    def _end_heading(self, level: int) -> None:
        """End a heading.

        Args:
            level: The level of the heading (1-9).
        """
        self.current_paragraph = None

    def _write_text(self, text: str, state: MultiFormatState,
                    formatting: Formatting) -> None:
        """Write text into current item (paragraph, bullet list item, etc.).

        Args:
            text: The text to write into the current item.
            state: The state of the current item.
            formatting: The formatting of the text.
        """
        if self.current_paragraph is None:
            raise RuntimeError('No current paragraph to write text into')
        run = self.current_paragraph.add_run(text)
        if formatting.bold:
            run.bold = True
        if formatting.italic:
            run.italic = True

    def _write_url(self, url: str, text: Optional[str],
                   state: MultiFormatState,
                   formatting: Formatting) -> None:
        """Write a URL into current item (paragraph, bullet list item, etc.).

        Args:
            url: The URL to write into the current item.
            text: The text to display for the URL.
            state: The state of the current item.
            formatting: The formatting of the text.
        """  # pylint: disable=too-many-arguments,too-many-positional-arguments
        if self.current_paragraph is None:
            raise RuntimeError('No current paragraph to write URL into')
        if not text:
            text = url
        self._add_hyperlink(self.current_paragraph, url, text, formatting)

    def _add_hyperlink(self, paragraph: Paragraph, url: str,
                       text: str, formatting: Formatting) -> None:
        """Add a clickable hyperlink to a paragraph.

        Args:
            paragraph: The paragraph to add the hyperlink to.
            url: The URL for the hyperlink.
            text: The display text for the hyperlink.
            formatting: The formatting (bold/italic) for the text.
        """
        # Create relationship for the hyperlink
        # The relationship type for external hyperlinks
        rel_type = ('http://schemas.openxmlformats.org/officeDocument/'
                    '2006/relationships/hyperlink')
        r_id = self.doc.part.relate_to(url, rel_type, is_external=True)
        # Create hyperlink element
        hyperlink = OxmlElement('w:hyperlink')
        hyperlink.set(qn('r:id'), r_id)
        # Create run inside hyperlink
        run_element = OxmlElement('w:r')
        run_props = OxmlElement('w:rPr')
        # Add blue color for link appearance
        color = OxmlElement('w:color')
        color.set(qn('w:val'), '0000FF')
        run_props.append(color)
        # Add underline for link appearance
        underline = OxmlElement('w:u')
        underline.set(qn('w:val'), 'single')
        run_props.append(underline)
        # Add bold if requested
        if formatting.bold:
            bold = OxmlElement('w:b')
            run_props.append(bold)
        # Add italic if requested
        if formatting.italic:
            italic = OxmlElement('w:i')
            run_props.append(italic)
        run_element.append(run_props)
        # Add text element
        text_element = OxmlElement('w:t')
        text_element.text = text
        run_element.append(text_element)
        hyperlink.append(run_element)
        # Append hyperlink to paragraph
        # pylint: disable=protected-access
        paragraph._p.append(hyperlink)

    def _start_bullet_list(self, level: int) -> None:
        """Start a bullet list.

        Args:
            level: The level of the bullet list (1-9).
        """
        assert isinstance(level, int)
        # In python-docx, lists are created by setting paragraph styles
        # No explicit list start/end is needed

    def _end_bullet_list(self, level: int) -> None:
        """End a bullet list.

        Args:
            level: The level of the bullet list (1-9).
        """
        assert isinstance(level, int)
        # In python-docx, lists are created by setting paragraph styles
        # No explicit list start/end is needed

    def _start_bullet_item(self, level: int) -> None:
        """Start a bullet item.

        Args:
            level: The level of the bullet item (1-9).
        """
        assert isinstance(level, int)
        self.current_paragraph = self.doc.add_paragraph(style='List Bullet')
        # Set the indentation level for nested lists
        if level > 1:
            self.current_paragraph.paragraph_format.left_indent = \
                Inches(0.5 * (level - 1))

    def _end_bullet_item(self, level: int) -> None:
        """End a bullet item.

        Args:
            level: The level of the bullet item (1-9).
        """
        assert isinstance(level, int)
        self.current_paragraph = None

    def _start_numbered_list(self, level: int) -> None:
        """Start a numbered list.

        Args:
            level: The level of the numbered list (1-9).
        """
        assert isinstance(level, int)
        # In python-docx, lists are created by setting paragraph styles
        # No explicit list start/end is needed

    def _end_numbered_list(self, level: int) -> None:
        """End a numbered list.

        Args:
            level: The level of the numbered list (1-9).
        """
        assert isinstance(level, int)
        # In python-docx, lists are created by setting paragraph styles
        # No explicit list start/end is needed

    def _start_numbered_item(self, level: int, num: int,
                             full_number: str) -> None:
        """Start a numbered item.

        Args:
            level: The level of the numbered item (1-9).
            num: The number of the item.
            full_number: The full number of the item including all levels.
        """
        assert isinstance(level, int)
        assert isinstance(num, int)
        assert isinstance(full_number, str)
        # Use regular paragraph with manual numbering for hierarchical numbers
        # The 'List Number' style only supports simple sequential numbering
        self.current_paragraph = self.doc.add_paragraph()
        # Set up hanging indent with tab stop for proper text alignment
        # Using twips: 720 twips = 0.5 inches
        number_width_twips = 720  # Space reserved for the number
        base_indent_twips = 720 * (level - 1)  # Additional indent per level
        text_position_twips = base_indent_twips + number_width_twips
        self.current_paragraph.paragraph_format.left_indent = \
            Twips(text_position_twips)
        self.current_paragraph.paragraph_format.first_line_indent = \
            Twips(-number_width_twips)
        # Add tab stop at text position so text after number aligns with
        # wrapped lines (both start at the same position)
        self._add_tab_stop(self.current_paragraph, text_position_twips)
        # Add the hierarchical number followed by tab (not space)
        self.current_paragraph.add_run(full_number)
        self.current_paragraph.add_run('\t')

    @staticmethod
    def _add_tab_stop(paragraph: Paragraph, position_twips: int) -> None:
        """Add a left-aligned tab stop to a paragraph.

        Args:
            paragraph: The paragraph to add the tab stop to.
            position_twips: The position of the tab stop in twips.
        """
        # pylint: disable=protected-access
        p_pr = paragraph._p.get_or_add_pPr()
        tabs = OxmlElement('w:tabs')
        tab = OxmlElement('w:tab')
        tab.set(qn('w:val'), 'left')
        tab.set(qn('w:pos'), str(position_twips))
        tabs.append(tab)
        p_pr.append(tabs)

    def _end_numbered_item(self, level: int, num: int) -> None:
        """End a numbered item.

        Args:
            level: The level of the numbered item (1-9).
            num: The number of the item.
        """
        assert isinstance(level, int)
        assert isinstance(num, int)
        self.current_paragraph = None

    def _start_table(self, num_columns: int) -> None:
        """Start a table.

        Args:
            num_columns: The number of columns in the table.
        """
        assert isinstance(num_columns, int)
        # Add an empty paragraph before the table for spacing
        # This separates the table from previous content
        self.doc.add_paragraph()
        # Note: Actual table creation happens in _write_table_first_row

    def _end_table(self, num_columns: int, num_rows: int) -> None:
        """End a table.

        Args:
            num_columns: The number of columns in the table.
            num_rows: The number of rows in the table.
        """
        assert isinstance(num_columns, int)
        assert isinstance(num_rows, int)
        # Add an empty paragraph after the table for spacing
        self.doc.add_paragraph()

    def _write_table_first_row(self, first_row: list[str],
                               formatting: Formatting) -> None:
        """Write the first row of a table.

        Args:
            first_row: The first row of the table.
            formatting: The formatting of the text in each cell.
        """
        assert isinstance(first_row, list)
        assert isinstance(formatting, Formatting)
        # Create the table with the first row
        table = self.doc.add_table(rows=1, cols=len(first_row))
        table.style = 'Table Grid'
        # Fill in the first row
        for idx, cell_text in enumerate(first_row):
            cell = table.rows[0].cells[idx]
            para = cell.paragraphs[0]
            run = para.add_run(cell_text)
            if formatting.bold:
                run.bold = True
            if formatting.italic:
                run.italic = True

    def _write_table_row(self, row: list[str], formatting: Formatting,
                         row_number: int) -> None:
        """Write a row of a table.

        Args:
            row: The row to add to the table.
            formatting: The formatting of the text in each cell.
            row_number: The row number (0-based).
        """
        assert isinstance(row, list)
        assert isinstance(formatting, Formatting)
        assert isinstance(row_number, int)
        # Get the last table in the document
        table = self.doc.tables[-1]
        # Add a new row
        new_row = table.add_row()  # type: ignore[no-untyped-call]
        # Fill in the row
        for idx, cell_text in enumerate(row):
            cell = new_row.cells[idx]
            para = cell.paragraphs[0]
            run = para.add_run(cell_text)
            if formatting.bold:
                run.bold = True
            if formatting.italic:
                run.italic = True

    def _start_code_block(self, programming_language: Optional[str]) -> None:
        """Start a code block.

        Args:
            programming_language: The programming language of the code block.
        """
        assert programming_language is None or \
            isinstance(programming_language, str)
        # Create a paragraph with a code/verbatim style
        # python-docx doesn't have a built-in code style,
        # so we'll use 'No Spacing' style and monospace font
        self.current_paragraph = self.doc.add_paragraph()
        self.current_paragraph.style = 'No Spacing'

    def _end_code_block(self, programming_language: Optional[str]) -> None:
        """End a code block.

        Args:
            programming_language: The programming language of the code block.
        """
        assert programming_language is None or \
            isinstance(programming_language, str)
        self.current_paragraph = None

    def _write_code_block(self, text: str,
                          programming_language: Optional[str]) -> None:
        """Write a code block.

        Args:
            text: The text to add to the code block.
            programming_language: The programming language of the code block.
        """
        assert isinstance(text, str)
        assert programming_language is None or \
            isinstance(programming_language, str)
        if self.current_paragraph is None:
            raise RuntimeError('No current paragraph to write code into')
        run = self.current_paragraph.add_run(text)
        # Set monospace font
        run.font.name = 'Courier New'

    def _encode_text(self, text: str) -> str:
        """Encode text (escape special characters)."""
        # No encoding needed for DOCX
        return text
