import json
import os
import sys
import logging
import re
import pybase64
import yaml
import base64

from .secret_store import AbstractSecretStore, SecretsStoreException
from itertools import cycle
from ...misc import run_cmd
from ...security.crypto import SecureKeyGenerator, LegacyKeyGenerator
from ...security.validation import InputValidator, SecurityValidationError
from ...security.filesystem import SecureFileManager, FileSystemSecurityError
from ...security.error_handling import secure_error_handler, secure_error_handling

from .keystore import PasswordProtectedKeystoreWithHMAC, SystemPasswordGenerator
from deprecated import deprecated
from base64 import urlsafe_b64encode


class LocalSecretStore(AbstractSecretStore):
    """
    A class representing a local secret store for managing secrets.

    Attributes:
        store_name (str): Name of the secret store.
        store_priority (int): Priority of the secret store.
        root_store_path (str): Root path where the local secret store is stored.
        application_settings (Settings): An instance of Settings providing application settings.
        app_short_name (str): Short name of the application.
        password (str): Password for the local secret store.

    Methods:
        __init__(store_name, store_priority, root_store_path, application_settings, app_short_name, password=None): Constructor to initialize the LocalSecretStore.
        __initialise_secrets_store(password): Initialize the secrets store if it doesn't exist.
        __guid(): Generate a unique identifier based on the machine and store path.
        get_secret(key, default_value=None): Retrieve a secret from the local secret store.
        set_secret(key, value): Set a secret in the local secret store.
        delete_secret(key): Delete a secret from the local secret store.
        __save(): Save the changes made to the local secret store.
    """

    def __init__(self, store_name, store_priority, root_store_path, application_settings, app_short_name,
                 password: str = os.getenv('KEYSTORE_PASSWORD') or os.getenv('SECRETS_STORE_PASSWORD', None)) -> None:
        """
        Initialize the LocalSecretStore with secure dual keystore system.

        Args:
            store_name (str): Name of the secret store.
            store_priority (int): Priority of the secret store.
            root_store_path (str): Root path where the local secret store is stored.
            application_settings (Settings): An instance of Settings providing application settings.
            app_short_name (str): Short name of the application.
            password (str): Password for the local secret store (default: None).
        """
        super().__init__(store_name, 'local', store_priority, application_settings)
        
        # Debug logging for environment variables
        keystore_pwd_env = os.getenv('KEYSTORE_PASSWORD')
        secrets_pwd_env = os.getenv('SECRETS_STORE_PASSWORD') 
        container_mode_env = os.getenv('CONTAINER_MODE')
        logging.debug(f"LocalSecretStore.__init__ - KEYSTORE_PASSWORD: {'SET' if keystore_pwd_env else 'NOT SET'}")
        logging.debug(f"LocalSecretStore.__init__ - SECRETS_STORE_PASSWORD: {'SET' if secrets_pwd_env else 'NOT SET'}")
        logging.debug(f"LocalSecretStore.__init__ - CONTAINER_MODE: {container_mode_env}")
        logging.debug(f"LocalSecretStore.__init__ - password parameter: {'SET' if password else 'NOT SET'}")
        logging.debug(f"LocalSecretStore.__init__ - store_name: {store_name}, root_store_path: {root_store_path}")
        
        # Check for deprecated keystore format
        if os.path.exists(os.path.join(root_store_path, f"{app_short_name}.keystore")):
            logging.warning(f'Old Keystore file "{os.path.join(root_store_path, f"{app_short_name}.keystore")}" is no longer supported.')

        # Initialize secure key generator for v3 keystores
        self.secure_key_generator = SecureKeyGenerator(app_short_name)
        
        # Store paths for both keystore versions
        self.v2_keystore_path = os.path.join(root_store_path, f"{app_short_name}.v2keystore")
        self.v3_keystore_path = os.path.join(root_store_path, f"{app_short_name}.v3keystore")
        self.app_short_name = app_short_name
        self.root_store_path = root_store_path

        try:
            # Debug logging for password source
            if password:
                logging.info("Using provided password for keystore initialization (LocalSecretStore)")
            else:
                logging.info("No password provided, will use system-generated password (LocalSecretStore)")
            
            # Determine which keystore to use and generate appropriate password
            keystore_path, keystore_password, version = self._determine_keystore_version_and_password(password)
            
            # Initialize the keystore
            self.store = PasswordProtectedKeystoreWithHMAC(keystore_path, keystore_password)
            self.store_path = keystore_path
            self.keystore_version = version
            
            self.store_available = True
            self.store_read_only = not self.__is_writeable()
            
            logging.info(f'Successfully opened {version} Secrets Store: {self.store_path}')
            self.__check_auto_imports(root_store_path)
            
        except Exception as ex:
            error_id = secure_error_handler.log_secret_operation_error(
                "keystore_initialization", 
                f"{app_short_name}_keystore", 
                ex, 
                store_name
            )
            raise SecretsStoreException(f'Failed to open Secrets Store (Error ID: {error_id})')

    def _migrate_v2_to_v3(self, custom_password: str = None):
        """
        Migrate a v2 keystore to v3 format.

        Opens the existing v2 keystore with the legacy password, creates a new
        v3 keystore with a secure password, copies all valid secrets across, and
        renames the old v2 file as a backup.

        Args:
            custom_password (str): Optional custom password for the new v3 keystore.

        Returns:
            tuple: (keystore_path, password, version) for the resulting keystore.
                   Falls back to the v2 keystore if migration fails.
        """
        logging.info("Found v2keystore, performing migration to v3...")

        try:
            v2_password = self._generate_v2_password()
            v2_keystore = PasswordProtectedKeystoreWithHMAC(self.v2_keystore_path, v2_password)

            v3_password = self._generate_v3_password(custom_password)
            v3_keystore = PasswordProtectedKeystoreWithHMAC(self.v3_keystore_path, v3_password)

            v2_secrets = v2_keystore.get_all()
            if v2_secrets:
                for secret_key in v2_secrets:
                    try:
                        InputValidator.validate_secret_key(secret_key)
                        secret_value = v2_keystore.get(secret_key)
                        if secret_value:
                            v3_keystore.set(secret_key, secret_value)
                    except SecurityValidationError:
                        logging.warning(f"Skipping invalid secret key during migration: {secret_key}")
                        continue

            backup_path = f"{self.v2_keystore_path}_old"
            os.rename(self.v2_keystore_path, backup_path)

            logging.info(f"Successfully migrated v2keystore to v3keystore. "
                         f"Backup saved as: {backup_path}")

            return self.v3_keystore_path, v3_password, "v3"

        except Exception as e:
            logging.error(f"Failed to migrate v2keystore: {e}")
            logging.info("Falling back to v2keystore (migration will retry next time)")

            v2_password = self._generate_v2_password()
            return self.v2_keystore_path, v2_password, "v2"

    def _determine_keystore_version_and_password(self, custom_password: str = None):
        """Determine which keystore to use and generate appropriate password."""

        v2_exists = os.path.exists(self.v2_keystore_path)
        v3_exists = os.path.exists(self.v3_keystore_path)

        if v3_exists:
            password = self._generate_v3_password(custom_password)
            return self.v3_keystore_path, password, "v3"

        if v2_exists:
            return self._migrate_v2_to_v3(custom_password)

        v3_password = self._generate_v3_password(custom_password)
        return self.v3_keystore_path, v3_password, "v3"

    def _generate_v3_password(self, custom_password: str = None) -> str:
        """
        Generate secure password for v3keystore (new keystores).

        In CONTAINER_MODE with KEYSTORE_PASSWORD or SECRETS_STORE_PASSWORD set,
        the environment password is used directly without any system fingerprint
        or path mixing. This ensures consistency across multiple containers
        sharing the same keystore file.

        Args:
            custom_password: Optional custom password provided by the caller.

        Returns:
            Password string for keystore encryption.
        """
        logging.debug(f"_generate_v3_password called - custom_password: {'SET' if custom_password else 'NOT SET'}")

        # In CONTAINER_MODE, prioritise KEYSTORE_PASSWORD for consistency across containers
        container_mode = os.environ.get('CONTAINER_MODE', 'False').lower() == 'true'
        docker_env = os.path.exists('/.dockerenv')
        k8s_env = os.environ.get('KUBERNETES_SERVICE_HOST') is not None
        is_container = container_mode or docker_env or k8s_env

        keystore_password_env = os.environ.get('KEYSTORE_PASSWORD')
        secrets_store_password_env = os.environ.get('SECRETS_STORE_PASSWORD')
        env_password = keystore_password_env or secrets_store_password_env

        if is_container and env_password:
            env_var_name = 'KEYSTORE_PASSWORD' if keystore_password_env else 'SECRETS_STORE_PASSWORD'
            logging.info(f"CONTAINER_MODE: Using {env_var_name} directly for keystore (no system fingerprint mixing)")
            return env_password

        # Non-container mode or no environment password set
        if custom_password:
            logging.debug("Using SystemPasswordGenerator with custom_password")
            # Use SystemPasswordGenerator for custom password strengthening
            return SystemPasswordGenerator(app_name=self.store_name).generate_password(custom_password=custom_password)
        else:
            logging.debug("Using SecureKeyGenerator.generate_keystore_password")
            return self.secure_key_generator.generate_keystore_password(self.v3_keystore_path)
    
    def _generate_v2_password(self) -> str:
        """Generate legacy password for v2keystore (migration only)."""
        return LegacyKeyGenerator.generate_legacy_v2_password(self.v2_keystore_path)

    def __check_auto_imports(self, root_store_path):
        """Securely check and process auto-imports."""
        auto_yaml = os.path.join(root_store_path, 'secrets.yaml')
        
        if not os.path.exists(auto_yaml):
            return
            
        try:
            # Validate file size and permissions
            SecureFileManager.validate_file_size(auto_yaml, max_size=10 * 1024 * 1024)  # 10MB max
            
            # Validate file path
            validated_path = InputValidator.validate_file_path(auto_yaml, allowed_dirs=[root_store_path])
            
            print(f'Performing Auto-Import of Secrets from {auto_yaml}')
            
            with open(validated_path, 'r', encoding='UTF-8') as auto_yaml_file:
                yaml_content = auto_yaml_file.read()
                
                # Validate YAML content for security
                InputValidator.validate_yaml_content(yaml_content)
                
                secrets_data = yaml.safe_load(yaml_content)
                
                if not isinstance(secrets_data, dict) or 'secrets' not in secrets_data:
                    logging.error("Invalid secrets.yaml format: missing 'secrets' key")
                    return
                
                if not isinstance(secrets_data['secrets'], list):
                    logging.error("Invalid secrets.yaml format: 'secrets' must be a list")
                    return
                
                for entry in secrets_data['secrets']:
                    try:
                        self._process_secret_entry(entry, root_store_path)
                    except Exception as e:
                        error_id = secure_error_handler.log_secret_operation_error(
                            "auto_import_entry", 
                            entry.get('name', 'unknown'), 
                            e, 
                            self.store_name
                        )
                        print(f'Failed to import secret entry (Error ID: {error_id})', file=sys.stderr)
                        continue

            # Securely delete the auto-import file
            SecureFileManager.secure_delete(auto_yaml)
            logging.info("Auto-import completed successfully")
            
        except (FileSystemSecurityError, SecurityValidationError) as e:
            error_id = secure_error_handler.log_file_operation_error(
                "auto_import_validation", auto_yaml, e
            )
            logging.error(f"Auto-import security validation failed (Error ID: {error_id})")
        except Exception as e:
            error_id = secure_error_handler.log_file_operation_error(
                "auto_import_processing", auto_yaml, e
            )
            logging.error(f"Auto-import failed (Error ID: {error_id})")

    def _process_secret_entry(self, entry, root_store_path):
        """Process a single secret entry from auto-import."""
        if not isinstance(entry, dict):
            raise ValueError("Secret entry must be a dictionary")
        
        name = entry.get('name')
        value = entry.get('value')
        secret_file = entry.get('file')
        store_as = entry.get('store_as', 'raw')
        
        # Validate secret name
        if not name:
            raise ValueError("Secret entry missing 'name' field")
        
        InputValidator.validate_secret_key(name)
        
        # Process file-based secrets
        if secret_file is not None:
            # Validate file path
            validated_file_path = InputValidator.validate_file_path(
                secret_file, 
                allowed_dirs=[root_store_path, os.getcwd()]
            )
            
            if not os.path.exists(validated_file_path):
                raise FileNotFoundError(f'The file "{secret_file}" specified for {name} does not exist')
            
            # Validate file size
            SecureFileManager.validate_file_size(str(validated_file_path), max_size=64 * 1024)  # 64KB max for secret files
            
            if store_as == 'raw':
                with open(validated_file_path, 'r', encoding='utf-8') as file:
                    value = file.read()
            elif store_as == 'base64':
                with open(validated_file_path, 'rb') as file:
                    file_content = file.read()
                value = base64.b64encode(file_content).decode('utf-8')
            else:
                raise ValueError(f'Unsupported "store_as" value of {store_as} for {name}')
        
        # Validate secret value
        if value is None:
            raise ValueError(f'Missing "value" for {name}. Not imported.')
        
        InputValidator.validate_secret_value(str(value))
        
        # Store the secret
        self.set_secret(name, value)
        print(f'Imported Secret: {name}')

    @deprecated(version='4.0.0', reason="Use SecureKeyGenerator or SystemPasswordGenerator instead")
    def __guid(self, store_p):
        """
        LEGACY METHOD - Generate password for v2keystore migration only.

        ⚠️  SECURITY WARNING: This method uses weak cryptography and should ONLY
        be used for migrating existing v2keystores to v3 format.
        
        DO NOT use for new keystore creation. Use SecureKeyGenerator instead.
        """
        logging.warning("Using deprecated __guid method. This should only be used for v2 keystore migration.")
        return LegacyKeyGenerator.generate_legacy_v2_password(store_p)

    @secure_error_handling("get_secret")
    def get_secret(self, key, default_value=None):
        """
        Retrieve a secret from the local secret store.

        Args:
            key (str): Key of the secret.
            default_value: Default value to return if the secret is not found.

        Returns:
            Secret value if found, else default_value.
        """
        # Validate secret key
        InputValidator.validate_secret_key(key)
        
        entry = self.store.get(key=key)
        if not entry or entry == 'NONE':
            return default_value

        return entry

    def set_persistent_setting(self, key, value):
        if self.get_secret(key):
            self.delete_secret(key)

        self.store.set(key=key, value=value)


    @secure_error_handling("set_secret")
    def set_secret(self, key, value):
        """
        Set a secret in the local secret store.

        Args:
            key (str): Key of the secret.
            value: Value of the secret.
        """
        # Validate inputs
        InputValidator.validate_secret_key(key)
        InputValidator.validate_secret_value(str(value))
        
        if self.get_secret(key):
            self.delete_secret(key)

        self.store.set(key=key, value=value)
        index = self.get_index()
        if key not in index:
            index.append(key)
        self.__set_index(index)

    @secure_error_handling("delete_secret")
    def delete_secret(self, key):
        """
        Delete a secret from the local secret store.

        Args:
            key (str): Key of the secret.
        """
        # Validate secret key
        InputValidator.validate_secret_key(key)
        
        self.store.delete(key=key)
        index = self.get_index()
        while key in index:
            index.remove(key)
        self.__set_index(index)

    def __set_index(self, index: list):
        self.store.set(key=f'{self.store_name}.INDEX', value=json.dumps(index))

    def get_index(self) -> list:
        index = self.get_secret(f'{self.store_name}.INDEX', None)
        if index is None:
            self.__set_index([])
            return []

        return json.loads(index)

    def __is_writeable(self):
        try:
            self.store.set('sstore_save', 'true')
            self.store.delete('sstore_save')
            return True
        except Exception as ex:
            logging.warning(str(ex))
            return False
