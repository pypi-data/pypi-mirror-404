"""Tools for iterating or working on iterable things."""

##############################################################################
# Python imports.
from itertools import chain
from typing import Iterable, Iterator, Literal

##############################################################################
type Direction = Literal["forward", "backward"]
"""Directions used with [`starting_at`][bagofstuff.itertools.starting_at]."""


##############################################################################
def starting_at[T](
    items: Iterable[T], start_at: int = 0, direction: Direction = "forward"
) -> Iterator[T]:
    """Create an iterator of all items starting at a given point.

    This function creates an iterator of all the items in the initial
    iterable, starting at the given point and wrapping around the end if
    necessary.

    Args:
        items: The items to iterate over.
        start_at: The item to start out at.
        direction: The direction to iterate in.

    Returns:
        An iterable of all the items starting at the given point.
    """
    items = list(reversed(list(items)) if direction == "backward" else items)
    start_at = (len(items) - start_at - 1) if direction == "backward" else start_at
    return chain(items[start_at:], items[:start_at])


### itertools.py ends here
