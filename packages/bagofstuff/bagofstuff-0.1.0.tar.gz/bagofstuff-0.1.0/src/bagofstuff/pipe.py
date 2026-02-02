"""Provides a tool for creating a 'pipe' of functions."""

##############################################################################
# Back from the future...
from __future__ import annotations

##############################################################################
# Python imports.
from functools import reduce
from typing import Any, Callable, Final, cast


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

    class Nullary:
        """Type that marks that there is no initial argument."""

    _NoArgument: Final[Nullary] = Nullary()
    """Sentinel value to say there is no argument."""

    def __init__(self, *functions: Callable[..., Any]) -> None:
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

    def __call__(self, initial: TInitial | Nullary = _NoArgument) -> TResult:
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
        if not (functions := self._functions):
            raise TypeError("Empty Pipe called")
        if (seed := initial) is self._NoArgument:
            seed = functions[0]()
            functions = functions[1:]
        return cast(
            TResult,
            reduce(
                lambda value, function: function(value),
                functions,
                seed,
            ),
        )

    def __repr__(self) -> str:
        """Represent the pipeline.

        Returns:
            A string representation of the pipeline.
        """
        pipeline = (
            " | ".join(function.__qualname__ for function in self._functions)
            or "<EMPTY>"
        )
        return f"<{self.__class__.__name__}: {pipeline}>"


### pipe.py ends here
