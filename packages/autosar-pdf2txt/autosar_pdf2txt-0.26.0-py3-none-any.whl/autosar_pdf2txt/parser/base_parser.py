"""Abstract base parser for AUTOSAR type parsing.

This module provides the abstract base class and common functionality
for parsing AUTOSAR types from PDF files.

Requirements:
    SWR_PARSER_00001: PDF Parser Initialization
    SWR_PARSER_00003: PDF File Parsing
    SWR_PARSER_00005: Class Definition Data Model
    SWR_PARSER_00010: Attribute Extraction from PDF
    SWR_PARSER_00023: Abstract Base Parser for Common Functionality
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, List, Match, Optional, Tuple, Union

from autosar_pdf2txt.models import (
    ATPType,
    AttributeKind,
    AutosarAttribute,
    AutosarClass,
    AutosarDocumentSource,
    AutosarEnumeration,
    AutosarPrimitive,
)

# Type alias for any AUTOSAR type
AutosarType = Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]


class AbstractTypeParser(ABC):
    """Abstract base parser for AUTOSAR types.

    This class provides common parsing functionality for all AUTOSAR type
    parsers, including:
    - Common regex patterns
    - Attribute validation and filtering logic
    - Package path validation
    - ATP marker validation
    - Source location tracking

    Requirements:
        SWR_PARSER_00023: Abstract Base Parser for Common Functionality
    """

    # Regex patterns for parsing class definitions
    # SWR_PARSER_00004: Class Definition Pattern Recognition
    # SWR_PARSER_00013: Recognition of Primitive and Enumeration Class Definition Patterns
    # SWR_PARSER_00010: Attribute Extraction from PDF
    # SWR_PARSER_00012: Multi-Line Attribute Handling
    # SWR_PARSER_00014: Enumeration Literal Header Recognition
    # SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass
    CLASS_PATTERN = re.compile(r"^Class\s+(.+?)(?:\s*\((abstract)\))?\s*$")
    PRIMITIVE_PATTERN = re.compile(r"^Primitive\s+(.+)$")
    ENUMERATION_PATTERN = re.compile(r"^Enumeration\s+(.+)$")
    PACKAGE_PATTERN = re.compile(r"^Package\s+(M2::)?(.+)$")
    BASE_PATTERN = re.compile(r"^Base\s+(.+)$")
    SUBCLASS_PATTERN = re.compile(r"^Subclasses\s+(.+)$")
    AGGREGATED_BY_PATTERN = re.compile(r"^Aggregated\s+by\s+(.+)$")
    NOTE_PATTERN = re.compile(r"^Note\s+(.+)$")
    ATTRIBUTE_HEADER_PATTERN = re.compile(r"^Attribute\s+Type\s+Mult\.\s+Kind\s+Note$")
    ENUMERATION_LITERAL_HEADER_PATTERN = re.compile(r"^Literal\s+Description$")
    ENUMERATION_LITERAL_PATTERN = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)(?:\s+(.*))?$")
    ATTRIBUTE_PATTERN = re.compile(r"^(\S+)\s+(\S+)\s+.*$")
    ATP_MIXED_STRING_PATTERN = re.compile(r"<<atpMixedString>>")
    ATP_VARIATION_PATTERN = re.compile(r"<<atpVariation>>")
    ATP_MIXED_PATTERN = re.compile(r"<<atpMixed>>")
    ATP_PROTOTYPE_PATTERN = re.compile(r"<<atpPrototype>>")

    # Class constants for filtering and continuation detection
    # SWR_PARSER_00012: Multi-Line Attribute Handling
    # SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass
    CONTINUATION_TYPES = {"data", "If", "has", "to", "of", "CP", "atpSplitable"}
    FRAGMENT_NAMES = {"Element", "SizeProfile", "intention", "ImplementationDataType"}
    PARTIAL_NAMES = {"isStructWith"}
    CONTINUATION_FRAGMENTS = {"Element", "Referrable", "Packageable", "Type", "Profile"}
    REFERENCE_INDICATORS = {"Prototype", "Ref", "Dependency", "Trigger", "Mapping", "Group", "Set", "List", "Collection"}

    # Attribute kind values for parsing
    ATTR_KINDS_ATTR = {"attr"}
    ATTR_KINDS_AGGR = {"aggr"}
    ATTR_KINDS_REF = {"ref"}
    ATTR_KINDS_ALL = ATTR_KINDS_ATTR | ATTR_KINDS_AGGR | ATTR_KINDS_REF

    # Multiplicity values for parsing
    MULTIPLICITIES = {"0..1", "0..*", "*", "1"}

    def _is_reference_type(self, attr_type: str) -> bool:
        """Determine if an attribute type is a reference type.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF

        Args:
            attr_type: The attribute type string.

        Returns:
            True if the attribute type appears to be a reference type, False otherwise.

        Reference types typically end with common AUTOSAR reference patterns.
        """
        return any(indicator in attr_type for indicator in self.REFERENCE_INDICATORS)

    def _is_broken_attribute_fragment(
        self, attr_name: str, attr_type: str
    ) -> bool:
        """Check if an attribute is a broken fragment from multi-line PDF table formatting.

        Requirements:
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            attr_name: The attribute name.
            attr_type: The attribute type.

        Returns:
            True if this is a broken fragment that should be filtered out, False otherwise.
        """
        return (
            attr_type in self.CONTINUATION_TYPES
            or attr_name in self.FRAGMENT_NAMES
            or attr_name in self.PARTIAL_NAMES
        )

    def _is_valid_package_path(self, package_path: str) -> bool:
        """Check if a package path is valid and should be accepted.

        Requirements:
            SWR_PARSER_00006: Package Hierarchy Building

        Args:
            package_path: The package path to validate (e.g., "M2::AUTOSAR::DataTypes").

        Returns:
            True if the package path is valid, False if it should be filtered out.

        Valid package paths:
        - Start with "M2::" (AUTOSAR meta-model packages)
        - Contain at least two levels (e.g., "AUTOSAR::DataTypes")
        - Single-level paths with proper naming (TitleCase or starts with underscore)
        - Do not contain suspicious patterns that look like descriptive text

        Invalid package paths:
        - Single-level paths with lowercase start (likely descriptive text)
        - Paths with suspicious patterns (e.g., "This is the package for...")
        """
        # Check for suspicious patterns that indicate descriptive text
        # rather than actual package paths
        suspicious_patterns = [
            "the ", " is ", " of ", " for ", " and ", " or ", " a ", " an ",
            "This ", "These ", "The ", "A ", "An ",
        ]
        for pattern in suspicious_patterns:
            if pattern in package_path:
                return False

        # Check for standalone "package", "Package", "template", or "Template" words
        # Use word boundary matching to avoid false positives (e.g., "Some_Package", "Templates")
        if re.search(r"\bpackage\b|\bPackage\b|\btemplate\b|\bTemplate\b", package_path):
            return False

        # Remove M2:: prefix if present for further validation
        test_path = package_path
        if test_path.startswith("M2::"):
            test_path = test_path[4:]

        # Check for empty parts (e.g., "AUTOSAR::" or "::Package")
        if "::" in test_path:
            parts = test_path.split("::")
            if any(not part for part in parts):
                return False

        # Multi-level paths are generally valid if they pass the above checks
        if "::" in test_path:
            return True

        # Single-level paths: only accept if they follow proper naming conventions
        # - Start with underscore (e.g., _PrivatePackage)
        # - TitleCase format (e.g., SomePackage, Some_Package)
        if test_path.startswith("_") or re.match(r"^[A-Z][a-zA-Z0-9]*(_[a-zA-Z0-9]+)*$", test_path):
            return True

        # Single-level paths with lowercase start are likely descriptive text
        return False

    def _validate_atp_markers(self, raw_class_name: str) -> Tuple[ATPType, str]:
        """Validate ATP markers and extract ATP type and clean class name.

        Requirements:
            SWR_PARSER_00004: Class Definition Pattern Recognition

        Args:
            raw_class_name: The raw class name that may contain ATP markers.

        Returns:
            Tuple of (atp_type, clean_class_name).

        Raises:
            ValueError: If multiple ATP markers are detected on the same class.
        """
        # Detect ATP patterns
        atp_mixed_string = self.ATP_MIXED_STRING_PATTERN.search(raw_class_name)
        atp_variation = self.ATP_VARIATION_PATTERN.search(raw_class_name)
        atp_mixed = self.ATP_MIXED_PATTERN.search(raw_class_name)
        atp_prototype = self.ATP_PROTOTYPE_PATTERN.search(raw_class_name)

        atp_markers = [atp_mixed_string, atp_variation, atp_mixed, atp_prototype]
        found_markers = [m for m in atp_markers if m is not None]

        if len(found_markers) > 1:
            raise ValueError(
                f"Multiple ATP markers detected in class name: {raw_class_name}"
            )

        # Determine ATP type
        if atp_mixed_string:
            atp_type = ATPType.ATP_MIXED_STRING
        elif atp_variation:
            atp_type = ATPType.ATP_VARIATION
        elif atp_mixed:
            atp_type = ATPType.ATP_MIXED
        elif atp_prototype:
            atp_type = ATPType.ATP_PROTO
        else:
            atp_type = ATPType.NONE

        # Remove ATP markers from class name
        clean_name = raw_class_name
        for marker in found_markers:
            clean_name = clean_name.replace(marker.group(0), "").strip()

        return atp_type, clean_name

    def _should_filter_attribute(
        self, attr_name: str, attr_type: str
    ) -> bool:
        """Check if an attribute should be filtered out.

        Requirements:
            SWR_PARSER_00011: Attribute Metadata Filtering
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            attr_name: The attribute name.
            attr_type: The attribute type.

        Returns:
            True if the attribute should be filtered, False otherwise.
        """
        return (
            ":" in attr_name or
            ";" in attr_name or
            attr_name.isdigit() or
            attr_type in self.CONTINUATION_TYPES or
            attr_name in self.FRAGMENT_NAMES or
            attr_name in self.PARTIAL_NAMES
        )

    def _create_attribute_from_pending(
        self,
        attr_name: str,
        attr_type: str,
        multiplicity: str,
        kind: AttributeKind,
        note: str,
    ) -> AutosarAttribute:
        """Create an AutosarAttribute from pending attribute data.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF

        Args:
            attr_name: The attribute name.
            attr_type: The attribute type.
            multiplicity: The attribute multiplicity.
            kind: The attribute kind.
            note: The attribute note.

        Returns:
            AutosarAttribute object.
        """
        is_ref = self._is_reference_type(attr_type)

        return AutosarAttribute(
            name=attr_name,
            type=attr_type,
            multiplicity=multiplicity,
            kind=kind,
            note=note,
            is_ref=is_ref,
        )

    def _add_attribute_if_valid(
        self,
        attributes: Dict[str, AutosarAttribute],
        pending_attr_name: Optional[str],
        pending_attr_type: Optional[str],
        pending_attr_multiplicity: Optional[str],
        pending_attr_kind: Optional[AttributeKind],
        pending_attr_note: Optional[str],
    ) -> None:
        """Add a pending attribute to the current class if it's valid.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF
            SWR_PARSER_00011: Attribute Metadata Filtering
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            attributes: Dictionary to add the attribute to.
            pending_attr_name: Name of the pending attribute.
            pending_attr_type: Type of the pending attribute.
            pending_attr_multiplicity: Multiplicity of the pending attribute.
            pending_attr_kind: Kind of the pending attribute.
            pending_attr_note: Note of the pending attribute.
        """
        if pending_attr_name is not None and pending_attr_type is not None:
            if not self._should_filter_attribute(pending_attr_name, pending_attr_type):
                attr = self._create_attribute_from_pending(
                    pending_attr_name,
                    pending_attr_type,
                    pending_attr_multiplicity or "1",
                    pending_attr_kind or AttributeKind.ATTR,
                    pending_attr_note or ""
                )
                attributes[pending_attr_name] = attr

    def _is_valid_type_definition(self, lines: List[str], start_index: int) -> bool:
        """Check if this is a valid type definition.

        A valid type definition must be followed by a Package line within 3 lines.

        Requirements:
            SWR_PARSER_00004: Class Definition Pattern Recognition

        Args:
            lines: List of text lines from the PDF.
            start_index: Starting line index.

        Returns:
            True if valid, False otherwise.
        """
        for i in range(start_index + 1, min(start_index + 4, len(lines))):
            line = lines[i].strip()
            if line.startswith("Package "):
                return True
            # Allow empty lines or Note lines, but reject anything else
            if line and not line.startswith("Note "):
                return False
        return False

    def _extract_package_path(self, lines: List[str], start_index: int) -> Optional[str]:
        """Extract package path from lines following type definition.

        Requirements:
            SWR_PARSER_00006: Package Hierarchy Building

        Args:
            lines: List of text lines from the PDF.
            start_index: Starting line index.

        Returns:
            Package path string, or None if not found.
        """
        for i in range(start_index + 1, min(start_index + 4, len(lines))):
            line = lines[i].strip()
            package_match = self.PACKAGE_PATTERN.match(line)
            if package_match:
                package_path = package_match.group(2)
                if package_match.group(1):  # M2:: was present
                    package_path = "M2::" + package_path
                return package_path
        return None

    def _create_source_location(
        self,
        pdf_filename: Optional[str],
        page_number: Optional[int],
        autosar_standard: Optional[str],
        standard_release: Optional[str],
    ) -> Optional[AutosarDocumentSource]:
        """Create source location for a type definition.

        Requirements:
            SWR_MODEL_00027: AUTOSAR Source Location Representation
            SWR_PARSER_00022: PDF Source Location Extraction

        Args:
            pdf_filename: PDF filename.
            page_number: Page number where type was defined.
            autosar_standard: Optional AUTOSAR standard identifier.
            standard_release: Optional AUTOSAR standard release.

        Returns:
            AutosarDocumentSource object, or None if pdf_filename is not provided.
        """
        if pdf_filename:
            if page_number is None:
                page_number = 1
            return AutosarDocumentSource(
                pdf_file=pdf_filename,
                page_number=page_number,
                autosar_standard=autosar_standard,
                standard_release=standard_release,
            )
        return None

    def _is_new_type_definition(self, line: str) -> bool:
        """Check if line represents a new type definition.

        Requirements:
            SWR_PARSER_00004: Class Definition Pattern Recognition
            SWR_PARSER_00013: Recognition of Primitive and Enumeration Class Definition Patterns

        Args:
            line: The line to check.

        Returns:
            True if line matches a new type definition pattern, False otherwise.
        """
        return (
            self.CLASS_PATTERN.match(line) is not None or
            self.PRIMITIVE_PATTERN.match(line) is not None or
            self.ENUMERATION_PATTERN.match(line) is not None
        )

    def _is_table_marker(self, line: str) -> bool:
        """Check if line is a table marker.

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            line: The line to check.

        Returns:
            True if line starts with "Table ", False otherwise.
        """
        return line.startswith("Table ")

    def _is_note_continuation(self, line: str, parser_type: str = "class") -> bool:
        """Check if a line continues a note (doesn't match any known pattern).

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            line: The line to check.
            parser_type: Type of parser ("class", "primitive", "enumeration").

        Returns:
            True if the line doesn't match any known pattern (note continues).
        """
        if not line:
            return False

        # Common patterns for all parsers
        if (self.CLASS_PATTERN.match(line) or
            self.PRIMITIVE_PATTERN.match(line) or
            self.ENUMERATION_PATTERN.match(line) or
            self.PACKAGE_PATTERN.match(line) or
            self.NOTE_PATTERN.match(line) or
            self.ATTRIBUTE_HEADER_PATTERN.match(line)):
            return False

        # Class-specific patterns
        if parser_type == "class":
            if (self.BASE_PATTERN.match(line) or
                self.SUBCLASS_PATTERN.match(line) or
                self.AGGREGATED_BY_PATTERN.match(line)):
                return False

        # Enumeration-specific patterns
        if parser_type == "enumeration":
            if self.ENUMERATION_LITERAL_HEADER_PATTERN.match(line):
                return False

        return True

    def _extract_note_text(
        self,
        note_match: Match,
        lines: List[str],
        line_index: int,
        parser_type: str = "class",
    ) -> str:
        """Extract multi-line note text starting from a matched Note line.

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            note_match: The regex match object for the Note line.
            lines: List of text lines from the PDF.
            line_index: Current line index.
            parser_type: Type of parser ("class", "primitive", "enumeration").

        Returns:
            The complete note text (may span multiple lines).
        """
        note_text = note_match.group(1).strip()

        # Check if note continues on next lines
        i = line_index + 1
        while i < len(lines):
            next_line = lines[i].strip()
            if self._is_note_continuation(next_line, parser_type):
                note_text += " " + next_line
                i += 1
            else:
                break

        return note_text.strip()

    def _handle_attribute_continuation(
        self, words: List[str], pending_attr_name: str, pending_attr_note: Optional[str],
        valid_third_words: Optional[set] = None,
    ) -> Dict[str, Optional[str]]:
        """Handle continuation of multi-line attribute.

        Requirements:
            SWR_PARSER_00012: Multi-Line Attribute Handling

        Args:
            words: Words from the continuation line.
            pending_attr_name: Pending attribute name.
            pending_attr_note: Pending attribute note.
            valid_third_words: Set of valid third words (defaults to common values).

        Returns:
            Dictionary with updated pending_attr_note.
        """
        if valid_third_words is None:
            valid_third_words = self.MULTIPLICITIES | self.ATTR_KINDS_ALL

        result: Dict[str, Optional[str]] = {"pending_attr_note": pending_attr_note}

        # Check if this is a continuation of the note
        # Continuation lines typically don't have the structure of a new attribute
        # They don't have multiplicity (0..1, *, 0..*) or kind (attr, aggr, ref)
        if len(words) > 2:
            third_word = words[2]
            if third_word not in valid_third_words:
                # This is likely a continuation of the note
                continuation_text = " ".join(words[2:])
                if pending_attr_note:
                    result["pending_attr_note"] = pending_attr_note + " " + continuation_text
                else:
                    result["pending_attr_note"] = continuation_text

        return result

    def _parse_attribute_kind(self, kind_str: str) -> AttributeKind:
        """Parse attribute kind string to AttributeKind enum.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF

        Args:
            kind_str: The kind string (e.g., "attr", "aggr", "ref").

        Returns:
            The corresponding AttributeKind enum value.
        """
        if kind_str in self.ATTR_KINDS_AGGR:
            return AttributeKind.AGGR
        if kind_str in self.ATTR_KINDS_REF:
            return AttributeKind.REF
        return AttributeKind.ATTR

    def _extract_attribute_parts(self, words: List[str], supports_ref: bool = False) -> Tuple[str, AttributeKind, str]:
        """Extract multiplicity, kind, and note from attribute line words.

        Requirements:
            SWR_PARSER_00010: Attribute Extraction from PDF

        Args:
            words: Words from the attribute line.
            supports_ref: Whether this parser supports the "ref" kind.

        Returns:
            Tuple of (multiplicity, kind, note).
        """
        multiplicity = "1"
        kind = AttributeKind.ATTR
        note = ""

        valid_kinds = self.ATTR_KINDS_ALL if supports_ref else (self.ATTR_KINDS_ATTR | self.ATTR_KINDS_AGGR)

        if len(words) > 2:
            # Check if third word is multiplicity or kind
            if words[2] in self.MULTIPLICITIES:
                multiplicity = words[2]
                # Fourth word is kind
                if len(words) > 3 and words[3] in valid_kinds:
                    kind = self._parse_attribute_kind(words[3])
                    # Fifth word onwards is note
                    if len(words) > 4:
                        note = " ".join(words[4:])
            elif words[2] in valid_kinds:
                kind = self._parse_attribute_kind(words[2])
                # Third word onwards is note
                if len(words) > 3:
                    note = " ".join(words[3:])

        return multiplicity, kind, note

    @abstractmethod
    def parse_definition(
        self,
        lines: List[str],
        line_index: int,
        pdf_filename: Optional[str] = None,
        page_number: Optional[int] = None,
        autosar_standard: Optional[str] = None,
        standard_release: Optional[str] = None,
    ) -> Optional[AutosarType]:
        """Parse a type definition from PDF lines.

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
            The parsed model object (AutosarClass, AutosarEnumeration, or AutosarPrimitive),
            or None if parsing failed.
        """
        pass

    @abstractmethod
    def continue_parsing(
        self,
        current_model: AutosarType,
        lines: List[str],
        line_index: int,
    ) -> Tuple[int, bool]:
        """Continue parsing a type definition from subsequent lines.

        Requirements:
            SWR_PARSER_00012: Multi-Line Attribute Handling
            SWR_PARSER_00015: Enumeration Literal Extraction from PDF
            SWR_PARSER_00016: Enumeration Literal Section Termination

        Args:
            current_model: The current model object being parsed.
            lines: List of text lines from the PDF.
            line_index: Current line index in the lines list.

        Returns:
            Tuple of (new_line_index, is_complete) where:
            - new_line_index: The line index to continue from
            - is_complete: True if parsing is complete, False if more lines needed
        """
        pass