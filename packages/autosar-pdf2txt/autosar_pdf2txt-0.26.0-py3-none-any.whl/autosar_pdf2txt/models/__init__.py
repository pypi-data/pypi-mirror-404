"""AUTOSAR data models for packages and classes."""

# Export enumerations
from autosar_pdf2txt.models.enums import ATPType, AttributeKind

# Export base class
from autosar_pdf2txt.models.base import AbstractAutosarBase, AutosarDocumentSource

# Export attribute classes
from autosar_pdf2txt.models.attributes import AutosarAttribute, AutosarEnumLiteral

# Export type classes
from autosar_pdf2txt.models.types import AutosarClass, AutosarEnumeration, AutosarPrimitive

# Export container classes
from autosar_pdf2txt.models.containers import AutosarPackage, AutosarDoc

__all__ = [
    # Enumerations
    "ATPType",
    "AttributeKind",
    # Base class
    "AbstractAutosarBase",
    "AutosarDocumentSource",
    # Attribute classes
    "AutosarAttribute",
    "AutosarEnumLiteral",
    # Type classes
    "AutosarClass",
    "AutosarEnumeration",
    "AutosarPrimitive",
    # Container classes
    "AutosarPackage",
    "AutosarDoc",
]
