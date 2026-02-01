import string
import random
import secrets
import re
import logging

class AbstractSecretStore(object):
    """
    An abstract class representing a generic secret store.

    Attributes:
        store_name (str): Name of the secret store.
        store_type (str): Type of the secret store.
        store_priority (int): Priority of the secret store.
        application_settings (Settings): An instance of Settings providing application settings.

    Methods:
        __init__(store_name, store_type, store_priority, application_settings): Constructor to initialize the AbstractSecretStore.
        priority(): Get the priority of the secret store.
        get_store_setting(key, default=None): Get a specific setting for the secret store from application settings.
        name(): Get the name of the secret store.
        __str__(): String representation of the secret store.
        get_secret(key, default_value=None): Retrieve a secret from the secret store.
        set_secret(key, value): Set a secret in the secret store.
        delete_secret(key): Delete a secret from the secret store.
        create_secret(name, length=18): Generate a random secret and store it in the secret store.

    Exceptions:
        SecretsStoreException: Custom exception for errors related to secret stores.
    """

    def __init__(self, store_name, store_type, store_priority, application_settings) -> None:
        """
        Initialize the AbstractSecretStore.

        Args:
            store_name (str): Name of the secret store.
            store_type (str): Type of the secret store.
            store_priority (int): Priority of the secret store.
            application_settings (Settings): An instance of Settings providing application settings.
        """
        super().__init__()
        self.store_name = store_name
        self.store_priority = store_priority
        self.store_type = store_type
        self.application_settings = application_settings
        self.store_available: bool = False
        self.store_read_only: bool = True

    def priority(self):
        """Get the priority of the secret store."""
        return self.store_priority

    def get_store_setting(self, key, default=None):
        """
        Get a specific setting for the secret store from application settings.

        Args:
            key (str): Setting key.
            default: Default value if the setting is not found.

        Returns:
            Setting value or default if not found.
        """
        full_key = f'secrets_manager.cloud_stores.{self.store_name}.{key}'
        return self.application_settings.get(full_key, default)

    def name(self):
        """Get the name of the secret store."""
        return self.store_name

    def __str__(self) -> str:
        """String representation of the secret store."""
        return f'{self.store_name}-SecretStore-{self.__hash__()} [Priority: {self.store_priority}]'

    def get_secret(self, key, default_value=None):
        """
        Retrieve a secret from the secret store.

        Args:
            key (str): Key of the secret.
            default_value: Default value to return if the secret is not found.

        Raises:
            NotImplementedError: This method should be implemented in concrete subclasses.

        Returns:
            Secret value if found, else default_value.
        """
        raise NotImplementedError

    def set_secret(self, key, value):
        """
        Set a secret in the secret store.

        Args:
            key (str): Key of the secret.
            value: Value of the secret.

        Raises:
            NotImplementedError: This method should be implemented in concrete subclasses.
        """
        raise NotImplementedError

    def delete_secret(self, key):
        """
        Delete a secret from the secret store.

        Args:
            key (str): Key of the secret.

        Raises:
            NotImplementedError: This method should be implemented in concrete subclasses.
        """
        raise NotImplementedError

    @staticmethod
    def _get_charset_for_complexity(complexity: str) -> str:
        """
        Return the character set corresponding to the given complexity level.

        Args:
            complexity (str): One of 'basic', 'medium', 'high', or 'alphanum'.

        Returns:
            str: The character set to use for secret generation.

        Raises:
            ValueError: If the complexity level is not recognised.
        """
        complexity_sets = {
            'basic': string.ascii_letters + string.digits,
            'medium': string.ascii_letters + string.digits + '!@#$%^&*',
            'high': string.ascii_letters + string.digits + '!@#$%^&*()_+-=[]{}|;:,.<>?',
            'alphanum': string.ascii_letters + string.digits
        }
        if complexity not in complexity_sets:
            raise ValueError(f"Invalid complexity level: {complexity}")
        return complexity_sets[complexity]

    @staticmethod
    def _meets_complexity_requirements(secret: str, complexity: str) -> bool:
        """
        Check whether a generated secret satisfies the character class requirements
        for the given complexity level.

        Args:
            secret (str): The generated secret string.
            complexity (str): The complexity level used during generation.

        Returns:
            bool: True if the secret meets the requirements, False otherwise.
        """
        has_lower = any(c.islower() for c in secret)
        has_upper = any(c.isupper() for c in secret)
        has_digit = any(c.isdigit() for c in secret)

        if complexity in ['medium', 'high']:
            has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in secret)
            return has_lower and has_upper and has_digit and has_special

        if complexity == 'basic':
            return has_lower and has_upper and has_digit

        # 'alphanum' has no special requirements beyond the charset itself
        return True

    def create_secret(self, name: str, length: int = 18, complexity: str = 'high') -> str:
        """
        Generate a cryptographically secure secret and store it in the secret store.

        Args:
            name (str): Key of the secret.
            length (int): Length of the generated secret (default: 18, min: 12, max: 1024).
            complexity (str): Complexity level ('basic', 'medium', 'high', 'alphanum').

        Returns:
            Generated secret value.

        Raises:
            ValueError: If inputs are invalid or secret generation fails.
        """
        # Import validation here to avoid circular imports
        try:
            from ...security.validation import InputValidator
            InputValidator.validate_secret_key(name)
        except ImportError:
            if not isinstance(name, str) or len(name) == 0:
                raise ValueError("Secret name must be non-empty string")

        if not isinstance(name, str) or len(name) == 0:
            raise ValueError("Secret name must be non-empty string")

        if length < 12:
            raise ValueError("Minimum secret length is 12 characters")

        if length > 1024:
            raise ValueError("Maximum secret length is 1024 characters")

        charset = self._get_charset_for_complexity(complexity)

        max_attempts = 50
        for _ in range(max_attempts):
            secret = ''.join(secrets.choice(charset) for _ in range(length))

            if not self._meets_complexity_requirements(secret, complexity):
                continue

            if not self._validate_secret_strength(secret):
                continue

            self.set_secret(name, secret)
            logging.info(f"Generated secret '{name}' with length {length}, complexity {complexity}")
            return secret

        raise RuntimeError(f"Failed to generate compliant secret after {max_attempts} attempts")

    def _validate_secret_strength(self, secret: str) -> bool:
        """Validate secret doesn't contain weak patterns."""
        
        # Check for repeated characters
        if re.search(r'(.)\1{3,}', secret):  # 4+ repeated chars
            return False
        
        # Check for sequential patterns
        sequential_patterns = [
            'abcdefgh', '12345678', 'qwertyui',
            'ABCDEFGH', '87654321', 'password'
        ]
        
        secret_lower = secret.lower()
        for pattern in sequential_patterns:
            if pattern in secret_lower:
                return False
        
        return True


class SecretsStoreException(Exception):
    """Custom exception for errors related to secret stores."""
    pass
