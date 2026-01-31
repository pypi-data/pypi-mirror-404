"""AutosarClass parser for extracting AUTOSAR class definitions from PDF files.

This module provides the specialized parser for AutosarClass definitions,
including attribute parsing, base class handling, and multi-page support.

Requirements:
    SWR_PARSER_00004: Class Definition Pattern Recognition
    SWR_PARSER_00010: Attribute Extraction from PDF
    SWR_PARSER_00011: Attribute Metadata Filtering
    SWR_PARSER_00012: Multi-Line Attribute Handling
    SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass
    SWR_PARSER_00024: AutosarClass Specialized Parser
    SWR_PARSER_00028: Direct Model Creation by Specialized Parsers
"""

import re
from typing import Any, Dict, List, Match, Optional, Tuple

from autosar_pdf2txt.models import (
    AttributeKind,
    AutosarClass,
)
from autosar_pdf2txt.parser.base_parser import AbstractTypeParser, AutosarType


class AutosarClassParser(AbstractTypeParser):
    """Specialized parser for AutosarClass definitions.

    This parser handles the parsing of AUTOSAR class definitions from PDF files,
    including:
    - Class definition pattern recognition with ATP markers
    - Attribute extraction with multi-line support
    - Base class parsing
    - Subclass parsing
    - Aggregated by parsing
    - Note parsing
    - State management across multiple pages

    Requirements:
        SWR_PARSER_00024: AutosarClass Specialized Parser
        SWR_PARSER_00028: Direct Model Creation by Specialized Parsers
    """

    def __init__(self) -> None:
        """Initialize the AutosarClass parser.

        Requirements:
            SWR_PARSER_00024: AutosarClass Specialized Parser
        """
        super().__init__()
        # Parsing state
        self._in_attribute_section: bool = False
        self._pending_attr_name: Optional[str] = None
        self._pending_attr_type: Optional[str] = None
        self._pending_attr_multiplicity: Optional[str] = None
        self._pending_attr_kind: Optional[AttributeKind] = None
        self._pending_attr_note: Optional[str] = None
        # Class list state (Base, Subclasses, Aggregated by)
        self._pending_class_lists: Dict[str, Tuple[Optional[List[str]], Optional[str], bool]] = {
            "base_classes": (None, None, True),
            "aggregated_by": (None, None, True),
            "subclasses": (None, None, True),
        }
        self._in_class_list_section: Optional[str] = None

    def _reset_state(self) -> None:
        """Reset parser state for a new class definition.

        This method clears all state variables to ensure clean parsing
        of each new class definition without interference from previous classes.

        Requirements:
            SWR_PARSER_00024: AutosarClass Specialized Parser
        """
        self._in_attribute_section = False
        self._pending_attr_name = None
        self._pending_attr_type = None
        self._pending_attr_multiplicity = None
        self._pending_attr_kind = None
        self._pending_attr_note = None
        self._pending_class_lists = {
            "base_classes": (None, None, True),
            "aggregated_by": (None, None, True),
            "subclasses": (None, None, True),
        }
        self._in_class_list_section = None

    def parse_definition(
        self,
        lines: List[str],
        line_index: int,
        pdf_filename: Optional[str] = None,
        page_number: Optional[int] = None,
        autosar_standard: Optional[str] = None,
        standard_release: Optional[str] = None,
    ) -> Optional[AutosarClass]:
        """Parse a class definition from PDF lines.

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
            The parsed AutosarClass object, or None if parsing failed.
        """
        if line_index >= len(lines):
            return None

        line = lines[line_index].strip()
        class_match = self.CLASS_PATTERN.match(line)

        if not class_match:
            return None

        # Extract class name and abstract status
        raw_class_name = class_match.group(1).strip()
        is_abstract = class_match.group(2) is not None

        # Validate ATP markers and get clean name
        atp_type, class_name = self._validate_atp_markers(raw_class_name)

        # Check if class name starts with "Abstract" (AUTOSAR naming convention)
        if not is_abstract and class_name.startswith("Abstract"):
            is_abstract = True

        # Check if this is a valid class definition (followed by package path)
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

        # Create AutosarClass directly (no intermediate ClassDefinition)
        return AutosarClass(
            name=class_name,
            package=package_path,
            is_abstract=is_abstract,
            atp_type=atp_type,
            sources=[source] if source else [],
        )

    def continue_parsing(
        self,
        current_model: AutosarType,
        lines: List[str],
        line_index: int,
    ) -> Tuple[int, bool]:
        """Continue parsing a class definition from subsequent lines.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF
            SWR_PARSER_00011: Attribute Metadata Filtering
            SWR_PARSER_00012: Multi-Line Attribute Handling
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            current_model: The current AutosarClass being parsed.
            lines: List of text lines from the PDF.
            line_index: Current line index in the lines list.

        Returns:
            Tuple of (new_line_index, is_complete) where:
            - new_line_index: The line index to continue from
            - is_complete: True if parsing is complete, False if more lines needed
        """
        # Type narrowing: current_model is always AutosarClass for this parser
        assert isinstance(current_model, AutosarClass)
        i = line_index
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Check for attribute header
            attr_header_match = self.ATTRIBUTE_HEADER_PATTERN.match(line)
            if attr_header_match:
                self._finalize_pending_class_lists(current_model)
                self._in_attribute_section = True
                self._in_class_list_section = None
                i += 1
                continue

            # Check for class list patterns (Base, Subclasses, Aggregated by)
            class_list_match = self._try_match_class_list_pattern(line)
            if class_list_match:
                section_name, match = class_list_match
                self._finalize_pending_class_lists(current_model)
                items, last_item, last_item_complete = self._parse_class_list_line(match)
                self._pending_class_lists[section_name] = (items, last_item, last_item_complete)
                self._in_class_list_section = section_name
                i += 1
                continue

            # Process class list continuation AFTER class list patterns but BEFORE other sections
            # This ensures that multi-line class lists are processed before sections like note/new class
            if self._in_class_list_section and current_model:
                line_stripped = line.strip()
                # Skip class definition headers that appear on new pages (multi-page class definitions)
                # These look like "Class ClassName (abstract)" and should NOT be treated as continuations
                if self._is_new_type_definition(line_stripped):
                    # This is a repeated class header on a new page - skip it
                    i += 1
                    continue
                if line_stripped and ("," in line_stripped or any(fragment in line_stripped for fragment in self.CONTINUATION_FRAGMENTS)):
                    (items, last_item), last_item_complete = self._handle_class_list_continuation(
                        line_stripped,
                        self._pending_class_lists[self._in_class_list_section][0],
                        self._pending_class_lists[self._in_class_list_section][1],
                        self._pending_class_lists[self._in_class_list_section][2] if len(self._pending_class_lists[self._in_class_list_section]) > 2 else True,
                    )
                    self._pending_class_lists[self._in_class_list_section] = (items, last_item, last_item_complete)
                    i += 1
                    continue

            # Check for note
            note_match = self.NOTE_PATTERN.match(line)
            if note_match:
                self._finalize_pending_class_lists(current_model)
                self._in_class_list_section = None
                i = self._process_note_line(note_match, lines, i, current_model)
                continue

            # Check for new class/primitive/enumeration definition
            if self._is_new_type_definition(line):
                # Check if this is a valid new type definition
                # A valid type definition must be followed by a Package line
                # If not, it's likely a continuation header (e.g., multi-page table)
                is_valid_new_definition = self._is_valid_type_definition(lines, i)

                if is_valid_new_definition:
                    # New type definition - finalize and return
                    self._finalize_pending_class_lists(current_model)
                    self._finalize_pending_attribute(current_model)
                    return i, True
                else:
                    # Not a valid new definition - continue parsing current model
                    # This handles multi-page tables where the class name is repeated
                    i += 1
                    continue

            # Check for table or enumeration (end of class)
            if self._is_table_marker(line) or line.startswith("Enumeration "):
                self._finalize_pending_class_lists(current_model)
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

            i += 1

        # End of lines - finalize and return
        self._finalize_pending_class_lists(current_model)
        self._finalize_pending_attribute(current_model)
        
        # Only mark as complete if we're not in the attribute section
        # If we're in the attribute section, we might have more attributes on the next page
        # This handles multi-page class definitions where attributes span multiple pages
        if self._in_attribute_section:
            # Still in attribute section - continue parsing on next page
            return i, False
        else:
            # Not in attribute section - mark as complete
            return i, True

    def _try_match_class_list_pattern(self, line: str) -> Optional[Tuple[str, re.Match]]:
        """Try to match class list patterns (Base, Subclasses, Aggregated by).

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            line: The line to match.

        Returns:
            Tuple of (section_name, match) or None if no match.
        """
        base_match = self.BASE_PATTERN.match(line)
        if base_match:
            return ("base_classes", base_match)

        subclass_match = self.SUBCLASS_PATTERN.match(line)
        if subclass_match:
            return ("subclasses", subclass_match)

        aggregated_match = self.AGGREGATED_BY_PATTERN.match(line)
        if aggregated_match:
            return ("aggregated_by", aggregated_match)

        return None

    def _parse_class_list_line(self, match: re.Match) -> Tuple[Optional[List[str]], Optional[str], bool]:
        """Parse a class list line (Base, Subclasses, Aggregated by).

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            match: The regex match object.

        Returns:
            Tuple of (list_items, last_item, last_item_complete).
            last_item_complete is True if the last item ended with a comma (complete),
            False if it didn't end with a comma (incomplete, continuation expected).
        """
        items_str = match.group(1)
        # Filter out empty strings that can occur when lines end with commas
        items = [item.strip() for item in items_str.split(",") if item.strip()]
        last_item = items[-1] if items else None
        # Check if the original string ended with a comma (indicates complete item)
        last_item_complete = items_str.rstrip().endswith(",")
        return items, last_item, last_item_complete

    def _handle_class_list_continuation(
        self, line: str, current_items: Optional[List[str]], last_item: Optional[str], last_item_complete: bool = True
    ) -> Tuple[Tuple[Optional[List[str]], Optional[str]], bool]:
        """Handle continuation of class list (multi-line Base, Subclasses, Aggregated by).

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            line: The continuation line.
            current_items: Current list of items.
            last_item: The last item from previous line.
            last_item_complete: True if the last item ended with a comma (complete),
                               False if it didn't end with a comma (incomplete).

        Returns:
            Tuple of ((updated_items, updated_last_item), last_item_complete).
        """
        if current_items is None:
            current_items = []

        parts = [part.strip() for part in line.split(",") if part.strip()]

        if not parts:
            return (current_items, last_item), last_item_complete

        # Check if the first part should be appended to the last item
        # Only concatenate if the last item was incomplete (didn't end with comma)
        # However, if the line starts with a comma, it's a new item (comma at start means previous item was complete)
        # Also, if the first part is a complete class name (not a fragment),
        # it's likely a new item (comma missing due to PDF text extraction error)
        if last_item is not None and parts and not last_item_complete:
            first_part = parts[0]

            # Check if line starts with a comma - if so, it's a new item
            line_starts_with_comma = line.lstrip().startswith(",")

            # Heuristic: if first part is a complete class name (not a fragment),
            # it's likely a new item (comma missing due to PDF text extraction error)
            # A complete class name typically has a recognizable pattern
            common_class_patterns = {
                "Timing", "Tcp", "Tls", "Tlv", "Transformation", "Unit", "Uploadable",
                "Value", "Variant", "View", "System", "Someip"
            }

            should_concatenate = True
            if first_part:
                # If line starts with comma, it's a new item
                if line_starts_with_comma:
                    should_concatenate = False
                else:
                    # Check if first part is a complete class name
                    # (starts with a common pattern and has reasonable length)
                    for pattern in common_class_patterns:
                        if first_part == pattern or first_part.startswith(pattern + "Config") or first_part.startswith(pattern + "Extension"):
                            should_concatenate = False
                            break

            if should_concatenate:
                combined_name = last_item + first_part
                current_items[-1] = combined_name
                parts = parts[1:]

        # Add remaining parts as new items
        for part in parts:
            if part:
                current_items.append(part)

        new_last_item = current_items[-1] if current_items else None
        # Check if the current line ended with a comma
        new_last_item_complete = line.rstrip().endswith(",")
        return (current_items, new_last_item), new_last_item_complete

    def _finalize_pending_class_lists(self, current_model: AutosarClass) -> None:
        """Finalize pending class lists and add to model.

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            current_model: The current AutosarClass being parsed.
        """
        for section_name, (items, _, _) in self._pending_class_lists.items():
            if items:
                if section_name == "base_classes":
                    # Split into regular bases and Atp interfaces
                    regular_bases = [item for item in items if not item.startswith("Atp")]
                    interfaces = [item for item in items if item.startswith("Atp")]
                    current_model.bases.extend(regular_bases)
                    current_model.implements.extend(interfaces)
                elif section_name == "subclasses":
                    current_model.subclasses.extend(items)
                elif section_name == "aggregated_by":
                    current_model.aggregated_by.extend(items)
            # Reset
            self._pending_class_lists[section_name] = (None, None, True)

    def _process_note_line(
        self, note_match: Match, lines: List[str], line_index: int, current_model: AutosarClass
    ) -> int:
        """Process a note line and extract multi-line note text.

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            note_match: The regex match object.
            lines: List of text lines from the PDF.
            line_index: Current line index.
            current_model: The current AutosarClass being parsed.

        Returns:
            The line index after processing the note (may have consumed multiple lines).
        """
        note_text = self._extract_note_text(note_match, lines, line_index, parser_type="class")
        current_model.note = note_text

        # Find where the note ended
        i = line_index + 1
        while i < len(lines):
            next_line = lines[i].strip()
            if self._is_note_continuation(next_line, parser_type="class"):
                i += 1
            else:
                break

        return i

    def _process_attribute_line(
        self,
        line: str,
        current_model: AutosarClass,
        pending_attr_name: Optional[str],
        pending_attr_type: Optional[str],
        pending_attr_multiplicity: Optional[str],
        pending_attr_kind: Optional[AttributeKind],
        pending_attr_note: Optional[str],
    ) -> Dict[str, Any]:
        """Process an attribute line.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF
            SWR_PARSER_00011: Attribute Metadata Filtering
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            line: The attribute line.
            current_model: The current AutosarClass being parsed.
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
            # - Third word as multiplicity (0..1, *, 0..*) or kind (attr, aggr, ref)
            third_word = words[2] if len(words) > 2 else ""
            fourth_word = words[3] if len(words) > 3 else ""

            is_new_attribute = (
                # Third word is multiplicity or kind
                third_word in (self.MULTIPLICITIES | self.ATTR_KINDS_ALL) or
                # Fourth word is kind (for lines like "dynamicArray String 0..1 attr")
                fourth_word in (self.ATTR_KINDS_ATTR | self.ATTR_KINDS_AGGR | self.ATTR_KINDS_REF)
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
                multiplicity, kind, note = self._extract_attribute_parts(words, supports_ref=True)

                result["pending_attr_multiplicity"] = multiplicity
                result["pending_attr_kind"] = kind
                result["pending_attr_note"] = note
            elif pending_attr_name is not None and pending_attr_type is not None:
                # This is a continuation line for the pending attribute
                continuation_result = self._handle_attribute_continuation(
                    words, pending_attr_name, pending_attr_note
                )
                result.update(continuation_result)

        return result

    def _finalize_pending_attribute(self, current_model: AutosarClass) -> None:
        """Finalize a pending attribute and add it to the current class if valid.

        Requirements:
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            current_model: The current AutosarClass being parsed.
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