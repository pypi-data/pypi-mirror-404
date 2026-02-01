"""Byte scale enum for file size operations."""

from __future__ import annotations

from enum import Enum
from typing import Self


class ByteScale(Enum):
    """Byte scale prefix converter."""

    NONE = (0, "")
    KILO = (1, "K")
    MEGA = (2, "M")
    GIGA = (3, "G")
    TERA = (4, "T")
    PETA = (5, "P")

    def __new__(cls, exponent: int, prefix_letter: str) -> Self:
        """Apply values to the new Enum.

        __new__ is used to control how new enum members are instantiated.
        It must set the `_value_` attribute and any custom attributes.

        Args:
            exponent (int): the exponent value for the scale
            prefix_letter (str): the prefix letter for the scale

        Returns:
            ByteScale: A new ByteScale enum.

        """
        obj = object.__new__(cls)
        obj._value_ = exponent
        obj.prefix_letter = prefix_letter
        return obj

    @property
    def prefix_letter(self) -> str:
        """Return the prefix letter for this scale."""
        return self._prefix_letter

    @prefix_letter.setter
    def prefix_letter(self, value: str) -> None:
        """Setter for prefix letter."""
        self._prefix_letter = value
