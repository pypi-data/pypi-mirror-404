===========
TypeChecked
===========

A comprehensive runtime type hint checker for use with Python 3.10 and above.

This library provides pure-Python functions and base classes to check type hints at runtime,
helping to catch type-related errors during data processing and manipulation.

It is not intended to be used for validating function parameters in production code.
It can be used for that purpose, but it is not optimized for performance in that scenario.

Other tools such as `typeguard <https://typeguard.readthedocs.io/en/latest/>`_ and
`beartype <https://beartype.readthedocs.io/en/latest/>`_ are much better suited for
that purpose as they are specifically optimized for performance in checking function
parameters at call time by injecting compiled type checks into function call sites.

It is intended for use in a more general context, such as validating complex
data structures, config files, or complex objects where type correctness is critical
such as during data ingestion, transformation, or serialization/deserialization.

It supports checking of standard type hints as defined in PEP 484, PEP 585, PEP 586,
PEP 589, PEP 591, PEP 593, and PEP 604 among others, as well as more complex
type constructs such as nested generics, unions, literals, typed dictionaries,
and recursive types. These are support for both built-in and user-defined classes
and dataclasses.

Supported Typing Constructs
---------------------------

- Basic types: int, str, float, bool, etc.
- Generic types: Set, Mapping, Sequence, Iterable, Callable, Collection
- Specific types: list, dict, OrderedDict, frozenset, tuple, etc.
- Generic aliases: list[int], dict[str, float], etc.
- Tuple types: Tuple, tuple, Tuple[int, ...], Tuple[int, str], etc
- Union types: Union, Optional, ``|``, etc.
- Final types: Final
- TypeVar
- NewType types: NewType
- Annotated types: Annotated
- Literal types: Literal
- Typed dictionaries: TypedDict, NotRequired, Required, ReadOnly, total, extras
- Runtime Protocols: Protocol
- Nested generics: List[Dict[str, Union[int, str]]], etc.
- User-defined classes and dataclasses
- Nested combinations of the above

It especially shines in scenarios where data structures are deeply nested
immutable structures (lists, tuples, dicts, sets, frozensets) containing
various combinations of types that need to be validated at runtime because
it caches type information for objects for improved performance on repeated checks
and subtree validations to avoid redundant checks.

If you check a subcontainer (e.g., a tuple within a MappingProxyType within a frozenset),
it will cache the results of each subtree so that if the same subtree is encountered again,
it can skip re-validating that subtree.

This library can be used in data processing pipelines, ETL processes,
or any scenario where data integrity and type correctness are paramount.

It also provides deep immutability checking for deep immutable types via the
`typechecked.immutable` submodule to validate data structures that should not be modified
after creation. This is useful for ensuring that certain data structures remain unchanged
throughout their lifecycle, preventing accidental mutations that could lead to bugs
or data corruption. It checks not just the top-level container, but also all nested containers
and their contents to ensure complete immutability.

It provides a base class `Immutable` that can be inherited by user-defined classes to
label them as immutable and have their instances marked as immutable during type checking.

It can check TypedDict definitions against any Mapping type at runtime, allowing for
validation of dictionary-like structures against TypedDict schemas.

Installation
------------

You can install TypeChecked via pip:

.. code-block:: bash

    pip install typechecked

It has few external dependencies and relies on the Python standard library
except for the use of `typing-extensions` to allow older Python versions to
use newer typing features when available.

Usage
-----

.. code-block:: python

    from typechecked import isinstance_of_typehint

    MyDataStructure = dict[str, list[int]]

    data = {"numbers": [1, 2, 3]}
    if isinstance_of_typehint(data, MyDataStructure):
        print("Data is valid")
    else:
        print("Data is invalid")

Contributing
------------
This project is open to contributions! If you find a bug or have a feature request,
please open an issue on GitHub. Pull requests are also welcome.

Bootstrapping Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fork a copy of the repository on GitHub.

Clone your fork the cloned repository: `git clone https://github.com/your-username/python-typechecked.git`

Change to the project directory: `cd python-typechecked`

Run the bootstrap script:

.. code-block:: bash

    python bootstrap.py

And follow the prompts.

This will create a virtual environment in the project root
without modifying your system or user Python installation.

It installs the necessary minimum tooling to get started
working with development tasks such as testing, linting,
and building documentation.
