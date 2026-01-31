"""AUTOSAR container model classes.

Requirements:
    SWR_MODEL_00004: AUTOSAR Package Representation
    SWR_MODEL_00005: AUTOSAR Package Name Validation
    SWR_MODEL_00006: Add Class to Package
    SWR_MODEL_00007: Add Subpackage to Package
    SWR_MODEL_00008: Query Package Contents
    SWR_MODEL_00009: Package String Representation
    SWR_MODEL_00020: AUTOSAR Package Type Support
    SWR_MODEL_00023: AUTOSAR Document Representation
    SWR_MODEL_00025: AUTOSAR Package Primitive Type Support
    SWR_MODEL_00028: Query Classes Implementing Interface
    SWR_MODEL_00029: Query Interfaces for Class
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union

from autosar_pdf2txt.models.enums import ATPType
from autosar_pdf2txt.models.types import AutosarClass, AutosarEnumeration, AutosarPrimitive


@dataclass
class AutosarPackage:
    """Represents an AUTOSAR package containing types and subpackages.

    Requirements:
        SWR_MODEL_00004: AUTOSAR Package Representation
        SWR_MODEL_00020: AUTOSAR Package Type Support
        SWR_MODEL_00025: AUTOSAR Package Primitive Type Support

    Attributes:
        name: The name of the package.
        types: List of types (AutosarClass, AutosarEnumeration, or AutosarPrimitive) in this package.
        subpackages: List of subpackages in this package.

    Examples:
        >>> pkg = AutosarPackage("BswBehavior")
        >>> pkg.add_type(AutosarClass("BswInternalBehavior", False))
        >>> pkg.add_type(AutosarEnumeration("MyEnum", False))
        >>> pkg.add_type(AutosarPrimitive("Limit", "M2::DataTypes"))
        >>> subpkg = AutosarPackage("SubBehavior")
        >>> pkg.add_subpackage(subpkg)
    """

    name: str
    types: List[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]] = field(default_factory=list)
    subpackages: List["AutosarPackage"] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the package fields.

        Requirements:
            SWR_MODEL_00005: AUTOSAR Package Name Validation

        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Package name cannot be empty")

    def add_type(self, typ: Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]) -> None:
        """Add a type (class, enumeration, or primitive) to the package.

        Requirements:
            SWR_MODEL_00006: Add Class to Package
            SWR_MODEL_00020: AUTOSAR Package Type Support
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support

        Args:
            typ: The AutosarClass, AutosarEnumeration, or AutosarPrimitive to add.

        Note:
            If a type with the same name already exists, the sources are merged.
            This allows tracking when a type is defined in multiple PDFs.
        """
        for existing_type in self.types:
            if existing_type.name == typ.name:
                # Merge sources from the duplicate type
                existing_sources = {str(s) for s in existing_type.sources}
                new_sources = {str(s) for s in typ.sources}
                added_sources = new_sources - existing_sources

                if added_sources:
                    # Add only non-duplicate sources
                    for source in typ.sources:
                        if str(source) in added_sources:
                            existing_type.sources.append(source)
                return
        self.types.append(typ)

    def add_class(self, cls: AutosarClass) -> None:
        """Add a class to the package.

        Requirements:
            SWR_MODEL_00006: Add Class to Package
            SWR_MODEL_00020: AUTOSAR Package Type Support

        Args:
            cls: The AutosarClass to add.

        Raises:
            ValueError: If a class with the same name already exists.

        Note:
            This method is maintained for backward compatibility and delegates to add_type().
        """
        self.add_type(cls)

    def add_enumeration(self, enum: AutosarEnumeration) -> None:
        """Add an enumeration to the package.

        Requirements:
            SWR_MODEL_00020: AUTOSAR Package Type Support

        Args:
            enum: The AutosarEnumeration to add.

        Raises:
            ValueError: If an enumeration with the same name already exists.
        """
        self.add_type(enum)

    def add_subpackage(self, pkg: "AutosarPackage") -> None:
        """Add a subpackage to this package.

        Requirements:
            SWR_MODEL_00007: Add Subpackage to Package

        Args:
            pkg: The AutosarPackage to add as a subpackage.

        Raises:
            ValueError: If a subpackage with the same name already exists.
        """
        pkg_names = {p.name for p in self.subpackages}
        if pkg.name in pkg_names:
            raise ValueError(f"Subpackage '{pkg.name}' already exists in package '{self.name}'")
        self.subpackages.append(pkg)

    def get_type(self, name: str) -> Optional[Union[AutosarClass, AutosarEnumeration, AutosarPrimitive]]:
        """Get a type (class, enumeration, or primitive) by name.

        Requirements:
            SWR_MODEL_00008: Query Package Contents
            SWR_MODEL_00020: AUTOSAR Package Type Support
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support

        Args:
            name: The name of the type to find.

        Returns:
            The AutosarClass, AutosarEnumeration, or AutosarPrimitive if found, None otherwise.
        """
        for typ in self.types:
            if typ.name == name:
                return typ
        return None

    def get_class(self, name: str) -> Optional[AutosarClass]:
        """Get a class by name.

        Requirements:
            SWR_MODEL_00008: Query Package Contents
            SWR_MODEL_00020: AUTOSAR Package Type Support

        Args:
            name: The name of the class to find.

        Returns:
            The AutosarClass if found, None otherwise.

        Note:
            This method is maintained for backward compatibility and returns only AutosarClass instances.
        """
        for typ in self.types:
            if isinstance(typ, AutosarClass) and typ.name == name:
                return typ
        return None

    def get_enumeration(self, name: str) -> Optional[AutosarEnumeration]:
        """Get an enumeration by name.

        Requirements:
            SWR_MODEL_00020: AUTOSAR Package Type Support

        Args:
            name: The name of the enumeration to find.

        Returns:
            The AutosarEnumeration if found, None otherwise.
        """
        for typ in self.types:
            if isinstance(typ, AutosarEnumeration) and typ.name == name:
                return typ
        return None

    def add_primitive(self, primitive: AutosarPrimitive) -> None:
        """Add a primitive type to the package.

        Requirements:
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support

        Args:
            primitive: The AutosarPrimitive to add.

        Raises:
            ValueError: If a primitive type with the same name already exists.
        """
        self.add_type(primitive)

    def get_primitive(self, name: str) -> Optional[AutosarPrimitive]:
        """Get a primitive type by name.

        Requirements:
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support

        Args:
            name: The name of the primitive type to find.

        Returns:
            The AutosarPrimitive if found, None otherwise.
        """
        for typ in self.types:
            if isinstance(typ, AutosarPrimitive) and typ.name == name:
                return typ
        return None

    def get_subpackage(self, name: str) -> Optional["AutosarPackage"]:
        """Get a subpackage by name.

        Requirements:
            SWR_MODEL_00008: Query Package Contents

        Args:
            name: The name of the subpackage to find.

        Returns:
            The AutosarPackage if found, None otherwise.
        """
        for pkg in self.subpackages:
            if pkg.name == name:
                return pkg
        return None

    def has_type(self, name: str) -> bool:
        """Check if a type (class, enumeration, or primitive) exists in the package.

        Requirements:
            SWR_MODEL_00008: Query Package Contents
            SWR_MODEL_00020: AUTOSAR Package Type Support
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support

        Args:
            name: The name of the type to check.

        Returns:
            True if the type exists, False otherwise.
        """
        return any(typ.name == name for typ in self.types)

    def get_classes_implementing_interface(self, interface_name: str) -> List[AutosarClass]:
        """Get all classes in this package that implement a specific ATP interface.

        Requirements:
            SWR_MODEL_00028: Query Classes Implementing Interface

        Args:
            interface_name: Name of the ATP interface to filter by.

        Returns:
            List of classes implementing the specified interface.
        """
        implementing_classes = []
        for typ in self.types:
            if isinstance(typ, AutosarClass):
                if interface_name in typ.implements:
                    implementing_classes.append(typ)
        return implementing_classes

    def get_interfaces_for_class(self, class_name: str) -> List[AutosarClass]:
        """Get all ATP interfaces implemented by a specific class.

        Requirements:
            SWR_MODEL_00029: Query Interfaces for Class

        Args:
            class_name: Name of the class to get interfaces for.

        Returns:
            List of ATP interface classes implemented by the specified class.
        """
        cls = self.get_class(class_name)
        if not cls:
            return []

        interfaces = []
        for interface_name in cls.implements:
            # Search for interface in this package and subpackages
            interface = self._find_interface_recursive(interface_name)
            if interface:
                interfaces.append(interface)
        return interfaces

    def _find_interface_recursive(self, interface_name: str) -> Optional[AutosarClass]:
        """Recursively search for an ATP interface by name.

        Args:
            interface_name: Name of the ATP interface to find.

        Returns:
            The ATP interface class or None if not found.
        """
        # Check this package
        interface = self.get_class(interface_name)
        if interface and interface.atp_type != ATPType.NONE:
            return interface

        # Check subpackages
        for subpkg in self.subpackages:
            result = subpkg._find_interface_recursive(interface_name)
            if result:
                return result

        return None

    def has_class(self, name: str) -> bool:
        """Check if a class exists in the package.

        Requirements:
            SWR_MODEL_00008: Query Package Contents
            SWR_MODEL_00020: AUTOSAR Package Type Support

        Args:
            name: The name of the class to check.

        Returns:
            True if the class exists, False otherwise.

        Note:
            This method is maintained for backward compatibility and checks only for AutosarClass instances.
        """
        return any(isinstance(typ, AutosarClass) and typ.name == name for typ in self.types)

    def has_enumeration(self, name: str) -> bool:
        """Check if an enumeration exists in the package.

        Requirements:
            SWR_MODEL_00020: AUTOSAR Package Type Support

        Args:
            name: The name of the enumeration to check.

        Returns:
            True if the enumeration exists, False otherwise.
        """
        return any(isinstance(typ, AutosarEnumeration) and typ.name == name for typ in self.types)

    def has_primitive(self, name: str) -> bool:
        """Check if a primitive type exists in the package.

        Requirements:
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support

        Args:
            name: The name of the primitive type to check.

        Returns:
            True if the primitive type exists, False otherwise.
        """
        return any(isinstance(typ, AutosarPrimitive) and typ.name == name for typ in self.types)

    def has_subpackage(self, name: str) -> bool:
        """Check if a subpackage exists in the package.

        Requirements:
            SWR_MODEL_00008: Query Package Contents

        Args:
            name: The name of the subpackage to check.

        Returns:
            True if the subpackage exists, False otherwise.
        """
        return any(pkg.name == name for pkg in self.subpackages)

    def __str__(self) -> str:
        """Return string representation of the package.

        Requirements:
            SWR_MODEL_00009: Package String Representation
            SWR_MODEL_00020: AUTOSAR Package Type Support
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support
        """
        parts = [f"Package '{self.name}'"]
        if self.types:
            parts.append(f"{len(self.types)} types")
        if self.subpackages:
            parts.append(f"{len(self.subpackages)} subpackages")
        return " (".join(parts) + ")"

    def __repr__(self) -> str:
        """Return detailed representation for debugging.

        Requirements:
            SWR_MODEL_00009: Package String Representation
            SWR_MODEL_00020: AUTOSAR Package Type Support
            SWR_MODEL_00025: AUTOSAR Package Primitive Type Support
        """
        return (
            f"AutosarPackage(name='{self.name}', "
            f"types={len(self.types)}, subpackages={len(self.subpackages)})"
        )


@dataclass
class AutosarDoc:
    """Represents an AUTOSAR document containing packages and root classes.

    Requirements:
        SWR_MODEL_00023: AUTOSAR Document Representation
        SWR_MODEL_00030: Query Classes Implementing Interface (Document Level)
        SWR_MODEL_00031: Query Interface Implementers

    This class encapsulates the complete AUTOSAR model structure including
    the package hierarchy and root classes (classes with no bases).

    Attributes:
        packages: List of top-level AutosarPackage objects.
        root_classes: List of root AutosarClass objects (classes with empty bases).

    Examples:
        >>> doc = AutosarDoc(packages=[pkg1, pkg2], root_classes=[root_cls])
    """

    packages: List[AutosarPackage]
    root_classes: List[AutosarClass]

    def __post_init__(self) -> None:
        """Validate the document fields.

        Requirements:
            SWR_MODEL_00023: AUTOSAR Document Representation

        Raises:
            ValueError: If packages or root_classes contain duplicate names.
        """
        # Check for duplicate package names
        pkg_names = [pkg.name for pkg in self.packages]
        if len(pkg_names) != len(set(pkg_names)):
            raise ValueError("Duplicate package names found in packages")

        # Check for duplicate root class names
        root_cls_names = [cls.name for cls in self.root_classes]
        if len(root_cls_names) != len(set(root_cls_names)):
            raise ValueError("Duplicate root class names found in root_classes")

    def get_package(self, name: str) -> Optional[AutosarPackage]:
        """Get a package by name.

        Requirements:
            SWR_MODEL_00023: AUTOSAR Document Representation

        Args:
            name: The name of the package to find.

        Returns:
            The AutosarPackage if found, None otherwise.
        """
        for pkg in self.packages:
            if pkg.name == name:
                return pkg
        return None

    def get_root_class(self, name: str) -> Optional[AutosarClass]:
        """Get a root class by name.

        Requirements:
            SWR_MODEL_00023: AUTOSAR Document Representation

        Args:
            name: The name of the root class to find.

        Returns:
            The AutosarClass if found, None otherwise.
        """
        for cls in self.root_classes:
            if cls.name == name:
                return cls
        return None

    def get_classes_implementing_interface(self, interface_name: str) -> List[AutosarClass]:
        """Get all classes in the document that implement a specific ATP interface.

        Requirements:
            SWR_MODEL_00030: Query Classes Implementing Interface (Document Level)

        Args:
            interface_name: Name of the ATP interface to filter by.

        Returns:
            List of classes implementing the specified interface.
        """
        implementing_classes = []
        for pkg in self.packages:
            implementing_classes.extend(
                pkg.get_classes_implementing_interface(interface_name)
            )
        return implementing_classes

    def get_interface_implementers(self, interface_name: str) -> List[AutosarClass]:
        """Get all classes that implement a specific ATP interface.

        This method uses the interface's implemented_by attribute for O(1) lookup.

        Requirements:
            SWR_MODEL_00031: Query Interface Implementers

        Args:
            interface_name: Name of the ATP interface.

        Returns:
            List of classes implementing the interface.
        """
        # Find the interface
        for pkg in self.packages:
            interface = pkg.get_class(interface_name)
            if interface and interface.atp_type != ATPType.NONE:
                # Look up implementers using the implemented_by attribute
                implementers = []
                for implementer_name in interface.implemented_by:
                    cls = self.get_class_by_name(implementer_name)
                    if cls:
                        implementers.append(cls)
                return implementers
        return []

    def get_class_by_name(self, class_name: str) -> Optional[AutosarClass]:
        """Get a class by name from any package.

        Args:
            class_name: Name of the class to find.

        Returns:
            The AutosarClass if found, None otherwise.
        """
        for pkg in self.packages:
            cls = pkg.get_class(class_name)
            if cls:
                return cls
            # Check subpackages recursively
            for subpkg in pkg.subpackages:
                cls = self._find_class_recursive(subpkg, class_name)
                if cls:
                    return cls
        return None

    def _find_class_recursive(self, pkg: AutosarPackage, class_name: str) -> Optional[AutosarClass]:
        """Recursively search for a class in a package.

        Args:
            pkg: The package to search.
            class_name: Name of the class to find.

        Returns:
            The AutosarClass if found, None otherwise.
        """
        cls = pkg.get_class(class_name)
        if cls:
            return cls

        for subpkg in pkg.subpackages:
            cls = self._find_class_recursive(subpkg, class_name)
            if cls:
                return cls

        return None

    def __str__(self) -> str:
        """Return string representation of the document.

        Requirements:
            SWR_MODEL_00023: AUTOSAR Document Representation

        Returns:
            Document summary with package and root class counts.
        """
        return f"AutosarDoc({len(self.packages)} packages, {len(self.root_classes)} root classes)"

    def __repr__(self) -> str:
        """Return detailed representation for debugging.

        Requirements:
            SWR_MODEL_00023: AUTOSAR Document Representation
        """
        return (
            f"AutosarDoc(packages={len(self.packages)}, root_classes={len(self.root_classes)})"
        )