"""Markdown writer for AUTOSAR packages and classes."""

import re
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Union

from autosar_pdf2txt.models import ATPType, AutosarClass, AutosarEnumeration, AutosarPackage


class MarkdownWriter:
    """Write AUTOSAR packages and classes to markdown format.

    Requirements:
        SWR_WRITER_00001: Markdown Writer Initialization
        SWR_WRITER_00005: Directory-Based Class File Output
        SWR_WRITER_00007: Class Hierarchy Output

    The output format uses asterisks (*) for hierarchy with indentation
    to show nesting levels. Each level adds 2 spaces of indentation.
    Classes and subpackages are written at the same indentation level:

    * TopLevelPackage
      * SubPackage
        * Class
        * AnotherClass

    Abstract classes are NOT marked in the main hierarchy output.
    The abstract status is only shown in individual class files.
    """

    def __init__(self) -> None:
        """Initialize the markdown writer.

        Requirements:
            SWR_WRITER_00001: Markdown Writer Initialization
        """

    def write_packages_to_files(
        self, packages: List[AutosarPackage], output_path: Optional[Union[str, Path]] = None, base_dir: Optional[Union[str, Path]] = None
    ) -> None:
        """Write packages to separate markdown files organized in directory structure.

        Requirements:
            SWR_WRITER_00005: Directory-Based Class File Output

        For each package:
        - Creates a directory corresponding to the package name
        - Creates a single markdown file for each class, named with the class name
        - Maintains nested directory structure for subpackages

        The root directory for the file structure is the same as the output markdown file location.
        If output_path is provided, the directory containing that file is used as the root.
        If base_dir is provided, it is used directly as the root directory.

        Args:
            packages: List of top-level AutosarPackage objects.
            output_path: Path to the output markdown file. The root directory will be
                the directory containing this file. Cannot be used with base_dir.
            base_dir: Base directory path where the package structure will be created.
                Cannot be used with output_path.

        Raises:
            OSError: If directory creation or file writing fails.
            ValueError: If both output_path and base_dir are provided, or if neither is provided,
                or if the path is empty.

        Examples:
            >>> writer = MarkdownWriter()
            >>> pkg = AutosarPackage(name="TestPackage")
            >>> pkg.add_class(AutosarClass("MyClass", False))
            >>> # Using output file path (root is dir of output.md)
            >>> writer.write_packages_to_files([pkg], output_path="/tmp/output.md")
            >>> # Using base directory directly
            >>> writer.write_packages_to_files([pkg], base_dir="/tmp/output")
        """
        if output_path is not None and base_dir is not None:
            raise ValueError("Cannot specify both output_path and base_dir")
        if output_path is None and base_dir is None:
            raise ValueError("Must specify either output_path or base_dir")
        if output_path is not None and not output_path:
            raise ValueError("output_path cannot be empty")
        if base_dir is not None and not base_dir:
            raise ValueError("base_dir cannot be empty")

        # Determine base path from output_path or base_dir
        if output_path is not None:
            output_file = Path(output_path)
            base_path = output_file.parent
        else:
            base_path = Path(base_dir)  # type: ignore

        for pkg in packages:
            self._write_package_to_files(pkg, base_path)

    def write_packages(self, packages: List[AutosarPackage]) -> str:
        """Write a list of top-level packages to markdown format.

        Requirements:
            SWR_WRITER_00002: Markdown Package Hierarchy Output
            SWR_WRITER_00004: Bulk Package Writing

        Args:
            packages: List of top-level AutosarPackage objects.

        Returns:
            Markdown formatted string representing the package hierarchy.

        Examples:
            >>> writer = MarkdownWriter()
            >>> pkg = AutosarPackage(name="TestPackage")
            >>> pkg.add_class(AutosarClass("MyClass", False))
            >>> markdown = writer.write_packages([pkg])
        """
        output = StringIO()
        for pkg in packages:
            self._write_package(pkg, [], 0, output)
        return output.getvalue()

    def write_class_hierarchy(self, root_classes: List[AutosarClass], all_classes: Optional[List[AutosarClass]] = None) -> str:
        """Write class hierarchy from root classes to markdown format.

        Requirements:
            SWR_WRITER_00007: Class Hierarchy Output

        Args:
            root_classes: List of root AutosarClass objects (classes with no bases).
            all_classes: Optional list of all AutosarClass objects. If not provided,
                only root classes will be written without descendants.

        Returns:
            Markdown formatted string representing the class hierarchy with proper indentation.
            Returns empty string if no root classes provided.

        Examples:
            >>> writer = MarkdownWriter()
            >>> root_cls = AutosarClass("RootClass", False)
            >>> markdown = writer.write_class_hierarchy([root_cls])
        """
        if not root_classes:
            return ""

        output = StringIO()
        output.write("## Class Hierarchy\n\n")

        # Build a mapping of class name to class for quick lookup
        all_classes_map = {}
        if all_classes:
            for cls in all_classes:
                all_classes_map[cls.name] = cls
        else:
            # If all_classes not provided, only use root classes
            for root_cls in root_classes:
                all_classes_map[root_cls.name] = root_cls

        # Write each root class and its descendants
        for root_cls in root_classes:
            self._write_class_hierarchy_recursive(root_cls, all_classes_map, [], 0, output)

        return output.getvalue()

    def _collect_classes_from_package(self, pkg: AutosarPackage) -> List[AutosarClass]:
        """Collect all AutosarClass objects from a package and its subpackages.

        Args:
            pkg: The package to collect classes from.

        Returns:
            List of all AutosarClass objects in the package hierarchy.
        """
        classes = []

        # Collect classes from this package
        for typ in pkg.types:
            if isinstance(typ, AutosarClass):
                classes.append(typ)

        # Recursively collect from subpackages
        for subpkg in pkg.subpackages:
            classes.extend(self._collect_classes_from_package(subpkg))

        return classes

    def _write_class_hierarchy_recursive(
        self,
        cls: AutosarClass,
        all_classes_map: Dict[str, AutosarClass],
        visited: List[str],
        level: int,
        output: StringIO,
    ) -> None:
        """Write a class and its descendants recursively to the output.

        Args:
            cls: The class to write.
            all_classes_map: Dictionary mapping class names to class objects.
            visited: List of visited class names to detect cycles.
            level: Current indentation level (0 for root classes).
            output: StringIO buffer to write to.
        """
        # Detect and handle cycles
        if cls.name in visited:
            indent = "  " * level
            output.write(f"{indent}* {cls.name} (cycle detected)\n")
            return

        # Write class line with abstract marker
        indent = "  " * level
        abstract_suffix = " (abstract)" if cls.is_abstract else ""
        output.write(f"{indent}* {cls.name}{abstract_suffix}\n")

        # Find subclasses (classes that have this class as parent)
        subclasses = []
        for other_cls in all_classes_map.values():
            if other_cls.parent == cls.name:
                subclasses.append(other_cls)

        # Sort subclasses by name for consistent output
        subclasses.sort(key=lambda c: c.name)

        # Recursively write subclasses
        for subclass in subclasses:
            self._write_class_hierarchy_recursive(
                subclass, all_classes_map, visited + [cls.name], level + 1, output
            )

    def _write_package(
        self,
        pkg: AutosarPackage,
        parent_path: List[str],
        level: int,
        output: StringIO,
    ) -> None:
        """Write a single package with its contents to the output.

        Requirements:
            SWR_WRITER_00002: Markdown Package Hierarchy Output

        Args:
            pkg: The package to write.
            parent_path: List of parent package names.
            level: Current indentation level (0 for top-level).
            output: StringIO buffer to write to.
        """
        # Write package line
        indent = "  " * level
        output.write(f"{indent}* {pkg.name}\n")

        # Write types (classes and enumerations) at one level deeper than their parent package
        for typ in pkg.types:
            if isinstance(typ, AutosarClass):
                self._write_class(typ, parent_path + [pkg.name], level + 1, output)
            elif isinstance(typ, AutosarEnumeration):
                self._write_enumeration(typ, parent_path + [pkg.name], level + 1, output)

        # Write subpackages at one level deeper than their parent package
        for subpkg in pkg.subpackages:
            self._write_package(subpkg, parent_path + [pkg.name], level + 1, output)

    def _write_class(
        self,
        cls: AutosarClass,
        parent_path: List[str],
        level: int,
        output: StringIO,
    ) -> None:
        """Write a single class to the output.

        Requirements:
            SWR_WRITER_00003: Markdown Class Output Format

        Args:
            cls: The class to write.
            parent_path: List of parent package names.
            level: Current indentation level.
            output: StringIO buffer to write to.
        """
        # Write class line with appropriate marker
        indent = "  " * level
        if cls.atp_type != ATPType.NONE:
            # ATP interface: use interface marker
            output.write(f"{indent}* {cls.name} (interface)\n")
        elif cls.is_abstract:
            # Abstract class: use abstract marker
            output.write(f"{indent}* {cls.name} (abstract)\n")
        else:
            # Concrete class: no marker
            output.write(f"{indent}* {cls.name}\n")

    def _write_package_to_files(self, pkg: AutosarPackage, parent_dir: Path, parent_path: Optional[List[str]] = None) -> None:
        """Write a package to directory structure with class files.

        Requirements:
            SWR_WRITER_00005: Directory-Based Class File Output

        Creates a directory for the package and writes each class to a separate
        markdown file within that directory. Recursively handles subpackages.

        Args:
            pkg: The package to write.
            parent_dir: Parent directory path where the package directory will be created.
            parent_path: List of parent package names for constructing full package path.

        Raises:
            OSError: If directory creation or file writing fails.
        """
        if parent_path is None:
            parent_path = []

        # Create directory for this package
        pkg_dir = parent_dir / pkg.name
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # Build full package path for this package
        full_package_path = parent_path + [pkg.name]
        package_path_str = "::".join(full_package_path)

        # Write each type to a separate file
        for typ in pkg.types:
            if isinstance(typ, AutosarClass):
                self._write_class_to_file(typ, pkg_dir, package_path_str)
            elif isinstance(typ, AutosarEnumeration):
                self._write_enumeration_to_file(typ, pkg_dir, package_path_str)

        # Recursively write subpackages
        for subpkg in pkg.subpackages:
            self._write_package_to_files(subpkg, pkg_dir, full_package_path)

    def _write_class_to_file(self, cls: AutosarClass, pkg_dir: Path, package_path_str: str) -> None:
        """Write a single class to its own markdown file.

        Requirements:
            SWR_WRITER_00005: Directory-Based Class File Output
            SWR_WRITER_00006: Individual Class Markdown File Content
            SWR_MODEL_00027: AUTOSAR Source Location Representation
            SWR_WRITER_00008: Markdown Source Information Output


        The markdown file contains:
        - Package path (full parent hierarchy)
        - Type indicator (Abstract or Concrete)
        - Parent class name (if parent is not None)
        - ATP type (if any ATP flags are present)
        - Base classes (if any)
        - Subclasses (if any)
        - Source location (if available)
        - Children classes (if any)
        - Note as description (if present)
        - Attributes list (if any)

        Args:
            cls: The class to write.
            pkg_dir: Directory where the class file will be created.
            package_path_str: Full package path (e.g., "AUTOSAR::DataTypes::ImplementationDataTypes").

        Raises:
            OSError: If file writing fails.
        """
        output = StringIO()
        
        # Determine class type indicator
        if cls.atp_type != ATPType.NONE:
            # ATP interface
            type_indicator = " (interface)"
        elif cls.is_abstract:
            type_indicator = " (abstract)"
        else:
            type_indicator = ""
        
        output.write(f"# {cls.name}{type_indicator}\n\n")

        # Write package information
        output.write("## Package\n\n")
        output.write(f"{package_path_str}\n\n")

        # Write type indicator
        output.write("## Type\n\n")
        if cls.atp_type != ATPType.NONE:
            output.write("ATP Interface\n\n")
        else:
            output.write(f"{'Abstract' if cls.is_abstract else 'Concrete'}\n\n")

        # Write parent if present (NOT for ATP interfaces)
        if cls.parent and cls.atp_type == ATPType.NONE:
            output.write("## Parent\n\n")
            output.write(f"{cls.parent}\n\n")

        # Write ATP type section if ATP type is not NONE
        if cls.atp_type != ATPType.NONE:
            output.write("## ATP Type\n\n")
            if cls.atp_type == ATPType.ATP_VARIATION:
                output.write("* atpVariation\n")
            elif cls.atp_type == ATPType.ATP_MIXED_STRING:
                output.write("* atpMixedString\n")
            elif cls.atp_type == ATPType.ATP_MIXED:
                output.write("* atpMixed\n")
            elif cls.atp_type == ATPType.ATP_PROTO:
                output.write("* atpPrototype\n")
            output.write("\n")

        # Write base classes if present (NOT for ATP interfaces)
        if cls.bases and cls.atp_type == ATPType.NONE:
            output.write("## Base Classes\n\n")
            for base in cls.bases:
                output.write(f"* {base}\n")
            output.write("\n")

        # Write implements if present (NOT for ATP interfaces)
        if cls.implements and cls.atp_type == ATPType.NONE:
            output.write("## Implements\n\n")
            for interface in cls.implements:
                output.write(f"* {interface}\n")
            output.write("\n")

        # Write implemented by if present (ONLY for ATP interfaces)
        if cls.implemented_by and cls.atp_type != ATPType.NONE:
            output.write("## Implemented By\n\n")
            for implementer in sorted(cls.implemented_by):
                output.write(f"* {implementer}\n")
            output.write("\n")

        # Write subclasses if present
        if cls.subclasses:
            output.write("## Subclasses\n\n")
            for subclass in sorted(cls.subclasses):
                output.write(f"* {subclass}\n")
            output.write("\n")

        # Write source section if available
        if cls.sources:
            output.write("## Document Source\n\n")
            # Table header with clickable source links
            output.write("| PDF File | Page | AUTOSAR Standard | Standard Release |\n")
            output.write("|----------|------|------------------|------------------|\n")
            # Sort sources by PDF filename
            for source in sorted(cls.sources, key=lambda s: s.pdf_file):
                autosar_standard = source.autosar_standard if source.autosar_standard else "-"
                standard_release = source.standard_release if source.standard_release else "-"
                # Create clickable link to PDF with page anchor
                # Format: [filename#page=N](filename.pdf#page=N)
                source_link = f"[{source.pdf_file}#page={source.page_number}]({source.pdf_file}#page={source.page_number})"
                output.write(f"| {source_link} | {source.page_number} | {autosar_standard} | {standard_release} |\n")
            output.write("\n")

        # Write children if present (NOT for ATP interfaces)
        if cls.children and cls.atp_type == ATPType.NONE:
            output.write("## Children\n\n")
            for child in sorted(cls.children):
                output.write(f"* {child}\n")
            output.write("\n")

        # Write note if present
        if cls.note:
            output.write("## Note\n\n")
            output.write(f"{cls.note}\n\n")

        # Write attributes if present
        if cls.attributes:
            output.write("## Attributes\n\n")
            # Table header
            output.write("| Attribute | Type | Mult. | Kind | Note |\n")
            output.write("|----------|------|-------|------|------|\n")
            # Table rows
            for attr_name, attr in cls.attributes.items():
                ref_suffix = " (ref)" if attr.is_ref else ""
                output.write(f"| {attr_name}{ref_suffix} | {attr.type} | {attr.multiplicity} | {attr.kind.value} | {attr.note} |\n")
            output.write("\n")

        # Write to file with sanitized filename
        sanitized_name = self._sanitize_filename(cls.name)
        file_path = pkg_dir / f"{sanitized_name}.md"
        file_path.write_text(output.getvalue(), encoding="utf-8")

    def _write_enumeration(
        self,
        enum: AutosarEnumeration,
        parent_path: List[str],
        level: int,
        output: StringIO,
    ) -> None:
        """Write an enumeration to the output stream.

        Requirements:
            SWR_MODEL_00019: AUTOSAR Enumeration Type Representation
            SWR_MODEL_00020: AUTOSAR Package Type Support

        Args:
            enum: The enumeration to write.
            parent_path: List of parent package names.
            level: Current indentation level.
            output: StringIO buffer to write to.
        """
        indent = "  " * level
        output.write(f"{indent}* {enum.name}\n")

    def _write_enumeration_to_file(
        self, enum: AutosarEnumeration, pkg_dir: Path, package_path_str: str
    ) -> None:
        """Write a single enumeration to its own markdown file.

        Requirements:
            SWR_WRITER_00006: Individual Class Markdown File Content
            SWR_WRITER_00009: Enumeration Literal Table Output Format
            SWR_MODEL_00019: AUTOSAR Enumeration Type Representation
            SWR_MODEL_00027: AUTOSAR Source Location Representation
            SWR_WRITER_00008: Markdown Source Information Output


        Args:
            enum: The enumeration to write.
            pkg_dir: Directory path for the package.
            package_path_str: Full package path (e.g., "AUTOSAR::DataTypes::ImplementationDataTypes").

        Raises:
            OSError: If file writing fails.
        """
        output = StringIO()

        # Write package name
        output.write(f"# Package: {package_path_str}\n\n")

        # Write enumeration name
        output.write("## Enumeration\n\n")
        output.write(f"**{enum.name}**\n\n")

        # Write source if available
        if enum.sources:
            output.write("## Document Source\n\n")
            # Table header with clickable source links
            output.write("| PDF File | Page | AUTOSAR Standard | Standard Release |\n")
            output.write("|----------|------|------------------|------------------|\n")
            # Sort sources by PDF filename
            for source in sorted(enum.sources, key=lambda s: s.pdf_file):
                autosar_standard = source.autosar_standard if source.autosar_standard else "-"
                standard_release = source.standard_release if source.standard_release else "-"
                # Create clickable link to PDF with page anchor
                # Format: [filename#page=N](filename.pdf#page=N)
                source_link = f"[{source.pdf_file}#page={source.page_number}]({source.pdf_file}#page={source.page_number})"
                output.write(f"| {source_link} | {source.page_number} | {autosar_standard} | {standard_release} |\n")
            output.write("\n")

        # Write note if present
        if enum.note:
            output.write("## Note\n\n")
            output.write(f"{enum.note}\n\n")

        # Write enumeration literals if present
        if enum.enumeration_literals:
            output.write("## Enumeration Literals\n\n")
            # Write table header (Name | Value | Description)
            output.write("| Name | Value | Description |\n")
            output.write("|------|-------|-------------|\n")
            # Write each literal as a table row
            for literal in enum.enumeration_literals:
                # Use literal.value for the Value column
                value = literal.value if literal.value is not None else "-"
                # Build description with original description and merged tags
                description_parts = []
                if literal.description:
                    description_parts.append(literal.description)
                if literal.tags:
                    # Merge all tags as "Tags: key=value, key2=value2" on new line
                    tag_strings = [f"{k}={v}" for k, v in sorted(literal.tags.items())]
                    description_parts.append(f"<br>Tags: {', '.join(tag_strings)}")
                description = "".join(description_parts) if description_parts else "-"
                # Write table row
                output.write(f"| {literal.name} | {value} | {description} |\n")
            output.write("\n")

        # Write to file with sanitized filename
        sanitized_name = self._sanitize_filename(enum.name)
        file_path = pkg_dir / f"{sanitized_name}.md"
        file_path.write_text(output.getvalue(), encoding="utf-8")

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a class name for use as a filename.

        Requirements:
            SWR_WRITER_00005: Directory-Based Class File Output

        Removes or replaces characters that are invalid in file paths on Windows
        and other operating systems. This ensures that class names with special
        characters can still be written to the filesystem.

        Args:
            name: The class name to sanitize.

        Returns:
            A sanitized version of the name safe for use in file paths.

        Examples:
            >>> writer = MarkdownWriter()
            >>> writer._sanitize_filename("<<atpVariation>>Class")
            '__atpVariation__Class'
            >>> writer._sanitize_filename("NormalClass")
            'NormalClass'
        """
        # Replace invalid filename characters with underscores
        # Invalid chars: < > : " / \ | ? * and control characters
        # Note: using \\ in pattern to match literal backslash
        invalid_chars = r'[<>:"/|?*\x00-\x1f]'
        # First handle backslash separately since it's tricky in regex
        sanitized = name.replace('\\', '_')
        # Then replace all other invalid characters
        sanitized = re.sub(invalid_chars, '_', sanitized)

        # Ensure name doesn't start or end with spaces or dots
        sanitized = sanitized.strip('. ')

        # If the name becomes empty or only underscores, use a default
        if not sanitized or sanitized.replace('_', '') == '':
            sanitized = 'UnnamedClass'

        return sanitized
