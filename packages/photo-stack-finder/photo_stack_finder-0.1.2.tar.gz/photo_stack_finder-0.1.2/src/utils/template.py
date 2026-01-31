"""Template utilities for partial string substitution.

Provides template extraction and partial substitution using str.format_map().
"""

from __future__ import annotations


class DefaultDict(dict[str, str]):
    """Dictionary that returns placeholder for missing keys during format_map().

    This allows partial substitution of template strings, leaving unmatched
    placeholders in their original form.

    Example:
            >>> template = "IMG_{P0}_{P1}_{P2}"
            >>> values = {'P0': '1234', 'P1': '5678'}
            >>> result = template.format_map(DefaultDict(values))
            >>> print(result)
            IMG_1234_5678_{P2}
    """

    def __missing__(self, key: str) -> str:
        """Return the key wrapped in braces for missing keys.

        Args:
                key: The missing key

        Returns:
                String of the form "{key}"
        """
        return f"{{{key}}}"


def partial_format(template: str, values: dict[str, str]) -> str:
    """Perform partial string substitution on a template.

    Substitutes available values and leaves missing placeholders unchanged.

    Args:
            template: Template string with {P0}, {P1}, etc. placeholders
            values: Dictionary of values to substitute

    Returns:
            Partially formatted string

    Example:
            >>> partial_format("IMG_{P0}_{P1}_{P2}", {'P0': '1234', 'P1': '5678'})
            'IMG_1234_5678_{P2}'

            >>> partial_format("IMG_{P0}_{P1}", {'P0': '1234', 'P1': '5678'})
            'IMG_1234_5678'

            >>> partial_format("IMG_{P0}_{P1}_{P2}", {})
            'IMG_{P0}_{P1}_{P2}'
    """
    return template.format_map(DefaultDict(values))
