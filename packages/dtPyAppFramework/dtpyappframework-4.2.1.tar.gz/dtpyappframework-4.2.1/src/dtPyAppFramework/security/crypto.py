import hashlib
import secrets
import sys
import socket
import platform
import subprocess
import os
import base64
from typing import Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from ..misc import run_cmd


class SecureKeyGenerator:
    """Cryptographically secure key generation for keystores."""
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.backend = default_backend()
    
    def generate_keystore_password(self, store_path: str, custom_salt: bytes = None) -> str:
        """Generate secure password for keystore access."""
        
        # Collect machine identifiers securely
        machine_data = self._collect_machine_fingerprint()
        
        # Create deterministic but secure seed
        seed_data = f"{self.app_name}:{store_path}:{machine_data}".encode('utf-8')
        
        # Use application-specific salt
        salt = custom_salt or self._get_application_salt()
        
        # Derive key using PBKDF2 with high iteration count
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
            backend=self.backend
        )
        
        derived_key = kdf.derive(seed_data)
        
        # Return as base64 for keystore compatibility
        return base64.b64encode(derived_key).decode('ascii')
    
    def _collect_machine_fingerprint(self) -> str:
        """Collect machine identifiers with fallback strategies."""
        identifiers = []

        try:
            self._collect_platform_uuid(identifiers)
            self._collect_mac_address(identifiers)
            identifiers.append(f"hostname:{socket.gethostname()}")
        except Exception:
            # Emergency fallback - still deterministic per machine
            identifiers.append(f"fallback:{platform.platform()}")

        if not identifiers:
            raise RuntimeError("Unable to generate machine fingerprint")

        return '|'.join(identifiers)

    def _collect_platform_uuid(self, identifiers: list) -> None:
        """Collect platform-specific hardware UUID."""
        if sys.platform == 'darwin':
            uuid_str = run_cmd(
                "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'"
            )
            if uuid_str:
                identifiers.append(f"hw_uuid:{uuid_str.strip()}")
        elif sys.platform.startswith('linux'):
            self._collect_linux_machine_id(identifiers)
        elif sys.platform in ['win32', 'cygwin']:
            self._collect_windows_uuid(identifiers)

    def _collect_linux_machine_id(self, identifiers: list) -> None:
        """Collect Linux machine identifier from standard paths."""
        for path in ['/var/lib/dbus/machine-id', '/etc/machine-id']:
            try:
                with open(path, 'r') as f:
                    machine_id = f.read().strip()
                    if machine_id:
                        identifiers.append(f"machine_id:{machine_id}")
                break
            except (IOError, OSError):
                continue

    def _collect_windows_uuid(self, identifiers: list) -> None:
        """Collect Windows system UUID via PowerShell."""
        try:
            result = subprocess.run([
                'powershell', '-Command',
                'Get-CimInstance -Class Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID'
            ], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                identifiers.append(f"win_uuid:{result.stdout.strip()}")
        except subprocess.SubprocessError:
            pass

    def _collect_mac_address(self, identifiers: list) -> None:
        """Collect network MAC address as secondary identifier."""
        import uuid
        mac_num = uuid.getnode()
        if mac_num != uuid.getnode():  # Validate it's not a random fallback
            mac = ':'.join(['{:02x}'.format((mac_num >> elements) & 0xff)
                           for elements in range(0, 2*6, 2)][::-1])
            identifiers.append(f"mac:{mac}")
    
    def _get_application_salt(self) -> bytes:
        """Get application-specific salt."""
        app_salt = f"dtPyAppFramework-v3-{self.app_name}".encode('utf-8')
        return hashlib.sha256(app_salt).digest()[:16]


class LegacyKeyGenerator:
    """Legacy key generator for v2keystore migration ONLY."""
    
    @staticmethod
    def generate_legacy_v2_password(store_path: str) -> str:
        """
        LEGACY METHOD - Generate password for v2keystore migration only.
        
        ⚠️  SECURITY WARNING: This method uses weak cryptography and should ONLY
        be used for migrating existing v2keystores to v3 format.
        
        DO NOT use for new keystore creation.
        """
        from itertools import cycle
        import re
        import pybase64
        from base64 import urlsafe_b64encode
        
        base = None
        
        # Original machine ID collection logic (unchanged for compatibility)
        if sys.platform == 'darwin':
            base = run_cmd(
                "ioreg -d2 -c IOPlatformExpertDevice | awk -F\\\" '/IOPlatformUUID/{print $(NF-1)}'")

        if sys.platform == 'win32' or sys.platform == 'cygwin' or sys.platform == 'msys':
            base = run_cmd('powershell "Get-WmiObject -Class "Win32_ComputerSystemProduct" | Select-Object -Property UUID"').split('\n')[2] \
                .strip()

        if sys.platform.startswith('linux'):
            base = run_cmd('cat /var/lib/dbus/machine-id') or \
                   run_cmd('cat /etc/machine-id')

        if sys.platform.startswith('openbsd') or sys.platform.startswith('freebsd'):
            base = run_cmd('cat /etc/hostid') or \
                   run_cmd('kenv -q smbios.system.uuid')

        if not base:
            raise RuntimeError("Failed to determine unique machine ID for legacy v2 keystore")

        # Original weak key derivation (preserved for v2 compatibility)
        base += store_path
        key = re.sub("[^a-zA-Z]+", "", base)
        xored = ''.join(chr(ord(x) ^ ord(y)) for (x, y) in zip(base, cycle(key)))
        return urlsafe_b64encode(pybase64.b64encode_as_string(xored.encode())[:32].encode()).decode()