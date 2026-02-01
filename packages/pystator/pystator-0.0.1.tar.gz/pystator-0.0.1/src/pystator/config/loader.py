"""Configuration loading for PyStator FSM definitions."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from pystator.config.converter import machine_config_to_core
from pystator.config.models import MachineConfig
from pystator.config.validator import ConfigValidator
from pystator.core.errors import ConfigurationError
from pystator.core.state import State
from pystator.core.transition import Transition

# Variable substitution pattern: ${VAR}, ${VAR:-default}, ${VAR:?error}
VARIABLE_PATTERN = re.compile(r"\$\{([^}:]+)(?::([?-])([^}]*))?\}")


class ConfigLoader:
    """Loads and parses FSM configuration from YAML/JSON files.

    The loader handles:
    - YAML and JSON file formats
    - Environment variable substitution
    - Schema validation
    - Conversion to State and Transition objects

    Variable Substitution:
        - ${VAR} - Replace with environment variable VAR
        - ${VAR:-default} - Use 'default' if VAR is not set
        - ${VAR:?error} - Raise error with message if VAR is not set

    Example:
        >>> loader = ConfigLoader(validate=True)
        >>> config = loader.load("order_fsm.yaml")
        >>> states, transitions, meta = loader.parse(config)
    """

    def __init__(
        self,
        validate: bool = True,
        strict: bool = True,
        variables: dict[str, str] | None = None,
    ) -> None:
        """Initialize the config loader.

        Args:
            validate: If True, validate config against schema.
            strict: If True, raise errors on validation failure.
            variables: Additional variables for substitution (takes precedence over env).
        """
        self.validate = validate
        self.strict = strict
        self.variables = variables or {}
        self._validator = ConfigValidator() if validate else None

    def load(self, path: str | Path) -> dict[str, Any]:
        """Load configuration from a file.

        Args:
            path: Path to YAML or JSON configuration file.

        Returns:
            Parsed configuration dictionary.

        Raises:
            ConfigurationError: If file not found or parsing fails.
        """
        path = Path(path)

        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}", path=str(path))

        try:
            content = path.read_text(encoding="utf-8")
        except OSError as e:
            raise ConfigurationError(f"Failed to read configuration: {e}", path=str(path)) from e

        # Substitute variables before parsing
        content = self._substitute_variables(content, str(path))

        # Parse based on file extension
        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            config = self._parse_yaml(content, str(path))
        elif suffix == ".json":
            config = self._parse_json(content, str(path))
        else:
            # Try YAML first, then JSON
            try:
                config = self._parse_yaml(content, str(path))
            except ConfigurationError:
                config = self._parse_json(content, str(path))

        # Validate if enabled
        if self._validator:
            errors = self._validator.validate(config)
            if errors and self.strict:
                raise ConfigurationError(
                    f"Configuration validation failed with {len(errors)} error(s)",
                    path=str(path),
                    context={"errors": errors},
                )

        return config

    def load_dict(self, config: dict[str, Any]) -> dict[str, Any]:
        """Load and validate a configuration dictionary.

        Args:
            config: Configuration dictionary.

        Returns:
            Validated configuration dictionary.

        Raises:
            ConfigurationError: If validation fails.
        """
        if self._validator:
            errors = self._validator.validate(config)
            if errors and self.strict:
                raise ConfigurationError(
                    f"Configuration validation failed with {len(errors)} error(s)",
                    context={"errors": errors},
                )
        return config

    def _substitute_variables(self, content: str, path: str) -> str:
        """Substitute environment variables in content."""

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            modifier = match.group(2)  # '-' or '?' or None
            default_or_error = match.group(3)  # default value or error message

            # Check variables dict first, then environment
            value = self.variables.get(var_name) or os.environ.get(var_name)

            if value is not None:
                return value

            if modifier == "-":
                # Use default value
                return default_or_error or ""
            elif modifier == "?":
                # Raise error
                error_msg = default_or_error or f"Required variable '{var_name}' not set"
                raise ConfigurationError(
                    f"Variable substitution error: {error_msg}",
                    path=path,
                    context={"variable": var_name},
                )
            else:
                # No modifier, return empty string
                return ""

        return VARIABLE_PATTERN.sub(replacer, content)

    def _parse_yaml(self, content: str, path: str) -> dict[str, Any]:
        """Parse YAML content."""
        try:
            import yaml

            result = yaml.safe_load(content)
            if not isinstance(result, dict):
                raise ConfigurationError(
                    "Configuration must be a YAML mapping (dictionary)",
                    path=path,
                )
            return result
        except ImportError as e:
            raise ConfigurationError(
                "PyYAML is required for YAML configuration files. "
                "Install with: pip install pyyaml",
                path=path,
            ) from e
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax: {e}",
                path=path,
            ) from e

    def _parse_json(self, content: str, path: str) -> dict[str, Any]:
        """Parse JSON content."""
        try:
            result = json.loads(content)
            if not isinstance(result, dict):
                raise ConfigurationError(
                    "Configuration must be a JSON object (dictionary)",
                    path=path,
                )
            return result
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON syntax: {e}",
                path=path,
            ) from e

    def parse(
        self, config: dict[str, Any]
    ) -> tuple[dict[str, State], list[Transition], dict[str, Any]]:
        """Parse complete configuration into states, transitions, and metadata.

        Uses Pydantic to validate and parse, then converts to core State/Transition.

        Args:
            config: Configuration dictionary (typically from load() or load_dict()).

        Returns:
            Tuple of (states_dict, transitions_list, meta_dict).

        Raises:
            ConfigurationError: If config is invalid (Pydantic or semantic validation).
        """
        try:
            validated = MachineConfig.model_validate(config)
        except ValidationError as e:
            errors = [
                f"[{'.'.join(str(p) for p in err.get('loc', ()))}] {err.get('msg', 'validation error')}"
                for err in e.errors()
            ]
            raise ConfigurationError(
                f"Configuration validation failed with {len(errors)} error(s)",
                context={"errors": errors},
            ) from e
        try:
            return machine_config_to_core(validated)
        except ValueError as e:
            raise ConfigurationError(
                str(e),
                context={"config": config},
            ) from e


def load_config(
    path: str | Path,
    validate: bool = True,
    strict: bool = True,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Load configuration from file.

    Convenience function for quick configuration loading.

    Args:
        path: Path to configuration file.
        validate: If True, validate against schema.
        strict: If True, raise errors on validation failure.
        variables: Additional variables for substitution.

    Returns:
        Parsed configuration dictionary.
    """
    loader = ConfigLoader(validate=validate, strict=strict, variables=variables)
    return loader.load(path)
