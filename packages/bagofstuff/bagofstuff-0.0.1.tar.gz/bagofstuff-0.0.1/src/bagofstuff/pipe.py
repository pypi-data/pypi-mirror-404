"""Provides a tool for creating a 'pipe' of functions."""

##############################################################################
# Back from the future...
from __future__ import annotations

##############################################################################
# Python imports.
from functools import reduce
from typing import Any, Callable, cast


##############################################################################
class Pipe[TInitial, TResult]:
    """A class that provides a simple function pipeline.

    `Pipe` is a little like Python's own [`partial`][functools.partial]
    except that:

    1. It only allows for one positional parameter.
    2. It allows for a whole chain of functions.

    Example:
        ```python
        from bagoftools.pipe import Pipe

        shortest_len = Pipe[str, int](str.trim, len)

        print(shortest_len("      this is padded     "))
        ```

        As well as passing a list of functions when creating the pipe, they
        can also be added afterwards:

        ```python
        from bagoftools.pipe import Pipe

        shortest_len = Pipe[str, int]()
        shortest_len |= str.trim
        shortest_len |= len

        print(shortest_len("      this is padded     "))
        ```
    """

    def __init__(self, *functions: Callable[[Any], Any]) -> None:
        """Initialise the pipeline.

        Args:
            functions: The initial set of functions.
        """
        self._functions = functions
        """The functions in the pipeline."""

    def __or__(self, function: Callable[[Any], Any], /) -> Pipe[TInitial, TResult]:
        """Add another function to the pipeline.

        Example:
            Assuming a pipeline called `tidy`, a call to
            [`strip`][str.strip] could be added like this:

            ```python
            tidy |= str.strip
            ```
        """
        return Pipe[TInitial, TResult](*self._functions, function)

    def __call__(self, initial: TInitial) -> TResult:
        """Execute the pipeline.

        Given an initial value, it is passed to the first function in the
        pipeline, the result is then passed as the argument to the next
        function in the pipeline, and so on. The result is the result of the
        call to the last function in the pipeline.

        Args:
            initial: The initial value.

        Returns:
            The result of the pipeline.
        """
        return cast(
            TResult,
            reduce(
                lambda value, function: function(value),
                self._functions,
                initial,
            ),
        )


### pipe.py ends here
