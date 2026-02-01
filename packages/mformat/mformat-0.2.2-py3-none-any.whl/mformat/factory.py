#! /usr/local/bin/python3
"""Factory class for creating MultiFormat instances."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from typing import Optional, TypedDict, Callable
from mformat.mformat import MultiFormat, FormatterDescriptor
from mformat.reg_pkg_formats import register_formats_in_pkg


_the_factory: Optional['MultiFormatFactory'] = None  # pylint: disable=invalid-name # noqa: E501


class OptArgsDict(TypedDict, total=False):
    """Optional arguments for the MultiFormat constructor."""

    file_exists_callback: Optional[Callable[[str], None]]
    lang: Optional[str]
    title: Optional[str]
    css_file: Optional[str]


type OptArgs = Optional[OptArgsDict]


class MultiFormatFactory:
    """Factory class for creating instances of MultiFormat subclasses."""

    def __init__(self) -> None:
        """Initialize the factory with an empty registry."""
        self._registry: dict[str, type[MultiFormat]] = {}
        self._usage: dict[str, FormatterDescriptor] = {}
        formats: list[type[MultiFormat]] = register_formats_in_pkg()
        for format_class in formats:
            self.i_register(format_class)

    @staticmethod
    def i_get_factory() -> 'MultiFormatFactory':
        """Internally get the factory instance."""
        global _the_factory  # pylint: disable=global-statement # noqa: E501
        if _the_factory is None:
            _the_factory = MultiFormatFactory()
        return _the_factory

    @staticmethod
    def register(format_class: type[MultiFormat]) -> None:
        """Register a MultiFormat subclass with the factory."""
        factory = MultiFormatFactory.i_get_factory()
        factory.i_register(format_class=format_class)

    def i_register(self, format_class: type[MultiFormat]) -> None:
        """Internally register a MultiFormat subclass with the factory."""
        if not issubclass(format_class, MultiFormat):
            err = f'{format_class.__name__} must be a subclass of MultiFormat'
            raise ValueError(err)
        desc: FormatterDescriptor = format_class.get_arg_desciption()
        self._registry[desc.name] = format_class
        self._usage[desc.name] = desc

    @staticmethod
    def create(format_name: str, file_name: str,
               url_as_text: bool = False,
               args: OptArgs = None) -> MultiFormat:
        """Create an instance of a registered MultiFormat subclass.

        Args:
            format_name: The name identifier of the format class to create.
            file_name: The file path to pass to the MultiFormat constructor.
            url_as_text: Format URLs as text not clickable URLs.
            args: additional arguments to pass to the MultiFormat constructor.
        Returns:
            An instance of the requested MultiFormat subclass.
            Intended to be used as context manager, using a with statement.
        Raises:
            ValueError: If the format_name is not registered.
        """
        factory = MultiFormatFactory.i_get_factory()
        return factory.i_create(format_name=format_name,
                                file_name=file_name,
                                url_as_text=url_as_text,
                                args=args)

    def i_create(self, format_name: str, file_name: str,
                 url_as_text: bool = False,
                 args: OptArgs = None) -> MultiFormat:
        """Internally create an instance of a registered subclass."""
        if format_name not in self._registry:
            raise ValueError(
                f'Format "{format_name}" is not registered. ' +
                'Available formats: ' +
                f'{", ".join(sorted(list(self._registry.keys())))}'
            )
        format_class = self._registry[format_name]
        if args is None:
            return format_class(file_name=file_name, url_as_text=url_as_text)
        assert args is not None
        return format_class(file_name=file_name,  # type: ignore[misc]
                            url_as_text=url_as_text, **args)
        # mypy cannot see which MultiFormat subclass is being created, so it
        # cannot know which arguments are valid.

    @staticmethod
    def get_registered_formats() -> list[str]:
        """Get a list of all registered format names.

        Returns:
            A list of registered format name strings.
        """
        factory = MultiFormatFactory.i_get_factory()
        return factory.i_get_registered_formats()

    def i_get_registered_formats(self) -> list[str]:
        """Internally get a list of registered format names."""
        return sorted(list(self._registry.keys()))

    @staticmethod
    def get_usage(format_name: str) -> FormatterDescriptor:
        """Get the usage information for a registered format."""
        factory = MultiFormatFactory.i_get_factory()
        return factory.i_get_usage(format_name=format_name)

    def i_get_usage(self, format_name: str) -> FormatterDescriptor:
        """Internally get the usage information for a registered format."""
        if format_name not in self._usage:
            raise ValueError(
                f'Format "{format_name}" is not registered. ' +
                'Available formats: ' +
                f'{", ".join(sorted(list(self._registry.keys())))}'
            )
        return self._usage[format_name]


def create_mf(format_name: str, file_name: str,
              url_as_text: bool = False,
              args: OptArgs = None) -> MultiFormat:
    """Create an instance of a registered MultiFormat subclass.

    Intended to be used as context manager, using a with statement.
    This is a shortcut for MultiFormatFactory.create().
    Args:
        format_name: The name identifier of the format class to create.
        file_name: The file path to pass to the MultiFormat constructor.
        url_as_text: Format URLs as text not clickable URLs.
        args: additional arguments to pass to the MultiFormat constructor.
    Returns:
        An instance of the requested MultiFormat subclass.
    Raises:
        ValueError: If the format_name is not registered.
    """
    return MultiFormatFactory.create(format_name=format_name,
                                     file_name=file_name,
                                     url_as_text=url_as_text,
                                     args=args)


def list_registered_mf() -> list[str]:
    """Get a list of all registered format names.

    This is a shortcut for MultiFormatFactory.get_registered_formats().
    Returns:
        A list of registered format name strings.
    """
    return MultiFormatFactory.get_registered_formats()


def usage_mf(format_name: str) -> FormatterDescriptor:
    """Get the usage information for a registered format.

    This is a shortcut for MultiFormatFactory.get_usage().
    """
    return MultiFormatFactory.get_usage(format_name=format_name)


def register_mf(format_class: type[MultiFormat]) -> None:
    """Register a MultiFormat subclass with the factory.

    This is a shortcut for MultiFormatFactory.register().
    Args:
        format_class: The MultiFormat subclass to register.
    Raises:
        ValueError: If the format_class is not a subclass of MultiFormat.
    """
    MultiFormatFactory.register(format_class=format_class)
