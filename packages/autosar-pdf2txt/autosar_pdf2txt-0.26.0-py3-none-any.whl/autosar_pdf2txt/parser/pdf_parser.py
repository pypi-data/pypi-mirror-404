"""PDF parser for extracting AUTOSAR class hierarchies from PDF files.

This module provides the main PdfParser class that orchestrates parsing
and delegates to specialized parsers for each AUTOSAR type.

Requirements:
    SWR_PARSER_00001: PDF Parser Initialization
    SWR_PARSER_00002: Backend Validation
    SWR_PARSER_00003: PDF File Parsing
    SWR_PARSER_00006: Package Hierarchy Building
    SWR_PARSER_00033: ATP Interface Tracking (parent resolution from implements)

    SWR_PARSER_00017: AUTOSAR Class Parent Resolution
    SWR_PARSER_00018: Ancestry Analysis for Parent Resolution
    SWR_PARSER_00019: Backend Warning Suppression
    SWR_PARSER_00022: PDF Source Location Extraction
    SWR_PARSER_00027: Parser Backward Compatibility
    SWR_PARSER_00031: ATP Interface Implementation Tracking
    SWR_PARSER_00032: ATP Interface Pure Interface Validation
"""

import logging
import warnings
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, cast

from autosar_pdf2txt.models import (
    AutosarClass,
    AutosarDoc,
    AutosarEnumeration,
    AutosarPackage,
    AutosarPrimitive,
)

from autosar_pdf2txt.models.enums import ATPType

from autosar_pdf2txt.parser.class_parser import AutosarClassParser
from autosar_pdf2txt.parser.enumeration_parser import AutosarEnumerationParser
from autosar_pdf2txt.parser.primitive_parser import AutosarPrimitiveParser

logger = logging.getLogger(__name__)


