class CannotLocatePyProjectError(Exception):
    """Used when the default Python file cannot be found."""


class TemplateMalformedError(Exception):
    """Used when a pyproject.toml file is malformed."""
