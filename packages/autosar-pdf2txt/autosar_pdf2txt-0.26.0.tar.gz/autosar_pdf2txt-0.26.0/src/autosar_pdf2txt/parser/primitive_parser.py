"""AutosarPrimitive parser for extracting AUTOSAR primitive definitions from PDF files.

This module provides the specialized parser for AutosarPrimitive definitions.

Requirements:
    SWR_PARSER_00004: Class Definition Pattern Recognition
    SWR_PARSER_00013: Recognition of Primitive and Enumeration Class Definition Patterns
    SWR_PARSER_00024: AUTOSAR Primitive Type Representation
    SWR_PARSER_00026: AutosarPrimitive Specialized Parser
    SWR_PARSER_00028: Direct Model Creation by Specialized Parsers
"""

from typing import Any, Dict, List, Match, Optional, Tuple

from autosar_pdf2txt.models import (
    AttributeKind,
    AutosarPrimitive,
)
from autosar_pdf2txt.parser.base_parser import AbstractTypeParser, AutosarType


class AutosarPrimitiveParser(AbstractTypeParser):
    """Specialized parser for AutosarPrimitive definitions.

    This parser handles the parsing of AUTOSAR primitive definitions from PDF files,
    including:
    - Primitive definition pattern recognition
    - Attribute parsing (simplified version)
    - Note parsing
    - State management across multiple pages

    Requirements:
        SWR_PARSER_00026: AutosarPrimitive Specialized Parser
        SWR_PARSER_00028: Direct Model Creation by Specialized Parsers
    """

    def __init__(self) -> None:
        """Initialize the AutosarPrimitive parser.

        Requirements:
            SWR_PARSER_00026: AutosarPrimitive Specialized Parser
        """
        super().__init__()
        # Parsing state
        self._in_attribute_section: bool = False
        self._pending_attr_name: Optional[str] = None
        self._pending_attr_type: Optional[str] = None
        self._pending_attr_multiplicity: Optional[str] = None
        self._pending_attr_kind: Optional[AttributeKind] = None
        self._pending_attr_note: Optional[str] = None

    def _reset_state(self) -> None:
        """Reset parser state for a new primitive definition.

        This method clears all state variables to ensure clean parsing
        of each new primitive definition without interference from previous primitives.

        Requirements:
            SWR_PARSER_00026: AutosarPrimitive Specialized Parser
        """
        self._in_attribute_section = False
        self._pending_attr_name = None
        self._pending_attr_type = None
        self._pending_attr_multiplicity = None
        self._pending_attr_kind = None
        self._pending_attr_note = None

    def parse_definition(
        self,
        lines: List[str],
        line_index: int,
        pdf_filename: Optional[str] = None,
        page_number: Optional[int] = None,
        autosar_standard: Optional[str] = None,
        standard_release: Optional[str] = None,
    ) -> Optional[AutosarPrimitive]:
        """Parse a primitive definition from PDF lines.

        Requirements:
            SWR_PARSER_00004: Class Definition Pattern Recognition
            SWR_PARSER_00013: Recognition of Primitive and Enumeration Class Definition Patterns
            SWR_MODEL_00027: AUTOSAR Source Location Representation
            SWR_PARSER_00022: PDF Source Location Extraction

        Args:
            lines: List of text lines from the PDF.
            line_index: Current line index in the lines list.
            pdf_filename: Optional PDF filename for source tracking.
            page_number: Optional page number for source tracking.
            autosar_standard: Optional AUTOSAR standard identifier for source tracking.
            standard_release: Optional AUTOSAR standard release for source tracking.

        Returns:
            The parsed AutosarPrimitive object, or None if parsing failed.
        """
        if line_index >= len(lines):
            return None

        line = lines[line_index].strip()
        primitive_match = self.PRIMITIVE_PATTERN.match(line)

        if not primitive_match:
            return None

        # Extract primitive name
        raw_primitive_name = primitive_match.group(1).strip()

        # Validate ATP markers and get clean name (primitives don't have ATP markers)
        atp_type, primitive_name = self._validate_atp_markers(raw_primitive_name)

        # Check if this is a valid primitive definition (followed by package path)
        if not self._is_valid_type_definition(lines, line_index):
            return None

        # Extract package path
        package_path = self._extract_package_path(lines, line_index)
        if not package_path:
            return None

        # Create source location
        source = self._create_source_location(
            pdf_filename, page_number, autosar_standard, standard_release
        )

        # Create AutosarPrimitive directly (no intermediate ClassDefinition)
        return AutosarPrimitive(
            name=primitive_name,
            package=package_path,
            sources=[source] if source else [],
        )

    def continue_parsing(
        self,
        current_model: AutosarType,
        lines: List[str],
        line_index: int,
    ) -> Tuple[int, bool]:
        """Continue parsing a primitive definition from subsequent lines.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF
            SWR_PARSER_00011: Attribute Metadata Filtering
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            current_model: The current AutosarPrimitive being parsed.
            lines: List of text lines from the PDF.
            line_index: Current line index in the lines list.

        Returns:
            Tuple of (new_line_index, is_complete) where:
            - new_line_index: The line index to continue from
            - is_complete: True if parsing is complete, False if more lines needed
        """
        # Type narrowing: current_model is always AutosarPrimitive for this parser
        assert isinstance(current_model, AutosarPrimitive)
        i = line_index
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Check for attribute header
            attr_header_match = self.ATTRIBUTE_HEADER_PATTERN.match(line)
            if attr_header_match:
                self._in_attribute_section = True
                i += 1
                continue

            # Check for new class/primitive/enumeration definition
            if self._is_new_type_definition(line):
                # New type definition - finalize and return
                self._finalize_pending_attribute(current_model)
                return i, True

            # Check for table (end of primitive)
            if self._is_table_marker(line):
                self._finalize_pending_attribute(current_model)
                return i, True

            # Process attribute section
            if self._in_attribute_section and line and " " in line:
                attr_result = self._process_attribute_line(
                    line, current_model,
                    self._pending_attr_name,
                    self._pending_attr_type,
                    self._pending_attr_multiplicity,
                    self._pending_attr_kind,
                    self._pending_attr_note,
                )
                if attr_result["section_ended"]:
                    self._in_attribute_section = False
                self._pending_attr_name = attr_result["pending_attr_name"]
                self._pending_attr_type = attr_result["pending_attr_type"]
                self._pending_attr_multiplicity = attr_result["pending_attr_multiplicity"]
                self._pending_attr_kind = attr_result["pending_attr_kind"]
                self._pending_attr_note = attr_result["pending_attr_note"]
                i += 1
                continue

            # Check for note
            note_match = self.NOTE_PATTERN.match(line)
            if note_match:
                self._process_note_line(note_match, lines, i, current_model)
                i += 1
                continue

            i += 1

        # End of lines - finalize and return
        self._finalize_pending_attribute(current_model)
        return i, True

    def _process_attribute_line(
        self,
        line: str,
        current_model: AutosarPrimitive,
        pending_attr_name: Optional[str],
        pending_attr_type: Optional[str],
        pending_attr_multiplicity: Optional[str],
        pending_attr_kind: Optional[AttributeKind],
        pending_attr_note: Optional[str],
    ) -> Dict[str, Any]:
        """Process an attribute line (simplified version for primitives).

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF
            SWR_PARSER_00011: Attribute Metadata Filtering
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            line: The attribute line.
            current_model: The current AutosarPrimitive being parsed.
            pending_attr_name: Pending attribute name.
            pending_attr_type: Pending attribute type.
            pending_attr_multiplicity: Pending attribute multiplicity.
            pending_attr_kind: Pending attribute kind.
            pending_attr_note: Pending attribute note.

        Returns:
            Dictionary with updated state and section_ended flag.
        """
        result = {
            "pending_attr_name": pending_attr_name,
            "pending_attr_type": pending_attr_type,
            "pending_attr_multiplicity": pending_attr_multiplicity,
            "pending_attr_kind": pending_attr_kind,
            "pending_attr_note": pending_attr_note,
            "section_ended": False,
        }

        # Check if this line ends the attribute section
        if self._is_table_marker(line) or line.startswith("Enumeration "):
            self._add_attribute_if_valid(
                current_model.attributes,
                pending_attr_name, pending_attr_type,
                pending_attr_multiplicity, pending_attr_kind, pending_attr_note
            )
            result["section_ended"] = True
            result["pending_attr_name"] = None
            result["pending_attr_type"] = None
            result["pending_attr_multiplicity"] = None
            result["pending_attr_kind"] = None
            result["pending_attr_note"] = None
            return result

        # This might be an attribute line or continuation
        attr_match = self.ATTRIBUTE_PATTERN.match(line)
        if attr_match:
            # This is a potential attribute line
            attr_name = attr_match.group(1)
            attr_type = attr_match.group(2)
            words = line.split()

            # A real attribute line should have:
            # - Third word as multiplicity (0..1, *, 0..*) or kind (attr, aggr)
            third_word = words[2] if len(words) > 2 else ""
            fourth_word = words[3] if len(words) > 3 else ""

            valid_third = self.MULTIPLICITIES | self.ATTR_KINDS_ATTR | self.ATTR_KINDS_AGGR
            valid_fourth = self.ATTR_KINDS_ATTR | self.ATTR_KINDS_AGGR

            is_new_attribute = (
                # Third word is multiplicity or kind
                third_word in valid_third or
                # Fourth word is kind (for lines like "dynamicArray String 0..1 attr")
                fourth_word in valid_fourth
            )

            if is_new_attribute:
                # This is a new attribute line with proper structure
                # Finalize any pending attribute first
                self._add_attribute_if_valid(
                    current_model.attributes,
                    pending_attr_name, pending_attr_type,
                    pending_attr_multiplicity, pending_attr_kind, pending_attr_note
                )

                # Save as pending (might be a multi-line attribute)
                result["pending_attr_name"] = attr_name
                result["pending_attr_type"] = attr_type

                # Extract multiplicity, kind, and note from the attribute line
                multiplicity, kind, note = self._extract_attribute_parts(words, supports_ref=False)

                result["pending_attr_multiplicity"] = multiplicity
                result["pending_attr_kind"] = kind
                result["pending_attr_note"] = note
            elif pending_attr_name is not None and pending_attr_type is not None:
                # This is a continuation line for the pending attribute
                continuation_result = self._handle_attribute_continuation(
                    words, pending_attr_name, pending_attr_note,
                    valid_third_words=valid_third
                )
                result.update(continuation_result)

        return result

    def _finalize_pending_attribute(self, current_model: AutosarPrimitive) -> None:
        """Finalize a pending attribute and add it to the current primitive if valid.

        Requirements:
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            current_model: The current AutosarPrimitive being parsed.
        """
        self._add_attribute_if_valid(
            current_model.attributes,
            self._pending_attr_name,
            self._pending_attr_type,
            self._pending_attr_multiplicity,
            self._pending_attr_kind,
            self._pending_attr_note,
        )
        # Reset
        self._pending_attr_name = None
        self._pending_attr_type = None
        self._pending_attr_multiplicity = None
        self._pending_attr_kind = None
        self._pending_attr_note = None

    def _process_note_line(
        self, note_match: Match, lines: List[str], line_index: int, current_model: AutosarPrimitive
    ) -> None:
        """Process a note line and extract multi-line note text.

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            note_match: The regex match object.
            lines: List of text lines from the PDF.
            line_index: Current line index.
            current_model: The current AutosarPrimitive being parsed.
        """
        note_text = self._extract_note_text(note_match, lines, line_index, parser_type="primitive")
        current_model.note = note_text