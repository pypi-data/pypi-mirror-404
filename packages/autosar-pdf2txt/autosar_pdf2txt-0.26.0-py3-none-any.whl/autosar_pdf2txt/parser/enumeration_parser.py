"""AutosarEnumeration parser for extracting AUTOSAR enumeration definitions from PDF files.

This module provides the specialized parser for AutosarEnumeration definitions,
including literal parsing and index extraction.

Requirements:
    SWR_PARSER_00004: Class Definition Pattern Recognition
    SWR_PARSER_00013: Recognition of Primitive and Enumeration Class Definition Patterns
    SWR_PARSER_00014: Enumeration Literal Header Recognition
    SWR_PARSER_00015: Enumeration Literal Extraction from PDF
    SWR_PARSER_00016: Enumeration Literal Section Termination
    SWR_PARSER_00025: AutosarEnumeration Specialized Parser
    SWR_PARSER_00028: Direct Model Creation by Specialized Parsers
"""

import re
from pathlib import Path
from typing import Dict, List, Match, Optional, Tuple

import yaml

from autosar_pdf2txt.models import (
    AutosarEnumeration,
    AutosarEnumLiteral,
)
from autosar_pdf2txt.parser.base_parser import AbstractTypeParser, AutosarType


class AutosarEnumerationParser(AbstractTypeParser):
    """Specialized parser for AutosarEnumeration definitions.

    This parser handles the parsing of AUTOSAR enumeration definitions from PDF files,
    including:
    - Enumeration definition pattern recognition
    - Enumeration literal header recognition
    - Enumeration literal extraction with indices
    - State management across multiple pages

    Requirements:
        SWR_PARSER_00025: AutosarEnumeration Specialized Parser
        SWR_PARSER_00028: Direct Model Creation by Specialized Parsers
    """

    def __init__(self) -> None:
        """Initialize the AutosarEnumeration parser.

        Loads YAML configuration for enumeration literal parsing patterns.

        Requirements:
            SWR_PARSER_00025: AutosarEnumeration Specialized Parser
            SWR_PARSER_00101: YAML Configuration for Enumeration Literal Word Mapping
        """
        super().__init__()
        # Parsing state
        self._in_enumeration_literal_section: bool = False
        # Temporary list to collect literals during parsing (converted to tuple at end)
        self._pending_literals: List[AutosarEnumLiteral] = []

        # Load YAML configuration for word mapping and patterns
        enum_config = self._load_yaml_config()
        self._continuation_words: set = set(enum_config.get("continuation_words", []))
        self._suffix_words: set = set(enum_config.get("suffix_words", []))
        self._header_exclusion_patterns: list = enum_config.get("header_exclusion_patterns", [])
        self._header_words: list = enum_config.get("header_words", [])
        self._patches: Dict = enum_config.get("patches", {})

    def _load_yaml_config(self) -> Dict:
        """Load YAML configuration for enumeration literal parsing.

        Returns:
            Dictionary containing enumeration literal configuration keys:
            - continuation_words: Words indicating continuation lines
            - suffix_words: Words to append to literal names
            - header_exclusion_patterns: Patterns to skip as headers
            - header_words: Individual header words
            - patches: Manual corrections for edge cases

        Requirements:
            SWR_PARSER_00101: YAML Configuration for Enumeration Literal Word Mapping
        """
        config_path = Path(__file__).parent.parent / "config" / "parser_config.yaml"

        if not config_path.exists():
            # Return empty config if file not found (backward compatibility)
            return {
                "continuation_words": [],
                "suffix_words": [],
                "header_exclusion_patterns": [],
                "header_words": [],
                "patches": {}
            }

        with open(config_path, "r") as f:
            full_config = yaml.safe_load(f) or {}

        # Extract enumeration_literals section from global config
        enum_config = full_config.get("enumeration_literals", {})

        return enum_config

    def _reset_state(self) -> None:
        """Reset parser state for a new enumeration definition.

        This method clears all state variables to ensure clean parsing
        of each new enumeration definition without interference from previous enumerations.

        Requirements:
            SWR_PARSER_00025: AutosarEnumeration Specialized Parser
        """
        self._in_enumeration_literal_section = False
        self._pending_literals = []

    def parse_definition(
        self,
        lines: List[str],
        line_index: int,
        pdf_filename: Optional[str] = None,
        page_number: Optional[int] = None,
        autosar_standard: Optional[str] = None,
        standard_release: Optional[str] = None,
    ) -> Optional[AutosarEnumeration]:
        """Parse an enumeration definition from PDF lines.

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
            The parsed AutosarEnumeration object, or None if parsing failed.
        """
        # Reset state for new enumeration
        self._pending_literals = []

        if line_index >= len(lines):
            return None

        line = lines[line_index].strip()
        enum_match = self.ENUMERATION_PATTERN.match(line)

        if not enum_match:
            return None

        # Extract enumeration name
        raw_enum_name = enum_match.group(1).strip()

        # Validate ATP markers and get clean name
        atp_type, enum_name = self._validate_atp_markers(raw_enum_name)

        # Check if this is a valid enumeration definition (followed by package path)
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

        # Create AutosarEnumeration directly (no intermediate ClassDefinition)
        return AutosarEnumeration(
            name=enum_name,
            package=package_path,
            sources=[source] if source else [],
        )

    def continue_parsing(
        self,
        current_model: AutosarType,
        lines: List[str],
        line_index: int,
    ) -> Tuple[int, bool]:
        """Continue parsing an enumeration definition from subsequent lines.

        Requirements:
            SWR_PARSER_00014: Enumeration Literal Header Recognition
            SWR_PARSER_00015: Enumeration Literal Extraction from PDF
            SWR_PARSER_00016: Enumeration Literal Section Termination

        Args:
            current_model: The current AutosarEnumeration being parsed.
            lines: List of text lines from the PDF.
            line_index: Current line index in the lines list.

        Returns:
            Tuple of (new_line_index, is_complete) where:
            - new_line_index: The line index to continue from
            - is_complete: True if parsing is complete, False if more lines needed
        """
        # Type narrowing: current_model is always AutosarEnumeration for this parser
        assert isinstance(current_model, AutosarEnumeration)
        i = line_index
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Check for enumeration literal header
            enum_literal_header_match = self.ENUMERATION_LITERAL_HEADER_PATTERN.match(line)
            if enum_literal_header_match:
                self._in_enumeration_literal_section = True
                i += 1
                continue

            # Check for new class/primitive/enumeration definition
            if self._is_new_type_definition(line):
                # Special handling: If this is an enumeration with the same name as current,
                # it's likely a table header repeated on subsequent pages. Skip it.
                enum_match = self.ENUMERATION_PATTERN.match(line)
                if enum_match and enum_match.group(1) == current_model.name:
                    # Skip this line - it's a repeated header
                    i += 1
                    continue
                # New type definition - finalize and return
                self._finalize_enumeration(current_model)
                return i, True

            # Check for table (end of enumeration)
            if self._is_table_marker(line):
                self._finalize_enumeration(current_model)
                return i, True

            # Process enumeration literal section
            if self._in_enumeration_literal_section:
                enum_section_ended = self._process_enumeration_literal_line(line, current_model)
                if enum_section_ended:
                    self._in_enumeration_literal_section = False
                    self._finalize_enumeration(current_model)
                    return i, True
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
        self._finalize_enumeration(current_model)

        # If in enumeration literal section, return False to allow multi-page continuation
        # Requirements: SWR_PARSER_00032: Multi-page Enumeration Literal List Support
        if self._in_enumeration_literal_section:
            return i, False  # More literals expected on next page
        else:
            return i, True   # Complete

    def _finalize_enumeration(self, current_model: AutosarEnumeration) -> None:
        """Finalize the enumeration by converting pending literals to tuple.

        This method is called when enumeration parsing is complete to convert
        the temporarily collected literals into an immutable tuple.
        Applies YAML patches if configured.

        Requirements:
            SWR_PARSER_00015: Enumeration Literal Extraction from PDF
            SWR_MODEL_00019: AUTOSAR Enumeration Type Representation
            SWR_PARSER_00101: YAML Configuration for Enumeration Literal Word Mapping

        Args:
            current_model: The current AutosarEnumeration being parsed.
        """
        # Apply YAML patches before finalizing (if any)
        self._apply_patches(current_model)

        # Convert pending literals to immutable tuple
        current_model.enumeration_literals = tuple(self._pending_literals)
        self._pending_literals = []

    def _apply_patches(self, current_model: AutosarEnumeration) -> None:
        """Apply YAML patches to fix enumeration literal names.

        Patches are applied as a post-processing step for edge cases that
        the improved multi-line logic couldn't handle.

        Args:
            current_model: The current AutosarEnumeration being parsed.

        Requirements:
            SWR_PARSER_00101: YAML Configuration for Enumeration Literal Word Mapping
        """
        if not self._patches:
            return

        # Check if this enumeration has patches configured
        enum_name = current_model.name
        if enum_name not in self._patches:
            return

        # Get patches for this enumeration
        enum_patches = self._patches[enum_name]

        # Apply patches to pending literals
        for literal in self._pending_literals:
            if literal.name in enum_patches:
                patch_value = enum_patches[literal.name]
                
                # Check if patch_value is a dict (index-based patches) or string (apply to all)
                if isinstance(patch_value, dict):
                    # Index-based patches: {correct_name: target_index}
                    for correct_name, target_index in patch_value.items():
                        if literal.index == target_index:
                            # Apply patch only for this specific index
                            literal.name = correct_name
                            break
                else:
                    # String patch: apply to all occurrences
                    literal.name = patch_value

    def _process_enumeration_literal_line(self, line: str, current_model: AutosarEnumeration) -> bool:
        """Process a line in the enumeration literal section.

        This method handles the parsing of enumeration literal lines, including
        multi-line names, descriptions, and tags. It supports 5 different patterns
        of enumeration literal formatting found in AUTOSAR PDF specifications.

        Args:
            line: The line to process.
            current_model: The current enumeration model being built.

        Returns:
            True if the enumeration literal section ended, False otherwise.
        """
        # Check if this line ends the enumeration literal section
        if line.startswith("Table ") or line.startswith("Class ") or line.startswith("Primitive ") or line.startswith("Enumeration "):
            return True

        # Special handling for "Tags:" lines
        # These lines contain tag information like "atp.EnumerationLiteralIndex=0"
        # They don't match the ENUMERATION_LITERAL_PATTERN because they have a colon
        if line.strip().startswith("Tags:"):
            if self._pending_literals:
                # Initialize tags dictionary if not exists
                if self._pending_literals[-1].tags is None:
                    self._pending_literals[-1].tags = {}
                # Extract tags from the line (may contain some tags inline)
                tags = self._extract_literal_tags(line)
                # Merge tags into the literal's tags
                self._pending_literals[-1].tags.update(tags)
                # Update index if found
                if "atp.EnumerationLiteralIndex" in tags:
                    self._pending_literals[-1].index = int(tags["atp.EnumerationLiteralIndex"])
            return False

        # Check if this line looks like a tag continuation line (contains tag patterns)
        # This handles the case where tag data is on separate lines after "Tags:"
        # Only treat as tag continuation if the line doesn't look like a literal definition
        if self._pending_literals and self._pending_literals[-1].tags is not None:
            # Check if line looks like pure tag data (contains atp. or xml. patterns)
            # and is short (< 50 chars) or starts with tag pattern
            # Don't treat as tag continuation if it matches literal pattern (looks like a new literal)
            line_lower = line.lower()
            is_tag_data = ("atp.enumerationliteralindex=" in line_lower or "xml.name=" in line_lower)
            is_literal_pattern = self.ENUMERATION_LITERAL_PATTERN.match(line) is not None
            
            if is_tag_data and not is_literal_pattern and len(line) < 50:
                # Extract and merge tags
                tags = self._extract_literal_tags(line)
                self._pending_literals[-1].tags.update(tags)
                # Update index if found
                if "atp.EnumerationLiteralIndex" in tags:
                    self._pending_literals[-1].index = int(tags["atp.EnumerationLiteralIndex"])
                return False  # Don't process this line as a literal

        # Try to match enumeration literal pattern
        literal_match = self.ENUMERATION_LITERAL_PATTERN.match(line)
        if literal_match:
            literal_name = literal_match.group(1)
            literal_description = literal_match.group(2).strip() if literal_match.group(2) else ""

            # Type annotation for previous_literal (used in multiple branches below)
            previous_literal: Optional[AutosarEnumLiteral]

            # Common continuation words that indicate multi-line descriptions
            # These are fragments that should be appended to the previous literal
            # Loaded from YAML configuration (SWR_PARSER_00101)
            continuation_words = self._continuation_words

            # Check if this is a continuation line (multi-line description or multi-line literal name)
            is_continuation = False
            append_to_name = False  # Flag to indicate if we should append to name instead of description
            if self._pending_literals:
                # Check if this is the same literal name (duplicate indicates continuation)
                if literal_name == self._pending_literals[-1].name:
                    # Check if previous literal already has tags (index is not None)
                    # If it does, this is a NEW literal with same base name (Pattern 2/5)
                    if self._pending_literals[-1].index is not None:
                        is_continuation = False  # Don't treat as continuation, will create new literal below
                    else:
                        is_continuation = True
                # Check if the "name" is a common continuation word or starts with one
                elif (literal_name.lower() in continuation_words or
                      any(literal_name.lower().startswith(word) for word in self._suffix_words)):
                    # If it's a suffix word (First, Last, On, In, etc.), append to name
                    # Loaded from YAML configuration (SWR_PARSER_00101)
                    if (literal_name.lower() in self._suffix_words or
                        any(literal_name.lower().startswith(word) for word in self._suffix_words)):
                        is_continuation = True
                        append_to_name = True
                    else:
                        is_continuation = True
                # Check if description starts with lowercase (indicates continuation)
                # EXCEPT if it contains tag patterns (like "atp.EnumerationLiteralIndex")
                elif (literal_description and
                      literal_description[0].islower() and
                      "atp.EnumerationLiteralIndex" not in literal_description and
                      "xml.name" not in literal_description):
                    is_continuation = True
            
            if is_continuation and self._pending_literals:
                if append_to_name:
                    # Append to previous literal's name (for Pattern 2/5)
                    self._pending_literals[-1].name += literal_name
                else:
                    # Append to previous literal's description
                    previous_literal = self._pending_literals[-1]  # Safe: guarded by self._pending_literals check above
                    # Initialize description if None
                    if previous_literal.description is None:
                        previous_literal.description = ''
                    # Add a space before appending if needed
                    if not previous_literal.description.endswith(' '):
                        previous_literal.description += ' '
                    # Append the continuation text (include the "name" as it's part of the description)
                    continuation_text = f"{literal_name} {literal_description}" if literal_description else literal_name
                    previous_literal.description += continuation_text
                return False  # Important: return False to prevent further processing
            else:
                # Distinguish between Pattern 3 (combined names) and Pattern 2/5 (separate literals)
                previous_literal = self._pending_literals[-1] if self._pending_literals else None

                # Check for multi-line literal name scenario (enum3.png from master):
                # When consecutive lines have the same description and the literal name
                # continues the previous name (e.g., "reportingIn", "ChronologicalOrder", "OldestFirst")
                #
                # Clean the current description before comparing (remove tags) to handle
                # cases where some lines have tags and others don't (SWR_PARSER_00101)
                clean_current_desc = literal_description
                if "atp.EnumerationLiteralIndex" in clean_current_desc:
                    clean_current_desc = re.sub(r"\s*atp\.EnumerationLiteralIndex=\d+", "", clean_current_desc)
                if "xml.name" in clean_current_desc:
                    clean_current_desc = re.sub(r"\s*xml\.name=[^\s,]+", "", clean_current_desc)
                clean_current_desc = clean_current_desc.strip()

                if (literal_description and previous_literal and previous_literal.description and
                      clean_current_desc == previous_literal.description):
                    # Append to previous literal's name (stacked names with same description)
                    self._pending_literals[-1].name += literal_name
                    # Don't create a new literal, continue processing
                    return False

                # Check if this is Pattern 2/5 (separate literal):
                # - Previous literal has tags and index (complete)
                # - Current description is a real description (not just "Tags:")
                # - Previous literal has index tag
                # - Current name is NOT a small suffix word (which would be Pattern 3)
                # - Names are different (or same base name for Pattern 2)
                # - NOT a continuation line (append_to_name=False)
                # OR:
                # - Previous literal exists (with or without tags)
                # - Current description starts with uppercase (indicates new literal)
                # - Names are different
                # - NOT a continuation line (append_to_name=False)
                # - NOT a continuation word (in continuation_words set)
                is_new_literal_by_tags = (
                    previous_literal and
                    previous_literal.tags and
                    previous_literal.index is not None and
                    literal_description and
                    literal_description != "Tags:" and
                    "atp.EnumerationLiteralIndex" in previous_literal.tags and
                    not append_to_name and  # Not a continuation line (append_to_name=False)
                    # Only treat as Pattern 2/5 if name is NOT a small suffix word
                    # Loaded from YAML configuration (SWR_PARSER_00101)
                    (len(literal_name) > 5 or literal_name not in self._suffix_words)
                )
                is_new_literal_by_uppercase = (
                    previous_literal and
                    not is_continuation and  # NOT a continuation line (important!)
                    not append_to_name and  # Not a continuation line (append_to_name=False)
                    literal_description and
                    not literal_description.startswith("Tags:") and  # Not starting with "Tags:" (Pattern 3)
                    literal_description[0].isupper() and  # Starts with uppercase
                    literal_name != previous_literal.name and
                    len(literal_name) > 2  # Not a small word like "of", "in"
                )

                if is_new_literal_by_tags or is_new_literal_by_uppercase:
                    # This is Pattern 2/5 (separate literal) - current line is a NEW literal
                    # For Pattern 2, names are the same (base name) but create separate literals
                    # For Pattern 5, names are different but create separate literals
                    # Create a new literal with current name and description
                    tags = self._extract_literal_tags(literal_description)
                    index = None
                    if "atp.EnumerationLiteralIndex" in tags:
                        index = int(tags["atp.EnumerationLiteralIndex"])

                    # Clean description by removing all tag patterns
                    clean_description = literal_description
                    if "atp.EnumerationLiteralIndex" in tags:
                        clean_description = re.sub(r"\s*atp\.EnumerationLiteralIndex=\d+", "", clean_description)
                    if "xml.name" in tags:
                        clean_description = re.sub(r"\s*xml\.name=[^\s,]+", "", clean_description)
                    clean_description = clean_description.strip()

                    # Create new literal with current name and description
                    literal = AutosarEnumLiteral(
                        name=literal_name,
                        description=clean_description if clean_description else None,
                        index=index,
                        tags=tags,
                        value=tags.get("xml.name") if tags else None,
                    )
                    self._pending_literals.append(literal)
                    return False  # Pattern 2/5 handled, don't continue
                else:
                    # Previous literal doesn't have complete tags yet OR description is only "Tags:" OR names match
                    # This is Pattern 3 (combined names) or continuation
                    # Append to previous literal's name (not description)
                    # This handles literal names split across multiple lines in one cell
                    if self._pending_literals:
                        self._pending_literals[-1].name += literal_name
                        # If this line has "Tags:", process them
                        if literal_description.startswith("Tags:"):
                            tags = self._extract_literal_tags(literal_description)
                            index = None
                            if "atp.EnumerationLiteralIndex" in tags:
                                index = int(tags["atp.EnumerationLiteralIndex"])
                            self._pending_literals[-1].index = index
                            self._pending_literals[-1].tags = tags
                        return False  # Pattern 3 handled, don't continue
                    # If no previous literals, fall through to create new literal below

            if is_continuation and self._pending_literals:
                # Append to previous literal's description
                previous_literal = self._pending_literals[-1]
                # Initialize description if None
                if previous_literal.description is None:
                    previous_literal.description = ''
                # Add a space before appending if needed
                if not previous_literal.description.endswith(' '):
                    previous_literal.description += ' '
                # Append the continuation text (include the "name" as it's part of the description)
                continuation_text = f"{literal_name} {literal_description}" if literal_description else literal_name
                previous_literal.description += continuation_text
            else:
                # This is a new literal - create it
                # Filter out common header words and phrases that are not valid enumeration literals
                # These often appear in PDF headers around enumeration tables
                # Loaded from YAML configuration (SWR_PARSER_00101)
                skip_literal = False
                literal_lower = literal_name.lower()
                desc_lower = literal_description.lower() if literal_description else ""

                # Check if description contains header patterns (e.g., "Extract Template")
                for pattern in self._header_exclusion_patterns:
                    if pattern in desc_lower or pattern in literal_lower:
                        skip_literal = True
                        break

                # Also check if name is a single common header word with generic description
                # e.g., "Diagnostic" with description "Extract Template"
                if (literal_name in self._header_words and
                    any(p in desc_lower for p in self._header_exclusion_patterns)):
                    skip_literal = True

                if skip_literal:
                    # Skip this literal - it's likely header text
                    return False
                # Extract tags from description
                tags = self._extract_literal_tags(literal_description)

                # Extract index from tags (backward compatible)
                index = None
                if "atp.EnumerationLiteralIndex" in tags:
                    index = int(tags["atp.EnumerationLiteralIndex"])

                # Extract value from xml.name tag
                value = tags.get("xml.name") if tags else None

                # Clean description by removing all tag patterns
                clean_description = literal_description
                if "atp.EnumerationLiteralIndex" in tags:
                    clean_description = re.sub(r"\s*atp\.EnumerationLiteralIndex=\d+", "", clean_description)
                if "xml.name" in tags:
                    clean_description = re.sub(r"\s*xml\.name=[^\s,]+", "", clean_description)
                clean_description = clean_description.strip()

                # Create and add the literal to pending list
                literal = AutosarEnumLiteral(
                    name=literal_name,
                    description=clean_description if clean_description else None,
                    index=index,
                    tags=tags,
                    value=value,
                )
                self._pending_literals.append(literal)

        return False

    def _extract_literal_index(self, description: str) -> Optional[int]:
        """Extract literal index from description.

        Requirements:
            SWR_PARSER_00015: Enumeration Literal Extraction from PDF

        Args:
            description: The literal description.

        Returns:
            The index if found, None otherwise.
        """
        # Look for pattern like "atp.EnumerationLiteralIndex=0"
        index_pattern = re.compile(r"atp\.EnumerationLiteralIndex=(\d+)")
        match = index_pattern.search(description)
        if match:
            return int(match.group(1))
        return None

    def _extract_literal_tags(self, description: str) -> Dict[str, str]:
        """Extract all metadata tags from description.

        Extracts patterns like:
        - atp.EnumerationLiteralIndex=0
        - xml.name=ISO-11992-4

        Requirements:
            SWR_PARSER_00031: Enumeration Literal Tags Extraction

        Args:
            description: The literal description.

        Returns:
            Dictionary of tag keys to tag values.
        """
        tags = {}

        # Extract atp.EnumerationLiteralIndex
        index_pattern = re.compile(r"atp\.EnumerationLiteralIndex=(\d+)")
        index_match = index_pattern.search(description)
        if index_match:
            tags["atp.EnumerationLiteralIndex"] = index_match.group(1)

        # Extract xml.name
        xml_pattern = re.compile(r"xml\.name=([^\s,]+)")
        xml_match = xml_pattern.search(description)
        if xml_match:
            tags["xml.name"] = xml_match.group(1)

        return tags

    def _process_note_line(
        self, note_match: Match, lines: List[str], line_index: int, current_model: AutosarEnumeration
    ) -> None:
        """Process a note line and extract multi-line note text.

        Requirements:
            SWR_PARSER_00021: Multi-Line Attribute Parsing for AutosarClass

        Args:
            note_match: The regex match object.
            lines: List of text lines from the PDF.
            line_index: Current line index.
            current_model: The current AutosarEnumeration being parsed.
        """
        note_text = self._extract_note_text(note_match, lines, line_index, parser_type="enumeration")
        current_model.note = note_text