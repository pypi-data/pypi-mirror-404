"""AUTOSAR type model classes.

Requirements:
    SWR_MODEL_00001: AUTOSAR Class Representation
    SWR_MODEL_00002: AUTOSAR Class Name Validation
    SWR_MODEL_00003: AUTOSAR Class String Representation
    SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
    SWR_MODEL_00021: AUTOSAR Class Multi-Level Inheritance Hierarchy

    SWR_MODEL_00019: AUTOSAR Enumeration Type Representation
    SWR_MODEL_00022: AUTOSAR Class Parent Attribute
    SWR_MODEL_00024: AUTOSAR Primitive Type Representation
    SWR_MODEL_00026: AUTOSAR Class Children Attribute
        SWR_MODEL_00021: AUTOSAR Class Multi-Level Inheritance Hierarchy

    SWR_MODEL_00027: AUTOSAR Source Location Representation
    SWR_MODEL_00028: ATP Interface Implementation Tracking
    SWR_MODEL_00029: ATP Interface Pure Interface Validation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from autosar_pdf2txt.models.attributes import AutosarAttribute, AutosarEnumLiteral
from autosar_pdf2txt.models.base import AbstractAutosarBase, AutosarDocumentSource
from autosar_pdf2txt.models.enums import ATPType


@dataclass
class AutosarClass(AbstractAutosarBase):
    """Represents an AUTOSAR class.

    Requirements:
        SWR_MODEL_00001: AUTOSAR Class Representation
        SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
        SWR_MODEL_00022: AUTOSAR Class Parent Attribute
        SWR_MODEL_00026: AUTOSAR Class Children Attribute
        SWR_MODEL_00021: AUTOSAR Class Multi-Level Inheritance Hierarchy

        SWR_MODEL_00027: AUTOSAR Source Location Representation

    Inherits from AbstractAutosarBase to provide common type properties (name, package, note)
    and adds class-specific attributes including inheritance support and ATP markers.

    Attributes:
        name: The name of the class (inherited from AbstractAutosarBase).
        package: The full package path (inherited from AbstractAutosarBase).
        is_abstract: Whether the class is abstract.
        atp_type: ATP marker type enum indicating the AUTOSAR Tool Platform marker.
        attributes: Dictionary of AUTOSAR attributes (key: attribute name, value: AutosarAttribute).
        bases: List of base class names for inheritance tracking.
        parent: Name of the immediate parent class from the bases list (None for root classes).
        children: List of child class names that inherit from this class.
        subclasses: List of subclass names explicitly listed in the PDF.
        aggregated_by: List of class names that aggregate this class.
        implements: List of interface names (starting with "Atp") that this class implements.
        implemented_by: List of class names that implement this ATP interface (for ATP interfaces only).
        sources: List of source locations for the class definition itself (inherited).
        note: Optional documentation or comments (inherited from AbstractAutosarBase).

    Examples:
        >>> cls = AutosarClass("RunnableEntity", "M2::SWR", False)
        >>> abstract_cls = AutosarClass("InternalBehavior", "M2::SWR", True)
        >>> attr = AutosarAttribute("dataReadPort", "PPortPrototype", True)
        >>> cls_with_attr = AutosarClass("Component", "M2::SWR", False, attributes={"dataReadPort": attr})
        >>> cls_with_bases = AutosarClass("DerivedClass", "M2::SWR", False, bases=["BaseClass"])
        >>> cls_with_parent = AutosarClass("ChildClass", "M2::SWR", False, bases=["BaseClass"], parent="BaseClass")
        >>> cls_with_note = AutosarClass("MyClass", "M2::SWR", False, note="Documentation note")
        >>> cls_with_atp = AutosarClass("MyClass", "M2::SWR", False, atp_type=ATPType.ATP_VARIATION)
        >>> cls_with_children = AutosarClass("BaseClass", "M2::SWR", False, children=["DerivedClass"])
        >>> cls_with_aggregated_by = AutosarClass("MyClass", "M2::SWR", False, aggregated_by=["AggregatorClass"])
    """

    is_abstract: bool = False
    atp_type: ATPType = ATPType.NONE
    attributes: Dict[str, AutosarAttribute] = field(default_factory=dict)
    bases: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)
    subclasses: List[str] = field(default_factory=list)
    aggregated_by: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    implemented_by: List[str] = field(default_factory=list)

    def __init__(
        self,
        name: str,
        package: str,
        is_abstract: bool = False,
        atp_type: ATPType = ATPType.NONE,
        attributes: Optional[Dict[str, AutosarAttribute]] = None,
        bases: Optional[List[str]] = None,
        parent: Optional[str] = None,
        children: Optional[List[str]] = None,
        subclasses: Optional[List[str]] = None,
        aggregated_by: Optional[List[str]] = None,
        implements: Optional[List[str]] = None,
        implemented_by: Optional[List[str]] = None,
        note: Optional[str] = None,
        sources: Optional[List[AutosarDocumentSource]] = None,
    ) -> None:
        """Initialize the AUTOSAR class.

        Requirements:
            SWR_MODEL_00001: AUTOSAR Class Representation
            SWR_MODEL_00002: AUTOSAR Class Name Validation
            SWR_MODEL_00026: AUTOSAR Class Children Attribute
        SWR_MODEL_00021: AUTOSAR Class Multi-Level Inheritance Hierarchy

            SWR_MODEL_00027: AUTOSAR Source Location Representation

        Args:
            name: The name of the class.
            package: The full package path.
            is_abstract: Whether the class is abstract.
            atp_type: ATP marker type.
            attributes: Dictionary of attributes.
            bases: List of base class names.
            parent: Name of immediate parent class.
            children: List of child class names that inherit from this class.
            subclasses: List of subclass names explicitly listed in the PDF.
            aggregated_by: List of class names that aggregate this class.
            implements: List of interface names (starting with "Atp") that this class implements.
            implemented_by: List of class names that implement this ATP interface (for ATP interfaces only).
            note: Optional documentation.
            sources: Optional list of source locations for this class definition.

        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        super().__init__(name, package, note, sources)
        self.is_abstract = is_abstract
        self.atp_type = atp_type
        self.attributes = attributes or {}
        self.bases = bases or []
        self.parent = parent
        self.children = children or []
        self.subclasses = subclasses or []
        self.aggregated_by = aggregated_by or []
        self.implements = implements or []
        self.implemented_by = implemented_by or []

    def __str__(self) -> str:
        """Return string representation of the class.

        Requirements:
            SWR_MODEL_00003: AUTOSAR Class String Representation

        Returns:
            Class name with '(abstract)' suffix if abstract.
        """
        suffix = " (abstract)" if self.is_abstract else ""
        return f"{self.name}{suffix}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging.

        Requirements:
            SWR_MODEL_00003: AUTOSAR Class String Representation
            SWR_MODEL_00022: AUTOSAR Class Parent Attribute
            SWR_MODEL_00026: AUTOSAR Class Children Attribute
        SWR_MODEL_00021: AUTOSAR Class Multi-Level Inheritance Hierarchy

        """
        attrs_count = len(self.attributes)
        bases_count = len(self.bases)
        children_count = len(self.children)
        subclasses_count = len(self.subclasses)
        implements_count = len(self.implements)
        note_present = self.note is not None
        return (
            f"AutosarClass(name='{self.name}', is_abstract={self.is_abstract}, "
            f"atp_type={self.atp_type.name}, "
            f"attributes={attrs_count}, bases={bases_count}, parent={self.parent}, "
            f"children={children_count}, subclasses={subclasses_count}, implements={implements_count}, note={note_present})"
        )


@dataclass
class AutosarEnumeration(AbstractAutosarBase):
    """Represents an AUTOSAR enumeration type.

    Requirements:
        SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
        SWR_MODEL_00019: AUTOSAR Enumeration Type Representation

    Inherits from AbstractAutosarBase to provide common type properties (name, package, note)
    and adds enumeration-specific literals.

    Attributes:
        name: The name of the enumeration (inherited from AbstractAutosarBase).
        package: The full package path (inherited from AbstractAutosarBase).
        enumeration_literals: Immutable tuple of enumeration literal values.
        note: Optional documentation or comments (inherited from AbstractAutosarBase).

    Examples:
        >>> enum = AutosarEnumeration("EcucDestinationUriNestingContractEnum", "M2::ECUC")
        >>> enum_with_literals = AutosarEnumeration(
        ...     "MyEnum",
        ...     "M2::ECUC",
        ...     enumeration_literals=[
        ...         AutosarEnumLiteral("VALUE1", 0, "First value"),
        ...         AutosarEnumLiteral("VALUE2", 1, "Second value")
        ...     ]
        ... )
    """

    enumeration_literals: Tuple[AutosarEnumLiteral, ...] = field(default_factory=tuple)

    def __init__(
        self,
        name: str,
        package: str,
        enumeration_literals: Optional[List[AutosarEnumLiteral]] = None,
        note: Optional[str] = None,
        sources: Optional[List[AutosarDocumentSource]] = None,
    ) -> None:
        """Initialize the AUTOSAR enumeration.

        Requirements:
            SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
            SWR_MODEL_00019: AUTOSAR Enumeration Type Representation
            SWR_MODEL_00027: AUTOSAR Source Location Representation

        Args:
            name: The name of the enumeration.
            package: The full package path.
            enumeration_literals: List of enumeration literal values (converted to immutable tuple).
            note: Optional documentation.
            sources: Optional list of source locations for this enumeration definition.

        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        super().__init__(name, package, note, sources)
        # Convert to tuple for immutability
        self.enumeration_literals = tuple(enumeration_literals) if enumeration_literals else ()

    def __str__(self) -> str:
        """Return string representation of the enumeration.

        Requirements:
            SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
            SWR_MODEL_00019: AUTOSAR Enumeration Type Representation

        Returns:
            Enumeration name.
        """
        return f"{self.name}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging.

        Requirements:
            SWR_MODEL_00019: AUTOSAR Enumeration Type Representation
        """
        literals_count = len(self.enumeration_literals)
        note_present = self.note is not None
        return (
            f"AutosarEnumeration(name='{self.name}', "
            f"package='{self.package}', "
            f"enumeration_literals={literals_count}, note={note_present})"
        )


@dataclass
class AutosarPrimitive(AbstractAutosarBase):
    """Represents an AUTOSAR primitive type.

    Requirements:
        SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
        SWR_MODEL_00024: AUTOSAR Primitive Type Representation

    Inherits from AbstractAutosarBase to provide common type properties (name, package, note)
    and represents primitive data types in AUTOSAR.

    Attributes:
        name: The name of the primitive type (inherited from AbstractAutosarBase).
        package: The full package path (inherited from AbstractAutosarBase).
        note: Optional documentation or comments (inherited from AbstractAutosarBase).
        attributes: Dictionary of AUTOSAR attributes (key: attribute name, value: AutosarAttribute).

    Examples:
        >>> primitive = AutosarPrimitive("Limit", "M2::DataTypes")
        >>> primitive_with_note = AutosarPrimitive("Interval", "M2::DataTypes", note="Interval type")
        >>> attr = AutosarAttribute("intervalType", "String", False)
        >>> primitive_with_attr = AutosarPrimitive("Limit", "M2::DataTypes", attributes={"intervalType": attr})
    """

    attributes: Dict[str, AutosarAttribute] = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        package: str,
        attributes: Optional[Dict[str, AutosarAttribute]] = None,
        note: Optional[str] = None,
        sources: Optional[List[AutosarDocumentSource]] = None,
    ) -> None:
        """Initialize the AUTOSAR primitive type.

        Requirements:
            SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
            SWR_MODEL_00024: AUTOSAR Primitive Type Representation
            SWR_MODEL_00027: AUTOSAR Source Location Representation

        Args:
            name: The name of the primitive type.
            package: The full package path.
            attributes: Dictionary of attributes.
            note: Optional documentation.
            sources: Optional list of source locations for this primitive definition.

        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        super().__init__(name, package, note, sources)
        self.attributes = attributes or {}

    def __str__(self) -> str:
        """Return string representation of the primitive type.

        Requirements:
            SWR_MODEL_00018: AUTOSAR Type Abstract Base Class
            SWR_MODEL_00024: AUTOSAR Primitive Type Representation

        Returns:
            Primitive type name.
        """
        return f"{self.name}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging.

        Requirements:
            SWR_MODEL_00024: AUTOSAR Primitive Type Representation
        """
        attrs_count = len(self.attributes)
        note_present = self.note is not None
        return (
            f"AutosarPrimitive(name='{self.name}', "
            f"package='{self.package}', "
            f"attributes={attrs_count}, note={note_present})"
        )