"""
Identity Manager

Handles Ed25519 key generation, storage, and signing for worker authentication.
"""

import os
from base64 import b64encode
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


class IdentityManager:
    """
    Manages worker identity (Ed25519 keypair).

    Identity is stored at:
    - Private key: /var/lib/hearth/identity/host_ed25519.key
    - Host ID: /var/lib/hearth/identity/host_id

    The private key is generated on first run and never leaves the machine.
    """

    DEFAULT_IDENTITY_DIR = Path("/var/lib/hearth/identity")
    PRIVATE_KEY_FILE = "host_ed25519.key"
    HOST_ID_FILE = "host_id"

    def __init__(self, identity_dir: Path | str | None = None):
        """
        Args:
            identity_dir: Directory to store identity files.
                          Defaults to /var/lib/hearth/identity
        """
        if identity_dir is None:
            identity_dir = self.DEFAULT_IDENTITY_DIR
        self.identity_dir = Path(identity_dir)
        self._private_key: Ed25519PrivateKey | None = None
        self._host_id: str | None = None

    @property
    def private_key_path(self) -> Path:
        return self.identity_dir / self.PRIVATE_KEY_FILE

    @property
    def host_id_path(self) -> Path:
        return self.identity_dir / self.HOST_ID_FILE

    def ensure_identity(self) -> None:
        """
        Ensure identity exists, generating if necessary.

        Creates the identity directory and generates a new keypair
        if one doesn't exist.

        Raises:
            PermissionError: If identity directory is not writable
        """
        self.identity_dir.mkdir(parents=True, exist_ok=True)
        self._check_identity_dir_writable()

        if self.private_key_path.exists():
            self._load_private_key()
        else:
            self._generate_keypair()

    def _check_identity_dir_writable(self) -> None:
        """Verify identity directory is writable, fail fast if not."""
        test_file = self.identity_dir / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            raise PermissionError(
                f"Identity directory not writable: {self.identity_dir}. "
                "Cannot persist worker identity key. "
                "Check directory permissions or run as appropriate user."
            )

    def _generate_keypair(self) -> None:
        """Generate a new Ed25519 keypair and save to disk."""
        self._private_key = Ed25519PrivateKey.generate()

        # Serialize private key in PEM format
        key_bytes = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Write with secure permissions (0600)
        self.private_key_path.write_bytes(key_bytes)
        os.chmod(self.private_key_path, 0o600)

    def _load_private_key(self) -> None:
        """Load private key from disk."""
        key_bytes = self.private_key_path.read_bytes()
        loaded_key = serialization.load_pem_private_key(
            key_bytes,
            password=None,
        )
        # Type assertion - we only store Ed25519 keys
        if not isinstance(loaded_key, Ed25519PrivateKey):
            raise ValueError("Loaded key is not an Ed25519 private key")
        self._private_key = loaded_key

    @property
    def private_key(self) -> Ed25519PrivateKey:
        """Get the private key, loading if necessary."""
        if self._private_key is None:
            self.ensure_identity()
        return self._private_key  # type: ignore

    @property
    def public_key(self) -> Ed25519PublicKey:
        """Get the public key."""
        return self.private_key.public_key()

    def get_public_key_bytes(self) -> bytes:
        """Get raw public key bytes (32 bytes for Ed25519)."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def get_public_key_base64(self) -> str:
        """Get public key as base64 string."""
        return b64encode(self.get_public_key_bytes()).decode("ascii")

    def sign(self, data: bytes) -> bytes:
        """
        Sign data with the private key.

        Args:
            data: Data to sign

        Returns:
            Ed25519 signature (64 bytes)
        """
        return self.private_key.sign(data)

    def sign_base64(self, data: str | bytes) -> str:
        """
        Sign data and return base64-encoded signature.

        Args:
            data: Data to sign (str will be UTF-8 encoded)

        Returns:
            Base64-encoded signature
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        signature = self.sign(data)
        return b64encode(signature).decode("ascii")

    def save_host_id(self, host_id: str) -> None:
        """
        Save host_id received from controller.

        Args:
            host_id: The host ID assigned by the controller
        """
        self.identity_dir.mkdir(parents=True, exist_ok=True)
        self.host_id_path.write_text(host_id)
        self._host_id = host_id

    def get_host_id(self) -> str | None:
        """
        Get saved host_id, if any.

        Returns:
            Host ID or None if not yet registered
        """
        if self._host_id:
            return self._host_id

        if self.host_id_path.exists():
            self._host_id = self.host_id_path.read_text().strip()
            return self._host_id

        return None

    def has_identity(self) -> bool:
        """Check if identity (private key) exists."""
        return self.private_key_path.exists()

    def is_registered(self) -> bool:
        """Check if this worker is registered (has host_id)."""
        return self.get_host_id() is not None
