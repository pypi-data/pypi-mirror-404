"""Exceptions for python-introspect."""


class IntrospectionError(Exception):
    """Base exception for introspection errors."""
    pass


class SignatureAnalysisError(IntrospectionError):
    """Exception raised when signature analysis fails."""
    pass


class DocstringParsingError(IntrospectionError):
    """Exception raised when docstring parsing fails."""
    pass


class TypeResolutionError(IntrospectionError):
    """Exception raised when type resolution fails."""
    pass
