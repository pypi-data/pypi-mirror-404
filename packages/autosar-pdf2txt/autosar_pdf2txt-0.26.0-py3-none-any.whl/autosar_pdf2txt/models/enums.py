"""AUTOSAR model enumerations.

Requirements:
    SWR_MODEL_00001: AUTOSAR Class Representation
"""

from enum import Enum


class ATPType(Enum):
    """AUTOSAR Tool Platform marker type.

    Requirements:
        SWR_MODEL_00001: AUTOSAR Class Representation

    This enum represents the ATP (AUTOSAR Tool Platform) marker type that can be
    associated with AUTOSAR classes.

    Attributes:
        NONE: No ATP marker present
        ATP_MIXED_STRING: The class has the <<atpMixedString>> marker
        ATP_VARIATION: The class has the <<atpVariation>> marker
        ATP_MIXED: The class has the <<atpMixed>> marker
        ATP_PROTO: The class has the <<atpPrototype>> marker
    """

    NONE = "none"
    ATP_MIXED_STRING = "atpMixedString"
    ATP_VARIATION = "atpVariation"
    ATP_MIXED = "atpMixed"
    ATP_PROTO = "atpPrototype"


class AttributeKind(Enum):
    """AUTOSAR attribute kind enumeration.

    Requirements:
        SWR_MODEL_00010: AUTOSAR Attribute Representation

    This enum represents the kind of AUTOSAR attribute, indicating whether it is
    a regular attribute, an aggregated attribute, or a reference attribute.

    Attributes:
        ATTR: Regular attribute
        AGGR: Aggregated attribute
        REF: Reference attribute
    """

    ATTR = "attr"
    AGGR = "aggr"
    REF = "ref"