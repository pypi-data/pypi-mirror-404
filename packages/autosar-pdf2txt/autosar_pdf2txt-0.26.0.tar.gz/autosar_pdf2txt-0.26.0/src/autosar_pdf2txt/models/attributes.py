"""AUTOSAR attribute model classes.

Requirements:
    SWR_MODEL_00010: AUTOSAR Attribute Representation
    SWR_MODEL_00011: AUTOSAR Attribute Name Validation
    SWR_MODEL_00012: AUTOSAR Attribute Type Validation
    SWR_MODEL_00013: AUTOSAR Attribute String Representation
    SWR_MODEL_00014: AUTOSAR Enumeration Literal Representation
    SWR_MODEL_00015: AUTOSAR Enumeration Literal Name Validation
    SWR_MODEL_00016: AUTOSAR Enumeration Literal String Representation
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from autosar_pdf2txt.models.enums import AttributeKind


@dataclass
class AutosarEnumLiteral:
    """Represents an enumeration literal value.

    Requirements:
        SWR_MODEL_00014: AUTOSAR Enumeration Literal Representation

    Attributes:
        name: The name of the enumeration literal.
        index: The optional index of the literal (e.g., atp.EnumerationLiteralIndex=0).
        description: Optional description of the literal.
        tags: Optional dictionary of metadata tags (e.g., xml.name, atp.*).
        value: Optional value of the literal (extracted from xml.name tag).

    Examples:
        >>> literal = AutosarEnumLiteral("leafOfTargetContainer", 0, "Elements directly owned by target container")
        >>> literal_no_index = AutosarEnumLiteral("targetContainer", description="Target container")
        >>> literal_with_tags = AutosarEnumLiteral("iso11992_4", description="ISO 11992-4 DTC format", tags={"xml.name": "ISO-11992-4"})
        >>> literal_with_value = AutosarEnumLiteral("iso11992_4", description="ISO 11992-4 DTC format", value="ISO-11992-4")
    """

    name: str
    index: Optional[int] = None
    description: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    value: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the literal fields.

        Requirements:
            SWR_MODEL_00015: AUTOSAR Enumeration Literal Name Validation

        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Enumeration literal name cannot be empty")

    def __str__(self) -> str:
        """Return string representation of the literal.

        Requirements:
            SWR_MODEL_00016: AUTOSAR Enumeration Literal String Representation

        Returns:
            Literal name with index suffix if present.
        """
        suffix = f" (index={self.index})" if self.index is not None else ""
        tags_suffix = f" [tags: {len(self.tags)}]" if self.tags else ""
        value_suffix = f" [value: {self.value}]" if self.value is not None else ""
        return f"{self.name}{suffix}{tags_suffix}{value_suffix}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging.

        Requirements:
            SWR_MODEL_00016: AUTOSAR Enumeration Literal String Representation
        """
        return (
            f"AutosarEnumLiteral(name='{self.name}', "
            f"index={self.index}, description={self.description is not None}, "
            f"tags={len(self.tags)}, value={self.value})"
        )


@dataclass
class AutosarAttribute:
    """Represents an AUTOSAR class attribute.

    Requirements:
        SWR_MODEL_00010: AUTOSAR Attribute Representation

    Attributes:
        name: The name of the attribute.
        type: The data type of the attribute.
        is_ref: Whether the attribute is a reference type.
        multiplicity: The multiplicity of the attribute (e.g., "0..1", "*", "0..*").
        kind: The kind of attribute (attr or aggr).
        note: The description or note for the attribute.

    Examples:
        >>> attr = AutosarAttribute("dataReadPort", "PPortPrototype", True, "0..1", AttributeKind.ATTR, "Data read port")
        >>> non_ref_attr = AutosarAttribute("id", "uint32", False, "0..1", AttributeKind.ATTR, "Unique identifier")
    """

    name: str
    type: str
    is_ref: bool
    multiplicity: str
    kind: AttributeKind
    note: str

    def __post_init__(self) -> None:
        """Validate the attribute fields.

        Requirements:
            SWR_MODEL_00011: AUTOSAR Attribute Name Validation
            SWR_MODEL_00012: AUTOSAR Attribute Type Validation

        Raises:
            ValueError: If name or type is empty or contains only whitespace.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Attribute name cannot be empty")
        if not self.type or not self.type.strip():
            raise ValueError("Attribute type cannot be empty")

    def __str__(self) -> str:
        """Return string representation of the attribute.

        Requirements:
            SWR_MODEL_00013: AUTOSAR Attribute String Representation

        Returns:
            Attribute name and type with '(ref)' suffix if reference type,
            plus multiplicity, kind, and note.
        """
        ref_suffix = " (ref)" if self.is_ref else ""
        return f"{self.name}: {self.type}{ref_suffix} [{self.multiplicity}] ({self.kind.value}) - {self.note}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging.

        Requirements:
            SWR_MODEL_00013: AUTOSAR Attribute String Representation
        """
        return (
            f"AutosarAttribute(name='{self.name}', type='{self.type}', "
            f"is_ref={self.is_ref}, multiplicity='{self.multiplicity}', "
            f"kind={self.kind}, note='{self.note}')"
        )