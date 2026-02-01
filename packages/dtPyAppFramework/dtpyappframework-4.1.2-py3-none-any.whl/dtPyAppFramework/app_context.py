"""
Application Context — unified facade for framework components.

Provides convenient singleton access to application metadata, paths,
configuration file locations, settings, and secrets management.
All methods delegate to the existing framework singletons.

Usage::

    from dtPyAppFramework.app_context import AppContext

    ctx = AppContext()
    print(ctx.version)
    print(ctx.logging_path)
    value = ctx.get_setting('app.timeout', 30)
    secret = ctx.get_secret('api_key')
"""

from typing import Any, List, Optional

from dtPyAppFramework.decorators import singleton


@singleton()
class AppContext:
    """
    Singleton facade providing convenient access to application metadata,
    paths, settings, and secrets management.

    Initialised automatically by ``ProcessManager`` during application
    startup.  Subsequent calls to ``AppContext()`` return the same
    pre-initialised instance.
    """

    def __init__(
        self,
        version: str = None,
        full_name: str = None,
        short_name: str = None,
        description: str = None,
    ) -> None:
        self._version = version
        self._full_name = full_name
        self._short_name = short_name
        self._description = description

    # ── Application Metadata ──────────────────────────────────

    @property
    def version(self) -> str:
        """Application version string."""
        return self._version

    @property
    def full_name(self) -> str:
        """Full display name of the application."""
        return self._full_name

    @property
    def short_name(self) -> str:
        """Short name / abbreviation of the application."""
        return self._short_name

    @property
    def description(self) -> str:
        """Application description."""
        return self._description

    # ── Application Paths ─────────────────────────────────────

    @property
    def logging_path(self) -> str:
        """Root path for log files."""
        from dtPyAppFramework.paths import ApplicationPaths
        return ApplicationPaths().logging_root_path

    @property
    def app_data_path(self) -> str:
        """Root path for system-wide / all-users application data."""
        from dtPyAppFramework.paths import ApplicationPaths
        return ApplicationPaths().app_data_root_path

    @property
    def usr_data_path(self) -> str:
        """Root path for current user application data."""
        from dtPyAppFramework.paths import ApplicationPaths
        return ApplicationPaths().usr_data_root_path

    @property
    def tmp_path(self) -> str:
        """Root path for temporary files."""
        from dtPyAppFramework.paths import ApplicationPaths
        return ApplicationPaths().tmp_root_path

    # ── Config File Paths ─────────────────────────────────────

    @property
    def config_file_paths(self) -> List[str]:
        """
        Paths to the ``config.yaml`` files currently loaded by the
        settings readers, ordered by priority (lowest number first).
        """
        from dtPyAppFramework.settings import Settings
        return [reader.settings_file for reader in Settings().settings_readers]

    # ── Settings Convenience ──────────────────────────────────

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a setting value by dot-notation key.

        Args:
            key: Dot-notation setting key (e.g. ``'app.name'``).
            default: Value returned when the key is not found.

        Returns:
            The setting value, or *default* if not found.
        """
        from dtPyAppFramework.settings import Settings
        return Settings().get(key, default)

    def set_setting(self, key: str, value: Any, store_name: str = None) -> None:
        """
        Persist a setting value.

        Args:
            key: Dot-notation setting key.
            value: Value to store.
            store_name: Optional target store name.
        """
        from dtPyAppFramework.settings import Settings
        Settings().set(key, value, store_name)

    # ── Secrets Convenience ───────────────────────────────────

    def get_secret(self, key: str, default: Any = None, store_name: str = None) -> Any:
        """
        Retrieve a secret value.

        Args:
            key: Secret key identifier.
            default: Value returned when the secret is not found.
            store_name: Optional target secret store name.

        Returns:
            The secret value, or *default* if not found.
        """
        from dtPyAppFramework.settings import Settings
        return Settings().secret_manager.get_secret(key, default, store_name)

    def set_secret(self, key: str, value: Any, store_name: str = 'User_Local_Store') -> None:
        """
        Store a secret value.

        Args:
            key: Secret key identifier.
            value: Secret value to store.
            store_name: Target secret store (default ``'User_Local_Store'``).
        """
        from dtPyAppFramework.settings import Settings
        Settings().secret_manager.set_secret(key, value, store_name)

    def delete_secret(self, key: str, store_name: str = 'User_Local_Store') -> None:
        """
        Delete a secret from a store.

        Args:
            key: Secret key identifier.
            store_name: Target secret store (default ``'User_Local_Store'``).
        """
        from dtPyAppFramework.settings import Settings
        Settings().secret_manager.delete_secret(key, store_name)

    # ── Resources Convenience ─────────────────────────────────

    def get_resource_path(self, resource: str) -> Optional[str]:
        """
        Locate a named resource across all resource paths.

        Args:
            resource: Resource file name or relative path.

        Returns:
            Full path to the resource, or ``None`` if not found.
        """
        from dtPyAppFramework.resources import ResourceManager
        return ResourceManager().get_resource_path(resource)
