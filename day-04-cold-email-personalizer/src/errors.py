# src/errors.py

class ColdEmailError(Exception):
    """Base class for all domain-specific errors."""


class DataLoadError(ColdEmailError):
    """Raised when prospect data cannot be loaded or parsed."""


class ValidationError(ColdEmailError):
    """Raised when prospect or template validation fails."""


class TemplateError(ColdEmailError):
    """Raised when a template is invalid or cannot be rendered."""


class RenderError(ColdEmailError):
    """Raised when output rendering fails."""