class PdfParser:
    """Parse AUTOSAR PDF files to extract package and class hierarchies.

    Requirements:
        SWR_PARSER_00001: PDF Parser Initialization

    The parser extracts class definitions from PDF files and builds
    AutosarPackage and AutosarClass objects using specialized parsers
    for each AUTOSAR type.

    Usage:
        >>> parser = PdfParser()
        >>> packages = parser.parse_pdf("path/to/file.pdf")
        >>> print(len(packages))
    """

    def __init__(self) -> None:
        """Initialize the PDF parser.

        Requirements:
            SWR_PARSER_00001: PDF Parser Initialization
            SWR_PARSER_00007: PDF Backend Support - pdfplumber

        Raises:
            ImportError: If pdfplumber is not installed.
        """
        self._validate_backend()

        # Instantiate specialized parsers
        self._class_parser = AutosarClassParser()
        self._enum_parser = AutosarEnumerationParser()
        self._primitive_parser = AutosarPrimitiveParser()

    def _validate_backend(self) -> None:
        """Validate that pdfplumber backend is available.

        Requirements:
            SWR_PARSER_00002: Backend Validation
            SWR_PARSER_00007: PDF Backend Support - pdfplumber

        Raises:
            ImportError: If pdfplumber is not installed.
        """
        try:
            import pdfplumber as _  # noqa: F401
        except ImportError:  # pragma: no cover
            raise ImportError(
                "pdfplumber is not installed. Install it with: pip install pdfplumber"
            )

    def _extract_autosar_metadata(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract AUTOSAR standard and release from PDF text.

        This method scans the extracted text for patterns indicating AUTOSAR
        standard and release information, typically found in document headers
        or footers.

        Requirements:
            SWR_PARSER_00022: PDF Source Location Extraction

        Args:
            text: The complete extracted text from the PDF.

        Returns:
            A tuple of (autosar_standard, standard_release). Both values are
            Optional[str] and will be None if not found in the text.
        """
        import re

        autosar_standard: Optional[str] = None
        standard_release: Optional[str] = None

        # Pattern for AUTOSAR standard: "Part of AUTOSAR Standard: <StandardName>" or "Part of AUTOSAR Standard <StandardName>"
        standard_pattern = re.compile(r"Part of AUTOSAR Standard:?\s*(.+)")
        # Pattern for AUTOSAR release: "Part of Standard Release: R<YY>-<MM>" or "Part of Standard Release R<YY>-<MM>"
        release_pattern = re.compile(r"Part of Standard Release:?\s*(R\d{2}-\d{2})")

        for line in text.split("\n"):
            # Try to match AUTOSAR standard
            standard_match = standard_pattern.match(line.strip())
            if standard_match and autosar_standard is None:
                autosar_standard = standard_match.group(1).strip()

            # Try to match AUTOSAR release
            release_match = release_pattern.match(line.strip())
            if release_match and standard_release is None:
                standard_release = release_match.group(1).strip()

        return autosar_standard, standard_release

    def parse_pdf(self, pdf_path: str) -> AutosarDoc:
        """Parse a PDF file and extract the package hierarchy.

        This is a convenience method for parsing a single PDF. Internally calls
        parse_pdfs() to ensure consistent behavior whether parsing one or many PDFs.

        Requirements:
            SWR_PARSER_00003: PDF File Parsing

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            AutosarDoc containing packages and root classes.

        Raises:
            FileNotFoundError: If the PDF file doesn't exist.
            Exception: If PDF parsing fails.
        """
        return self.parse_pdfs([pdf_path])

    def parse_pdfs(self, pdf_paths: List[str]) -> AutosarDoc:
        """Parse multiple PDF files and extract the complete package hierarchy.

        This method parses all PDFs first, then builds the package hierarchy and
        resolves parent/children relationships on the complete model. This ensures
        that parent classes are found even if they are defined in later PDFs.

        Requirements:
            SWR_PARSER_00003: PDF File Parsing
            SWR_PARSER_00006: Package Hierarchy Building
    SWR_PARSER_00033: ATP Interface Tracking (parent resolution from implements)

            SWR_PARSER_00017: AUTOSAR Class Parent Resolution

        Args:
            pdf_paths: List of paths to PDF files.

        Returns:
            AutosarDoc containing packages and root classes from all PDFs.

        Raises:
            FileNotFoundError: If any PDF file doesn't exist.
            Exception: If PDF parsing fails.
        """
        # Phase 1: Extract all model objects from ALL PDFs first
        all_models: List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]] = []
        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"  [{i}/{len(pdf_paths)}] 📄 {pdf_path}")
            models = self._extract_models(pdf_path)
            all_models.extend(models)

        # Phase 2: Build complete package hierarchy once
        return self._build_package_hierarchy(all_models)

    def _extract_models(self, pdf_path: str) -> List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]]:
        """Extract all model objects from the PDF.

        Requirements:
            SWR_PARSER_00003: PDF File Parsing

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of model objects (AutosarClass, AutosarEnumeration, AutosarPrimitive).
        """
        return self._extract_with_pdfplumber(pdf_path)

    def _extract_with_pdfplumber(self, pdf_path: str) -> List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]]:
        """Extract model objects using pdfplumber.

        Requirements:
            SWR_PARSER_00003: PDF File Parsing
            SWR_PARSER_00007: PDF Backend Support - pdfplumber
    SWR_PARSER_00008: PDF Backend Support - pdfplumber

            SWR_PARSER_00009: Proper Word Spacing in PDF Text Extraction
            SWR_PARSER_00019: PDF Backend Warning Suppression
            SWR_MODEL_00027: AUTOSAR Source Location Representation
            SWR_PARSER_00022: PDF Source Location Extraction

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            List of model objects with source information.
        """
        import pdfplumber

        models: List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]] = []

        # Extract PDF filename for source tracking
        pdf_filename = Path(pdf_path).name

        # SWR_PARSER_00019: Suppress pdfplumber warnings that don't affect parsing
        # Many AUTOSAR PDFs have minor PDF specification errors that generate warnings
        # but don't affect text extraction correctness
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="pdfplumber")

            try:
                with pdfplumber.open(pdf_path) as pdf:
                    # Phase 1: Extract all text from all pages into a single buffer
                    # SWR_PARSER_00030: Track line-to-page mapping for accurate page number tracking
                    text_buffer = StringIO()
                    line_to_page: List[int] = []  # Maps line index to page number
                    
                    for page_num, page in enumerate(pdf.pages, start=1):
                        # Use extract_words() with x_tolerance=1 to properly extract words with spaces
                        # This fixes the issue where words are concatenated without spaces
                        words = page.extract_words(x_tolerance=1)

                        if words:
                            # Reconstruct text from words, preserving line breaks
                            # Group words by their vertical position (top coordinate)
                            current_y = None
                            for word in words:
                                text = word['text']
                                top = word['top']

                                # Check if we've moved to a new line
                                if current_y is not None and abs(top - current_y) > 5:
                                    text_buffer.write("\n")
                                    # Record the page number for this line
                                    line_to_page.append(page_num)

                                text_buffer.write(text + " ")
                                current_y = top

                            # Add newline after each page
                            text_buffer.write("\n")
                            line_to_page.append(page_num)

                    # Phase 2: Parse the complete text at once
                    complete_text = text_buffer.getvalue()
                    
                    # Parse all text with state management for multi-page definitions
                    current_models: Dict[int, Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]] = {}
                    model_parsers: Dict[int, str] = {}  # Maps model index to parser type
                    
                    models = self._parse_complete_text(
                        complete_text,
                        pdf_filename=pdf_filename,
                        current_models=current_models,
                        model_parsers=model_parsers,
                        line_to_page=line_to_page,
                    )

            except Exception as e:
                raise Exception(f"Failed to parse PDF with pdfplumber: {e}") from e

        return models

    def _parse_complete_text(
        self,
        text: str,
        pdf_filename: Optional[str] = None,
        current_models: Optional[Dict[int, Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]]] = None,
        model_parsers: Optional[Dict[int, str]] = None,
        line_to_page: Optional[List[int]] = None,
    ) -> List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]]:
        """Parse model definitions from complete PDF text.

        This method processes the complete text from the entire PDF and:
        1. Extracts AUTOSAR standard and release metadata
        2. Detects new type definitions (Class, Enumeration, Primitive)
        3. Delegates to the appropriate specialized parser
        4. Continues parsing for existing models across pages

        Requirements:
            SWR_PARSER_00004: Class Definition Pattern Recognition
            SWR_PARSER_00013: Recognition of Primitive and Enumeration Class Definition Patterns
            SWR_PARSER_00012: Multi-Line Attribute Handling
            SWR_PARSER_00014: Enumeration Literal Header Recognition
            SWR_PARSER_00015: Enumeration Literal Extraction from PDF
            SWR_PARSER_00016: Enumeration Literal Section Termination
            SWR_MODEL_00027: AUTOSAR Source Location Representation
            SWR_PARSER_00022: PDF Source Location Extraction
            SWR_PARSER_00030: Page Number Tracking in Two-Phase Parsing

        Args:
            text: The complete extracted text from the entire PDF.
            pdf_filename: Optional PDF filename for source tracking.
            current_models: Dictionary of current models being parsed (for multi-page support).
            model_parsers: Dictionary mapping model indices to parser types.
            line_to_page: Optional list mapping line indices to page numbers.

        Returns:
            List of model objects parsed from the PDF.
        """
        if current_models is None:
            current_models = {}
        if model_parsers is None:
            model_parsers = {}
        if line_to_page is None:
            line_to_page = []

        # Extract AUTOSAR standard and release from text
        autosar_standard, standard_release = self._extract_autosar_metadata(text)

        models: List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]] = []
        lines = text.split("\n")

        # SWR_PARSER_00030: Track current page number during parsing
        # Use line_to_page mapping if available, otherwise default to page 1
        current_page = 1

        i = 0
        new_model: Optional[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]] = None
        while i < len(lines):
            line = lines[i].strip()

            # SWR_PARSER_00030: Skip empty lines
            if not line:
                i += 1
                continue

            # SWR_PARSER_00030: Update current page from line_to_page mapping
            if i < len(line_to_page):
                current_page = line_to_page[i]

            # Try to match type definition patterns
            class_match = self._class_parser.CLASS_PATTERN.match(line)
            primitive_match = self._primitive_parser.PRIMITIVE_PATTERN.match(line)
            enumeration_match = self._enum_parser.ENUMERATION_PATTERN.match(line)

            if class_match or primitive_match or enumeration_match:
                # Extract the name from the match
                if class_match:
                    name = class_match.group(1)
                elif primitive_match:
                    name = primitive_match.group(1)
                else:  # enumeration_match
                    assert enumeration_match is not None
                    name = enumeration_match.group(1)

                # Check if this model is already being parsed (multi-page definition)
                # This handles the case where table headers are repeated on subsequent pages
                existing_model_index = None
                existing_model = None
                for model_index, current_model in current_models.items():
                    if current_model.name == name:
                        existing_model_index = model_index
                        existing_model = current_model
                        break

                if existing_model is not None:
                    # Continue parsing the existing model
                    assert existing_model_index is not None
                    parser_type = model_parsers[existing_model_index]
                    i += 1
                    is_complete = False
                    while i < len(lines):
                        if parser_type == "class":
                            new_i, is_complete = self._class_parser.continue_parsing(
                                existing_model, lines, i
                            )
                        elif parser_type == "primitive":
                            new_i, is_complete = self._primitive_parser.continue_parsing(
                                existing_model, lines, i
                            )
                        else:  # enumeration
                            new_i, is_complete = self._enum_parser.continue_parsing(
                                existing_model, lines, i
                            )

                        i = new_i

                        if is_complete:
                            # Remove from current_models as parsing is complete
                            if existing_model_index in current_models:
                                del current_models[existing_model_index]
                                del model_parsers[existing_model_index]
                            # Add the continued model to the models list
                            models.append(existing_model)
                            # Don't increment i - continue_parsing already returned the correct line index
                            break
                    else:
                        # Loop completed without break (end of lines reached)
                        # Remove from current_models as parsing is complete
                        if existing_model_index in current_models:
                            del current_models[existing_model_index]
                            del model_parsers[existing_model_index]
                        # Finalize the model (apply patches, etc.) before adding to models list
                        if parser_type == "enumeration":
                            self._enum_parser._finalize_enumeration(
                                cast(AutosarEnumeration, existing_model)
                            )
                        # Add the continued model to the models list
                        models.append(existing_model)
                    continue

                # This is a new type definition
                # Reset parser state before parsing new type
                # SWR_PARSER_00030: Ensure clean state for each new type definition
                if class_match:
                    self._class_parser._reset_state()
                    new_model = self._class_parser.parse_definition(
                        lines, i, pdf_filename, current_page, autosar_standard, standard_release
                    )
                    parser_type = "class"
                elif primitive_match:
                    self._primitive_parser._reset_state()
                    new_model = self._primitive_parser.parse_definition(
                        lines, i, pdf_filename, current_page, autosar_standard, standard_release
                    )
                    parser_type = "primitive"
                else:  # enumeration_match
                    self._enum_parser._reset_state()
                    new_model = self._enum_parser.parse_definition(
                        lines, i, pdf_filename, current_page, autosar_standard, standard_release
                    )
                    parser_type = "enumeration"

                if new_model:
                    # Store the model for continuation parsing
                    model_index = len(models)
                    current_models[model_index] = new_model
                    model_parsers[model_index] = parser_type
                    models.append(new_model)

                    # Continue parsing with this model
                    i += 1
                    while i < len(lines):
                        # Use the appropriate parser to continue parsing
                        if parser_type == "class":
                            new_i, is_complete = self._class_parser.continue_parsing(
                                new_model, lines, i
                            )
                        elif parser_type == "primitive":
                            new_i, is_complete = self._primitive_parser.continue_parsing(
                                new_model, lines, i
                            )
                        else:  # enumeration
                            new_i, is_complete = self._enum_parser.continue_parsing(
                                new_model, lines, i
                            )

                        i = new_i

                        if is_complete:
                            # Remove from current_models as parsing is complete
                            if model_index in current_models:
                                del current_models[model_index]
                                del model_parsers[model_index]
                            # Don't increment i - continue_parsing already returned the correct line index
                            break
                    continue

            # Try to continue parsing existing models
            if current_models:
                for model_index, current_model in list(current_models.items()):
                    parser_type = model_parsers[model_index]
                    
                    if parser_type == "class":
                        new_i, is_complete = self._class_parser.continue_parsing(
                            current_model, lines, i
                        )
                    elif parser_type == "primitive":
                        new_i, is_complete = self._primitive_parser.continue_parsing(
                            current_model, lines, i
                        )
                    else:  # enumeration
                        new_i, is_complete = self._enum_parser.continue_parsing(
                            current_model, lines, i
                        )

                    i = new_i

                    if is_complete:
                        # Remove from current_models as parsing is complete
                        del current_models[model_index]
                        del model_parsers[model_index]
                        # Advance past the line that caused completion
                        i += 1
                    else:
                        # Model still being parsed, don't advance i
                        # But increment i to avoid infinite loop
                        # The parser will try again on the next line
                        i += 1
                        break
            else:
                i += 1

        return models

    def _build_package_hierarchy(self, models: List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]]) -> AutosarDoc:
        """Build complete package hierarchy from model objects.

        Requirements:
            SWR_PARSER_00006: Package Hierarchy Building
            SWR_MODEL_00023: AUTOSAR Document Model

        Args:
            models: List of model objects (AutosarClass, AutosarEnumeration, AutosarPrimitive).

        Returns:
            AutosarDoc containing packages and root classes.
        """
        # Filter out invalid models (those with empty or whitespace names)
        valid_models = [
            model for model in models
            if model.name and not model.name.isspace()
        ]

        # Create a dictionary to track packages by path
        packages_dict: Dict[str, AutosarPackage] = {}

        # Process each model and build package hierarchy
        for model in valid_models:
            # Get or create package chain
            current_pkg = self._get_or_create_package_chain(
                model.package, packages_dict
            )

            # Add model to package
            if isinstance(model, AutosarClass):
                current_pkg.add_type(model)
            elif isinstance(model, AutosarEnumeration):
                current_pkg.add_type(model)
            elif isinstance(model, AutosarPrimitive):
                current_pkg.add_type(model)

        # Collect root packages (those that are not subpackages of any other package)
        all_subpackages: set[str] = set()
        for pkg in packages_dict.values():
            all_subpackages.update(subpkg.name for subpkg in pkg.subpackages)

        root_packages = [
            pkg for pkg in packages_dict.values()
            if pkg.name not in all_subpackages
        ]

        # Collect root classes (classes with no bases)
        root_classes = [
            model for model in valid_models
            if isinstance(model, AutosarClass) and not model.bases
        ]

        # Create AutosarDoc
        doc = AutosarDoc(packages=root_packages, root_classes=root_classes)

        # Resolve parent/children references (pass all packages, not just root)
        all_packages = list(packages_dict.values())
        self._resolve_parent_references(all_packages)

        # Build interface implementation map
        interface_map = self._build_interface_implementation_map(all_packages)

        # Update ATP interfaces with implementers
        self._update_interface_implementers(all_packages, interface_map)

        return doc

    def _get_or_create_package_chain(
        self, package_path: str, packages_dict: Dict[str, AutosarPackage]
    ) -> AutosarPackage:
        """Get or create package chain for a given package path.

        Requirements:
            SWR_PARSER_00002: PDF Content Patterns
            SWR_PARSER_00006: Package Hierarchy Building

        Args:
            package_path: The package path (e.g., "M2::AUTOSAR::DataTypes").
            packages_dict: Dictionary of existing packages.

        Returns:
            The leaf package in the chain.

        Note:
            M2:: prefix is preserved to maintain the complete package hierarchy
            with M2 as the root metamodel package.
        """
        # Split by :: (preserving M2:: prefix if present)
        parts = package_path.split("::")

        # Build package chain
        current_path = ""
        current_pkg: Optional[AutosarPackage] = None

        for part in parts:
            if current_path:
                current_path += "::"
            current_path += part

            if current_path not in packages_dict:
                new_pkg = AutosarPackage(name=part)
                packages_dict[current_path] = new_pkg

                if current_pkg:
                    current_pkg.add_subpackage(new_pkg)

            current_pkg = packages_dict[current_path]

        # current_pkg is guaranteed to be non-None here because we always create packages
        assert current_pkg is not None
        return current_pkg

    def _resolve_parent_references(self, packages: List[AutosarPackage]) -> List[AutosarClass]:
        """Resolve parent and children references for all classes.

        Requirements:
    SWR_PARSER_00033: ATP Interface Tracking (parent resolution from implements)

            SWR_PARSER_00017: AUTOSAR Class Parent Resolution
            SWR_PARSER_00018: Ancestry Analysis for Parent Resolution
            SWR_PARSER_00029: Subclasses Contradiction Validation
            SWR_PARSER_00031: ATP Interface Pure Interface Semantics

        ATP classes are pure interfaces and do not have parent/children relationships.
        Only regular classes resolve parent from their bases list.

        Args:
            packages: List of packages to process.

        Returns:
            List of root classes (classes without parents).
        """
        # Build ancestry cache for efficient parent lookup
        warned_ancestry_bases: set[str] = set()
        warned_parent_bases: set[str] = set()
        ancestry_cache = self._build_ancestry_cache(packages, warned_ancestry_bases)

        # Set parent references for all classes (skip ATP classes - they are pure interfaces)
        root_classes: List[AutosarClass] = []
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass):
                    # Skip ATP classes - they are pure interfaces with no parent/children
                    if typ.atp_type != ATPType.NONE:
                        continue
                    self._set_parent_references(typ, ancestry_cache, packages, warned_parent_bases)
                    if typ.parent is None:
                        root_classes.append(typ)

        # Populate children lists (skip ATP classes)
        self._populate_children_lists(packages)

        # Validate ATP interfaces are pure (SWR_PARSER_00032)
        self._validate_atp_interfaces(packages)

        # Validate subclasses contradictions (SWR_PARSER_00029)
        # Skip ATP classes - they have no inheritance
        self._validate_subclasses(packages)

        return root_classes

    def _build_ancestry_cache(self, packages: List[AutosarPackage], warned_bases: set[str]) -> Dict[str, Set[str]]:
        """Build a cache of ancestry relationships for efficient parent lookup.

        Requirements:
            SWR_PARSER_00018: Ancestry Analysis for Parent Resolution
            SWR_PARSER_00020: Missing Base Class Logging with Deduplication

        Args:
            packages: List of packages to process.
            warned_bases: Set of base classes that have already been warned about.

        Returns:
            Dictionary mapping class names to sets of all ancestor class names.
        """
        # First, build a direct bases map
        direct_bases: Dict[str, List[str]] = {}
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass):
                    direct_bases[typ.name] = typ.bases
        
        # Then, recursively collect all ancestors for each class
        def collect_ancestors(class_name: str, visited: Set[str]) -> Set[str]:
            """Recursively collect all ancestors of a class."""
            if class_name in visited:
                return set()
            
            visited.add(class_name)
            ancestors = set()
            
            for base_name in direct_bases.get(class_name, []):
                if base_name != "ARObject":  # Filter out ARObject (implicit root)
                    # Check if base class exists in the model
                    base_exists = False
                    for pkg in packages:
                        for typ in pkg.types:
                            if isinstance(typ, AutosarClass) and typ.name == base_name:
                                base_exists = True
                                break
                        if base_exists:
                            break
                    
                    ancestors.add(base_name)
                    
                    # If base class doesn't exist, log warning if not already warned
                    if not base_exists and base_name not in warned_bases:
                        logger.warning(
                            "Class '%s' referenced in base classes could not be located in the model during ancestry traversal. Ancestry analysis may be incomplete.",
                            base_name,
                        )
                        warned_bases.add(base_name)
                    
                    # Recursively collect ancestors of this base
                    ancestors.update(collect_ancestors(base_name, visited))
            
            return ancestors
        
        cache: Dict[str, Set[str]] = {}
        for class_name in direct_bases.keys():
            cache[class_name] = collect_ancestors(class_name, set())
        
        return cache

    def _set_parent_references(
        self,
        cls: AutosarClass,
        ancestry_cache: Dict[str, Set[str]],
        packages: List[AutosarPackage],
        warned_bases: set[str],
    ) -> None:
        """Set parent reference for a class by finding the actual direct parent.

        Requirements:
    SWR_PARSER_00033: ATP Interface Tracking (parent resolution from implements)

            SWR_PARSER_00017: AUTOSAR Class Parent Resolution
            SWR_PARSER_00018: Ancestry Analysis for Parent Resolution

        Args:
            cls: The class to set parent for.
            ancestry_cache: Cache of ancestry relationships.
            packages: List of all packages.
            warned_bases: Set of base classes that have already been warned about.
        """
        if not cls.bases:
            return

        # Filter out ARObject from the bases list (ARObject is the implicit root)
        filtered_bases = [b for b in cls.bases if b != "ARObject"]

        # If we have bases after filtering ARObject, use the most specific one
        # Otherwise, fall back to the original bases (may include ARObject)
        bases_to_check = filtered_bases if filtered_bases else cls.bases

        # Find existing bases only (for ancestry analysis)
        existing_bases = []
        for base_name in bases_to_check:
            base_class = self._find_class_in_all_packages(base_name, packages)
            if base_class is not None:
                existing_bases.append(base_name)
            else:
                # Base class not found - log warning if not already warned
                if base_name not in warned_bases:
                    logger.warning(
                        "Class '%s::%s' references base class '%s' which could not be located in the model",
                        cls.package,
                        cls.name,
                        base_name,
                    )
                    warned_bases.add(base_name)

        if not existing_bases:
            # No valid bases found, parent remains None
            return

        # Ancestry-based parent selection:
        # Filter out bases that are ancestors of other bases
        # The direct parent is the base that is NOT an ancestor of any other base
        direct_parent = None
        for i, base_name in enumerate(existing_bases):
            is_ancestor = False
            for j, other_base_name in enumerate(existing_bases):
                if i != j:
                    # Check if base_name is an ancestor of other_base_name
                    # This means other_base_name's ancestors include base_name
                    if base_name in ancestry_cache.get(other_base_name, set()):
                        is_ancestor = True
                        break
            
            if not is_ancestor:
                # This base is not an ancestor of any other base
                # It could be the direct parent
                # If multiple candidates exist, choose the last one (backward compatibility)
                direct_parent = base_name

        if direct_parent:
            cls.parent = direct_parent

    def _populate_children_lists(self, packages: List[AutosarPackage]) -> None:
        """Populate children lists for all classes.

        Requirements:
    SWR_PARSER_00033: ATP Interface Tracking (parent resolution from implements)

            SWR_PARSER_00017: AUTOSAR Class Parent Resolution

        Args:
            packages: List of all packages.
        """
        # Build a parent-to-children mapping (O(n) complexity)
        parent_to_children: Dict[str, List[str]] = {}
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass) and typ.parent:
                    if typ.parent not in parent_to_children:
                        parent_to_children[typ.parent] = []
                    parent_to_children[typ.parent].append(typ.name)
        
        # Populate children lists using the mapping
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass) and typ.name in parent_to_children:
                    typ.children = parent_to_children[typ.name]

    def _build_interface_implementation_map(
        self, packages: List[AutosarPackage]
    ) -> Dict[str, List[str]]:
        """Build reverse lookup map from ATP interfaces to their implementers.

        This method builds a dictionary mapping each ATP interface name to a list
        of class names that implement that interface. This is used to populate
        the implemented_by attribute of ATP interfaces.

        Requirements:
            SWR_PARSER_00031: ATP Interface Implementation Tracking

        Args:
            packages: List of all packages to process.

        Returns:
            Dictionary mapping ATP interface names to lists of implementing class names.
        """
        interface_map: Dict[str, List[str]] = {}

        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass):
                    # For each class that implements ATP interfaces
                    for interface_name in typ.implements:
                        if interface_name not in interface_map:
                            interface_map[interface_name] = []
                        if typ.name not in interface_map[interface_name]:
                            interface_map[interface_name].append(typ.name)

        return interface_map

    def _update_interface_implementers(
        self, packages: List[AutosarPackage], interface_map: Dict[str, List[str]]
    ) -> None:
        """Update ATP interface classes with their implementers.

        This method populates the implemented_by attribute of each ATP interface
        with the list of classes that implement it.

        Requirements:
            SWR_PARSER_00031: ATP Interface Implementation Tracking

        Args:
            packages: List of all packages to process.
            interface_map: Map from interface names to implementers.
        """
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass) and typ.atp_type != ATPType.NONE:
                    implementers = interface_map.get(typ.name, [])
                    typ.implemented_by = implementers

    def _find_class_in_all_packages(
        self, class_name: str, packages: List[AutosarPackage]
    ) -> Optional[AutosarClass]:
        """Find a class by name across all packages.

        Args:
            class_name: Name of the class to find.
            packages: List of packages to search.

        Returns:
            The AutosarClass if found, None otherwise.
        """
        for pkg in packages:
            cls = pkg.get_class(class_name)
            if cls is not None:
                return cls
        return None

    def _validate_atp_interfaces(self, packages: List[AutosarPackage]) -> None:
        """Validate that ATP classes are pure interfaces.

        ATP classes should have no inheritance relationships (no bases, parent, or children).
        However, we log warnings instead of raising errors to accommodate real-world
        PDF data where ATP classes may have inheritance relationships.

        Requirements:
            SWR_PARSER_00032: ATP Interface Pure Interface Validation

        Args:
            packages: List of all packages to validate.
        """
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass) and typ.atp_type != ATPType.NONE:
                    if typ.bases:
                        logger.debug(
                            "ATP interface '%s' in package '%s' has bases %s. "
                            "ATP interfaces should be pure interfaces with no inheritance relationships.",
                            typ.name,
                            pkg.name,
                            typ.bases,
                        )
                    if typ.parent is not None:
                        logger.debug(
                            "ATP interface '%s' has parent '%s'. "
                            "ATP interfaces should have no parent relationships.",
                            typ.name,
                            typ.parent,
                        )
                    if typ.children:
                        logger.debug(
                            "ATP interface '%s' has children %s. "
                            "ATP interfaces should have no child relationships.",
                            typ.name,
                            typ.children,
                        )

    def _validate_subclasses(self, packages: List[AutosarPackage]) -> None:
        """Validate that subclasses attribute does not contain contradictions.

        Requirements:
            SWR_PARSER_00029: Subclasses Contradiction Validation

        This method validates that the `subclasses` attribute of each class
        does not contain any contradictions with the inheritance hierarchy
        defined by the `bases` and `parent` attributes.

        Validation Rules:
        - A subclass MUST have the parent class in its `bases` list
        - A subclass CANNOT be in the parent class's `bases` list (circular relationship)
        - A subclass CANNOT be in the parent class's parent's `bases` list (would be an ancestor)
        - A subclass CANNOT be the parent class itself

        Note: Missing subclasses are logged as warnings (not errors) to handle
        incomplete PDF specifications gracefully, similar to how missing base
        classes are handled in parent resolution.

        Args:
            packages: List of all packages to validate.
        """
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass) and typ.subclasses:
                    for subclass_name in typ.subclasses:
                        # Rule 1: Subclass must exist in the model
                        subclass = self._find_class_in_all_packages(subclass_name, packages)
                        if subclass is None:
                            logger.debug(
                                "Class '%s' is listed as a subclass of '%s' but does not exist in the model",
                                subclass_name,
                                typ.name,
                            )
                            continue

                        # Rule 2: Subclass must have this class in its bases list
                        if typ.name not in subclass.bases:
                            logger.debug(
                                "Class '%s' is listed as a subclass of '%s' but does not inherit from it (bases: %s)",
                                subclass_name,
                                typ.name,
                                subclass.bases,
                            )
                            continue

                        # Rule 3: Subclass cannot be in this class's bases list (circular)
                        if subclass_name in typ.bases:
                            logger.debug(
                                "Circular inheritance detected: '%s' is both a subclass and a base of '%s'",
                                subclass_name,
                                typ.name,
                            )
                            continue

                        # Rule 4: Subclass cannot be in this class's parent's bases list (ancestor)
                        if typ.parent:
                            parent_class = self._find_class_in_all_packages(typ.parent, packages)
                            if parent_class and subclass_name in parent_class.bases:
                                logger.debug(
                                    "Class '%s' is listed as a subclass of '%s' but is an ancestor (in bases of parent '%s')",
                                    subclass_name,
                                    typ.name,
                                    typ.parent,
                                )
                                continue

                        # Rule 5: Subclass cannot be the parent class itself
                        if typ.parent and subclass_name == typ.parent:
                            logger.debug(
                                "Class '%s' is listed as a subclass of '%s' but is the parent of '%s'",
                                subclass_name,
                                typ.name,
                                typ.name,
                            )
                            continue

    def _build_atp_ancestry_cache(self, packages: List[AutosarPackage]) -> Dict[str, Set[str]]:
        """Build a cache of ATP ancestry relationships from implements field.

        Requirements:
            SWR_PARSER_00034: ATP Class Parent Resolution from Implements

        Args:
            packages: List of packages to process.

        Returns:
            Dictionary mapping ATP class names to sets of all ATP ancestor class names.
        """
        # First, build a direct implements map (only ATP classes)
        direct_implements: Dict[str, List[str]] = {}
        for pkg in packages:
            for typ in pkg.types:
                if isinstance(typ, AutosarClass):
                    # Filter implements to only ATP classes (or ARObject)
                    atp_implements = [
                        impl for impl in typ.implements
                        if impl.startswith("Atp") or impl == "ARObject"
                    ]
                    direct_implements[typ.name] = atp_implements

        # Then, recursively collect all ATP ancestors for each class
        def collect_atp_ancestors(class_name: str, visited: Set[str]) -> Set[str]:
            """Recursively collect all ATP ancestors of a class."""
            if class_name in visited:
                return set()

            visited.add(class_name)
            ancestors = set()

            for impl_name in direct_implements.get(class_name, []):
                if impl_name != "ARObject":  # Don't treat ARObject as an ancestor
                    # Check if implemented ATP class exists in the model
                    impl_exists = False
                    for pkg in packages:
                        for typ in pkg.types:
                            if isinstance(typ, AutosarClass) and typ.name == impl_name:
                                impl_exists = True
                                break
                        if impl_exists:
                            break

                    if impl_exists:
                        ancestors.add(impl_name)
                        # Recursively collect ancestors of this implemented class
                        ancestors.update(collect_atp_ancestors(impl_name, visited))

            return ancestors

        cache: Dict[str, Set[str]] = {}
        for class_name in direct_implements.keys():
            cache[class_name] = collect_atp_ancestors(class_name, set())

        return cache

    def _resolve_atp_parent_references(self, packages: List[AutosarPackage]) -> None:
        """Resolve parent references for ATP classes from implements field.

        Requirements:
            SWR_PARSER_00034: ATP Class Parent Resolution from Implements

        For ATP classes (classes whose names start with "Atp"), the parent is
        determined from the implements field by considering only ATP classes
        (or ARObject) as potential parents. Non-ATP classes continue using the
        existing parent resolution from bases.

        Args:
            packages: List of all packages.
        """
        # Build ATP ancestry cache from implements field
        atp_ancestry_cache = self._build_atp_ancestry_cache(packages)

        # Set parent references for ATP classes from implements
        for pkg in packages:
            for typ in pkg.types:
                # Only process AutosarClass instances
                if not isinstance(typ, AutosarClass):
                    continue

                # Only process ATP classes (names starting with "Atp") with implements
                # (parent check removed since ATP resolution runs first)
                if not typ.name.startswith("Atp") or not typ.implements:
                    continue

                # Filter to only ATP classes and ARObject
                atp_candidates = [
                    impl for impl in typ.implements
                    if impl.startswith("Atp") or impl == "ARObject"
                ]

                if not atp_candidates:
                    continue

                # Find existing ATP candidates only (for ancestry analysis)
                existing_atp = []
                for candidate_name in atp_candidates:
                    candidate_class = self._find_class_in_all_packages(candidate_name, packages)
                    if candidate_class is not None:
                        existing_atp.append(candidate_name)

                if not existing_atp:
                    # No valid ATP candidates found, parent remains unchanged
                    continue

                # Ancestry-based parent selection:
                # Filter out candidates that are ancestors of other candidates
                # The direct parent is the candidate that is NOT an ancestor of any other candidate
                direct_parent = None
                for i, candidate_name in enumerate(existing_atp):
                    is_ancestor = False
                    for j, other_candidate_name in enumerate(existing_atp):
                        if i != j:
                            # Check if candidate_name is an ancestor of other_candidate_name
                            if candidate_name in atp_ancestry_cache.get(other_candidate_name, set()):
                                is_ancestor = True
                                break

                    if not is_ancestor:
                        # This candidate is not an ancestor of any other candidate
                        # It could be the direct parent
                        # If multiple candidates exist, choose the last one (backward compatibility)
                        direct_parent = candidate_name

                if direct_parent:
                    typ.parent = direct_parent