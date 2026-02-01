import json
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import logging as logger
import logging
import hashlib
import secrets
import platform
import socket
import subprocess
import os
import uuid
import base64
import hmac
import time
import tempfile
from typing import Optional, Dict, List
from pathlib import Path
from filelock import FileLock, Timeout as FileLockTimeout

class SystemPasswordGenerator:
    """
        Generates secure passwords based on unique system attributes.
        Supports both bare metal and containerized environments.
        Designed to work with PasswordProtectedKeystoreWithHMAC.
        """

    def __init__(self, app_name: str = "keystore", salt: Optional[str] = None, min_entropy: int = 256):
        """
        Initialize the password generator.

        Args:
            app_name: Application name for consistent fingerprinting
            salt: Optional custom salt for additional security
            min_entropy: Minimum entropy bits required (default 256)
        """
        self.app_name = app_name
        self.salt = salt or self._generate_installation_salt()
        self.min_entropy = min_entropy
        self._system_fingerprint = None

    def generate_password(self, custom_password: Optional[str] = None, user_override: bool = False) -> str:
        """
        Generate a secure password using system attributes or custom input.

        Args:
            custom_password: Optional user-provided password override
            user_override: If True, use only custom_password without system strengthening

        Returns:
            Secure password string suitable for keystore usage
        """
        # Debug logging
        logger.debug(f"SystemPasswordGenerator.generate_password called - custom_password: {'SET' if custom_password else 'NOT SET'}, user_override: {user_override}")
        
        # Check for container-specific environment variables first
        keystore_password_env = os.environ.get('KEYSTORE_PASSWORD')
        secrets_store_password_env = os.environ.get('SECRETS_STORE_PASSWORD')
        container_password = keystore_password_env or secrets_store_password_env
        
        # Debug logging for environment variables
        if keystore_password_env:
            logger.info("Found KEYSTORE_PASSWORD environment variable")
        elif secrets_store_password_env:
            logger.info("Found SECRETS_STORE_PASSWORD environment variable")
        else:
            logger.debug("No keystore password environment variables found")
        
        # In container environments, prioritize environment variables for persistence
        env_type = self._detect_environment()
        container_mode = os.environ.get('CONTAINER_MODE', 'False').lower() == 'true'
        logger.debug(f"Environment type: {env_type}, CONTAINER_MODE: {container_mode}")
        
        # CRITICAL FIX: Check container environment BEFORE custom_password logic
        if container_password and (env_type == "container" or container_mode):
            env_var_name = "KEYSTORE_PASSWORD" if keystore_password_env else "SECRETS_STORE_PASSWORD"
            logger.info(f"Using container environment password from {env_var_name} for keystore persistence")
            logger.debug("Container environment detected - using environment password WITHOUT system fingerprint strengthening")
            # In containers, use the environment password directly for consistency
            return container_password
        
        if custom_password and user_override:
            logger.info("Using user-provided password without system strengthening")
            return custom_password
        elif custom_password:
            logger.info("Using user-provided password with system strengthening")
            return self._strengthen_user_password(custom_password)
        else:
            logger.info("Generating system-based password")
            return self._generate_system_password()

    def _generate_system_password(self) -> str:
        """Generate password based on system fingerprint."""
        fingerprint = self._get_system_fingerprint()

        # Use PBKDF2 for key derivation with high iteration count
        # Using same algorithm as your keystore for consistency
        password_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            fingerprint.encode('utf-8'),
            self.salt.encode('utf-8'),
            iterations=100000,  # Higher than keystore's 20k for master password
            dklen=32  # 256-bit key
        )

        # Convert to a string format that's safe and deterministic
        return base64.urlsafe_b64encode(password_bytes).decode('utf-8')

    def _strengthen_user_password(self, password: str) -> str:
        """Strengthen user-provided password with system entropy."""
        system_entropy = self._get_system_fingerprint()

        # Combine user password with system fingerprint
        combined = f"{password}:{system_entropy}:{self.app_name}"

        # Use PBKDF2 to strengthen
        strengthened = hashlib.pbkdf2_hmac(
            'sha256',
            combined.encode('utf-8'),
            self.salt.encode('utf-8'),
            iterations=100_000,
            dklen=32
        )

        return base64.urlsafe_b64encode(strengthened).decode('utf-8')

    def _get_system_fingerprint(self) -> str:
        """
        Generate a unique system fingerprint that works in various environments.

        Returns:
            Deterministic system fingerprint string
        """
        if self._system_fingerprint:
            return self._system_fingerprint

        fingerprint_components = []

        try:
            # 1. Platform information (always available)
            fingerprint_components.extend([
                platform.system(),
                platform.release(),
                platform.machine(),
                platform.processor() or "unknown_processor"
            ])

            # 2. Network-based identifiers
            try:
                hostname = socket.gethostname()
                fingerprint_components.append(hostname)
                # Get primary network interface info if available
                try:
                    import netifaces
                    gateways = netifaces.gateways()
                    default_gateway = gateways.get('default', {})
                    if default_gateway:
                        default_interface = list(default_gateway.values())[0][1]
                        fingerprint_components.append(default_interface)
                except ImportError:
                    logger.debug("netifaces not available, skipping network interface fingerprinting")
            except Exception as e:
                logger.debug(f"Could not get network info: {e}")
                fingerprint_components.append("unknown_network")

            # 3. Environment detection and specific fingerprinting
            env_type = self._detect_environment()
            fingerprint_components.append(env_type)

            if env_type == "container":
                fingerprint_components.extend(self._get_container_fingerprint())
            else:
                fingerprint_components.extend(self._get_hardware_fingerprint())

            # 4. File system identifiers
            fingerprint_components.extend(self._get_filesystem_fingerprint())

            # 5. Application-specific identifiers
            fingerprint_components.append(self.app_name)

        except Exception as e:
            logger.error(f"Error generating system fingerprint: {e}")
            # Fallback to basic identifiers
            fingerprint_components = [
                platform.system(),
                socket.gethostname(),
                self.app_name,
                str(secrets.randbits(64))  # Random fallback
            ]

        # Combine all components and hash them
        combined = ":".join(str(component) for component in fingerprint_components if component)
        self._system_fingerprint = hashlib.sha256(combined.encode()).hexdigest()

        logger.debug(f"Generated system fingerprint from {len(fingerprint_components)} components")
        return self._system_fingerprint

    def _detect_environment(self) -> str:
        """Detect if running in container, VM, or bare metal."""
        # Check for common container indicators
        container_indicators = [
            os.path.exists('/.dockerenv'),
            os.environ.get('container') is not None,
            os.path.exists('/proc/1/cgroup') and self._check_cgroup_container(),
            os.environ.get('KUBERNETES_SERVICE_HOST') is not None,
        ]

        if any(container_indicators):
            return "container"

        # Check for VM indicators
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()
                vm_indicators = ['hypervisor', 'vmware', 'virtualbox', 'xen', 'kvm']
                if any(indicator in cpuinfo for indicator in vm_indicators):
                    return "vm"
        except (FileNotFoundError, PermissionError):
            pass

        return "bare_metal"

    def _check_cgroup_container(self) -> bool:
        """Check cgroup for container indicators."""
        try:
            with open('/proc/1/cgroup', 'r') as f:
                cgroup_content = f.read()
                return 'docker' in cgroup_content or 'kubepods' in cgroup_content
        except (FileNotFoundError, PermissionError):
            return False

    def _get_container_fingerprint(self) -> List[str]:
        """Get container-specific identifiers."""
        components = []

        # Container ID from cgroup
        try:
            with open('/proc/self/cgroup', 'r') as f:
                cgroup_info = f.read()
                components.append(hashlib.sha256(cgroup_info.encode()).hexdigest()[:16])
        except (FileNotFoundError, PermissionError):
            pass

        # Mount namespace
        try:
            mount_ns = os.readlink('/proc/self/ns/mnt')
            components.append(mount_ns)
        except OSError:
            pass

        # Container environment variables
        container_vars = ['HOSTNAME', 'PATH', 'HOME']
        for var in container_vars:
            if os.environ.get(var):
                components.append(f"{var}={os.environ[var]}")

        return components

    def _collect_cpu_info(self) -> List[str]:
        """Collect CPU-related components for the hardware fingerprint.

        Reads /proc/cpuinfo and extracts the first processor line and model name.

        Returns:
            List of CPU identifier strings.
        """
        components = []
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                for line in cpuinfo.split('\n'):
                    if 'processor' in line and '0' in line:
                        components.append(line.strip())
                    elif 'model name' in line:
                        components.append(line.strip())
                        break
        except (FileNotFoundError, PermissionError):
            pass
        return components

    def _collect_memory_info(self) -> List[str]:
        """Collect memory-related components for the hardware fingerprint.

        Reads /proc/meminfo and extracts the total memory value.

        Returns:
            List of memory identifier strings.
        """
        components = []
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n')[:3]:
                    if 'MemTotal' in line:
                        components.append(line.strip())
                        break
        except (FileNotFoundError, PermissionError):
            pass
        return components

    def _collect_dmi_info(self) -> List[str]:
        """Collect DMI (Desktop Management Interface) components for the hardware fingerprint.

        Reads product UUID, board serial, and chassis serial from sysfs on Linux.

        Returns:
            List of DMI identifier strings.
        """
        components = []
        dmi_paths = [
            '/sys/class/dmi/id/product_uuid',
            '/sys/class/dmi/id/board_serial',
            '/sys/class/dmi/id/chassis_serial'
        ]
        for path in dmi_paths:
            try:
                with open(path, 'r') as f:
                    value = f.read().strip()
                    if value and value != 'To be filled by O.E.M.':
                        components.append(f"{os.path.basename(path)}={value}")
            except (FileNotFoundError, PermissionError):
                continue
        return components

    def _collect_mac_addresses(self) -> List[str]:
        """Collect MAC address components for the hardware fingerprint.

        Uses netifaces (if available) to find the first valid MAC address from
        physical network interfaces (eth*, en*, wlan*).

        Returns:
            List of MAC address identifier strings.
        """
        components = []
        try:
            import netifaces
            interfaces = netifaces.interfaces()
            for interface in interfaces:
                if interface.startswith(('eth', 'en', 'wlan')):
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_LINK in addrs:
                        mac = addrs[netifaces.AF_LINK][0]['addr']
                        if mac and mac != '00:00:00:00:00:00':
                            components.append(f"mac_{interface}={mac}")
                            break  # Only need one MAC
        except ImportError:
            logger.debug("netifaces not available for MAC address fingerprinting")
        return components

    def _get_hardware_fingerprint(self) -> List[str]:
        """Get hardware-specific identifiers for bare metal.

        Collects CPU, memory, DMI, and MAC address information to build
        a unique hardware fingerprint.

        Returns:
            List of hardware identifier strings.
        """
        components = []
        components.extend(self._collect_cpu_info())
        components.extend(self._collect_memory_info())
        components.extend(self._collect_dmi_info())
        components.extend(self._collect_mac_addresses())
        return components

    def _get_filesystem_fingerprint(self) -> List[str]:
        """Get filesystem-specific identifiers."""
        components = []

        # Root filesystem UUID (Linux)
        try:
            result = subprocess.run(['blkid', '-o', 'value', '-s', 'UUID', '/dev/root'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                components.append(f"root_uuid={result.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Boot time (system uptime reference)
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('btime'):
                        boot_time = line.strip().split()[1]
                        # Use boot time modulo to avoid exact timestamp but maintain uniqueness
                        components.append(f"boot_ref={int(boot_time) % 86400}")  # Day-relative boot time
                        break
        except (FileNotFoundError, PermissionError):
            pass

        # Application directory stat
        try:
            app_dir = Path(__file__).parent
            stat_info = app_dir.stat()
            components.append(f"app_dir_inode={stat_info.st_ino}")
        except (OSError, AttributeError):
            pass

        return components

    def _generate_installation_salt(self) -> str:
        """Generate a consistent salt for this installation."""
        # Create a salt based on multiple system factors
        salt_components = [
            platform.node(),  # Network node name
            str(uuid.getnode()),  # Hardware address
            platform.machine(),
            self.app_name
        ]

        combined = ":".join(salt_components)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

class PasswordProtectedKeystoreWithHMAC:
    """
    PasswordProtectedKeystoreWithHMAC provides a mechanism to securely store key-value pairs
    in a file. The data is protected using encryption and integrity is ensured by HMAC.

    This class supports multi-process access through file locking, making it safe to use
    in containerised environments where multiple workers share the same keystore file.

    Methods:
        __init__(keystore_path, password, lock_timeout):
            Initialises the keystore with the provided path, password, and optional lock timeout.

        _derive_key(salt):
            Derives an encryption key from the password and salt using PBKDF2.

        _generate_hmac(data, key):
            Generates an HMAC for the given data using the derived key.

        _verify_hmac(data, key, expected_hmac):
            Verifies the HMAC for the given data against the expected HMAC.

        _load_keystore():
            Loads the keystore from the file, verifying its integrity and returning the stored data.

        _save_keystore(data):
            Saves the provided data to the keystore file atomically, including the generated HMAC for integrity.

        set(key, value):
            Adds or updates a key-value pair in the keystore (thread-safe).

        get(key):
            Retrieves a value from the keystore by its key (thread-safe).

        delete(key):
            Deletes a key-value pair from the keystore (thread-safe).

    Attributes:
        lock_timeout (int): Maximum time in seconds to wait for acquiring the file lock.
            Default is 30 seconds. Set via KEYSTORE_LOCK_TIMEOUT environment variable.
    """

    # Default lock timeout in seconds
    DEFAULT_LOCK_TIMEOUT = 30

    def __init__(self, keystore_path, password, lock_timeout: int = None):
        """
        Initialise the keystore with file locking support for multi-process safety.

        Args:
            keystore_path: Path to the keystore file.
            password: Password for encrypting/decrypting the keystore.
            lock_timeout: Maximum time in seconds to wait for the file lock.
                         Defaults to KEYSTORE_LOCK_TIMEOUT env var or 30 seconds.
        """
        self.keystore_path = keystore_path
        self.password = password.encode()

        # Configure lock timeout from parameter, environment, or default
        if lock_timeout is not None:
            self.lock_timeout = lock_timeout
        else:
            self.lock_timeout = int(os.environ.get('KEYSTORE_LOCK_TIMEOUT', self.DEFAULT_LOCK_TIMEOUT))

        # Create file lock for multi-process synchronisation
        self.lock_path = f"{keystore_path}.lock"
        self._file_lock = FileLock(self.lock_path, timeout=self.lock_timeout)

        logging.debug(f"Keystore initialised with lock timeout: {self.lock_timeout}s, lock file: {self.lock_path}")

    def _derive_key(self, salt):
        """
        Args:
            salt: A cryptographic salt used for deriving the key, which should be a byte sequence.

        Returns:
            A base64-encoded, url-safe byte sequence representing the derived cryptographic key.
        """
        # TODO: Increase iterations to 600,000+ per OWASP PBKDF2-SHA256 guidance.
        # Requires keystore version migration (v3 -> v4) to avoid breaking existing keystores.
        kdf = PBKDF2HMAC(
            algorithm=SHA256(),
            length=32,
            salt=salt,
            iterations=20_000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(self.password))

    def _generate_hmac(self, data, key):
        """
        Args:
            data: The data that needs to be protected with an HMAC.
            key: The cryptographic key used for HMAC generation.
        """
        hmac = HMAC(key, SHA256(), backend=default_backend())
        hmac.update(data)
        return hmac.finalize()

    def _verify_hmac(self, data, key, expected_hmac):
        """
        Verify HMAC using constant-time comparison to prevent timing attacks.

        Args:
            data: The data for which the HMAC is to be verified.
            key: The secret key used for the HMAC generation.
            expected_hmac: The HMAC value that is expected for the provided data and key combination.

        Returns:
            bool: True if the computed HMAC matches the expected HMAC, False otherwise.
        """
        start_time = time.time()
        
        try:
            # Compute expected HMAC
            hmac_obj = HMAC(key, SHA256(), backend=default_backend())
            hmac_obj.update(data)
            computed_digest = hmac_obj.finalize()
            
            # Use constant-time comparison
            result = hmac.compare_digest(computed_digest, expected_hmac)
            
            # Ensure minimum time to prevent timing analysis
            self._ensure_minimum_time(start_time, 0.01)  # 10ms minimum
            return result
            
        except Exception:
            # Even exceptions should take constant time
            dummy_hmac = b'0' * 32  # SHA256 output size
            hmac.compare_digest(dummy_hmac, expected_hmac)
            self._ensure_minimum_time(start_time, 0.01)
            return False

    def _ensure_minimum_time(self, start_time: float, min_time: float):
        """Ensure operation takes minimum time to prevent timing analysis."""
        elapsed = time.time() - start_time
        if elapsed < min_time:
            time.sleep(min_time - elapsed)

    def _load_keystore(self):
        """
        Loads and decrypts the keystore data from a specified file path.

        If the keystore file exists, it reads the file content and extracts the salt,
        encrypted data, and HMAC. The method then derives the key using the extracted
        salt and verifies the HMAC to ensure data integrity. If the HMAC verification
        fails, a ValueError is raised indicating potential file tampering. After successful
        verification, the method decrypts the data using the derived key and
        returns the decrypted JSON content. If the file does not exist, an empty
        dictionary is returned.

        Raises:
            ValueError: If HMAC verification fails, indicating possible tampering.

        Returns:
            dict: The decrypted content of the keystore file as a dictionary, or an
            empty dictionary if the keystore file does not exist.
        """
        if os.path.exists(self.keystore_path):
            with open(self.keystore_path, 'rb') as file:
                # Read the entire file content
                file_content = file.read()

                # Check for minimum file size
                if len(file_content) < 48:  # 16 salt + 32 HMAC minimum
                    raise ValueError(f"Keystore file {self.keystore_path} is corrupted (too small).")

                # Extract the salt, encrypted data, and HMAC
                salt = file_content[:16]  # First 16 bytes
                encrypted_data = file_content[16:-32]  # Middle bytes
                stored_hmac = file_content[-32:]  # Last 32 bytes

                # Derive the key and verify the HMAC
                derived_key = self._derive_key(salt)
                if not self._verify_hmac(salt + encrypted_data, derived_key, stored_hmac):
                    raise ValueError("HMAC verification failed: File may have been tampered with.")

                # Decrypt the data
                cipher_suite = Fernet(derived_key)
                decrypted_data = cipher_suite.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
        return {}

    def _save_keystore(self, data):
        """
        Save data to the keystore using atomic write operations.

        This method writes data to a temporary file first, then atomically
        renames it to the target path. This ensures that the keystore file
        is never left in a partially-written state, even if the process is
        interrupted during the write operation.

        Args:
            data: The data to be saved in the keystore, which will be encrypted and stored securely.

        Raises:
            OSError: If the atomic rename operation fails.
            Exception: If encryption or file operations fail.
        """
        # Generate a random 16-byte salt
        salt = os.urandom(16)

        # Derive the key
        derived_key = self._derive_key(salt)
        cipher_suite = Fernet(derived_key)

        # Encrypt the data
        encrypted_data = cipher_suite.encrypt(json.dumps(data).encode())

        # Generate the HMAC
        hmac_value = self._generate_hmac(salt + encrypted_data, derived_key)

        # Prepare the complete file content
        file_content = salt + encrypted_data + hmac_value

        # Use atomic write: write to temp file, then rename
        dir_name = os.path.dirname(self.keystore_path) or '.'
        fd = None
        temp_path = None

        try:
            # Create temporary file in the same directory to ensure atomic rename works
            fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp', prefix='keystore_')

            # Write all content to the temporary file
            with os.fdopen(fd, 'wb') as temp_file:
                fd = None  # os.fdopen takes ownership of the file descriptor
                temp_file.write(file_content)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Ensure data is written to disk

            # Atomic rename (on POSIX systems this is atomic, on Windows it replaces)
            os.replace(temp_path, self.keystore_path)
            temp_path = None  # Successfully moved, don't try to clean up

            logging.debug(f"Keystore saved atomically to {self.keystore_path}")

        except Exception as e:
            logging.error(f"Failed to save keystore atomically: {e}")
            raise
        finally:
            # Clean up the file descriptor if still open
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass

            # Clean up temporary file if it still exists
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def set(self, key, value):
        """
        Add or update a key-value pair in the keystore (thread-safe).

        This method acquires an exclusive file lock before modifying the keystore,
        ensuring that concurrent processes do not corrupt the data.

        Args:
            key: The key to be stored in the keystore.
            value: The value associated with the key to be stored.

        Raises:
            FileLockTimeout: If the lock cannot be acquired within the timeout period.
        """
        try:
            with self._file_lock:
                keystore = self._load_keystore()
                keystore[key] = value
                self._save_keystore(keystore)
                logging.debug(f"Key '{key}' stored successfully.")
        except FileLockTimeout:
            logging.error(f"Timeout acquiring lock to set key '{key}' in keystore after {self.lock_timeout}s")
            raise

    def get(self, key):
        """
        Retrieve a value from the keystore by its key (thread-safe).

        This method acquires a file lock before reading the keystore,
        ensuring consistent reads even when other processes are writing.

        Args:
            key: The key whose associated value is to be returned.

        Returns:
            The value corresponding to the specified key if it exists, otherwise None.

        Raises:
            FileLockTimeout: If the lock cannot be acquired within the timeout period.
        """
        try:
            with self._file_lock:
                keystore = self._load_keystore()
                logging.debug(f"Retrieving Key '{key}'")
                return keystore.get(key)
        except FileLockTimeout:
            logging.error(f"Timeout acquiring lock to get key '{key}' from keystore after {self.lock_timeout}s")
            raise

    def get_all(self):
        """
        Retrieve all key-value pairs from the keystore (thread-safe).

        This method acquires a file lock before reading the keystore.

        Returns:
            Dictionary containing all key-value pairs in the keystore.

        Raises:
            FileLockTimeout: If the lock cannot be acquired within the timeout period.
        """
        try:
            with self._file_lock:
                return self._load_keystore()
        except FileLockTimeout:
            logging.error(f"Timeout acquiring lock to get all keys from keystore after {self.lock_timeout}s")
            raise

    def delete(self, key):
        """
        Delete a key-value pair from the keystore (thread-safe).

        This method acquires an exclusive file lock before modifying the keystore,
        ensuring that concurrent processes do not corrupt the data.

        Args:
            key: The key to be deleted from the keystore.

        Raises:
            FileLockTimeout: If the lock cannot be acquired within the timeout period.
        """
        try:
            with self._file_lock:
                keystore = self._load_keystore()
                if key in keystore:
                    del keystore[key]
                    self._save_keystore(keystore)
                    logging.debug(f"Key '{key}' deleted successfully.")
                else:
                    logging.debug(f"Key '{key}' not found in the keystore.")
        except FileLockTimeout:
            logging.error(f"Timeout acquiring lock to delete key '{key}' from keystore after {self.lock_timeout}s")
            raise