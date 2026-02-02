"""
Host Identity Service

Handles Ed25519-based worker authentication:
- Challenge-response verification
- Host registration and reconnection
- Identity management (merge, revoke)
"""

import hashlib
import json
import secrets
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from enum import Enum

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from hearth_controller.db import Host, HostDuplicateCandidate, HostIdentity
from hearth_controller.util import generate_id


class HostStatus(str, Enum):
    """Host status values."""

    PENDING = "pending"  # Awaiting admin approval
    ACTIVE = "active"  # Approved and can accept tasks
    OFFLINE = "offline"  # Not connected
    MERGED = "merged"  # Merged into another host


class IdentityError(Exception):
    """Base exception for identity-related errors."""

    pass


class InvalidSignatureError(IdentityError):
    """Signature verification failed."""

    pass


class IdentityRevokedError(IdentityError):
    """Identity has been revoked."""

    pass


class IdentityService:
    """
    Service for host identity management (async).

    Handles:
    - Challenge generation for authentication
    - Signature verification using Ed25519
    - Host lookup/creation based on public key
    - Identity merging and revocation

    Note: This service does NOT commit transactions. The caller is responsible
    for committing or rolling back the session.
    """

    # Ed25519 key/signature sizes
    PUBLIC_KEY_SIZE = 32
    SIGNATURE_SIZE = 64

    def __init__(self, db: AsyncSession, auto_approve: bool = False):
        """
        Args:
            db: SQLAlchemy async session
            auto_approve: If True, new hosts are automatically approved (status=active)
        """
        self.db = db
        self.auto_approve = auto_approve

    def generate_challenge(self) -> str:
        """
        Generate a random nonce for signature verification.

        Returns:
            Base64-encoded 32-byte random nonce
        """
        return secrets.token_urlsafe(32)

    def verify_signature(self, public_key_b64: str, nonce: str, signature_b64: str) -> bool:
        """
        Verify an Ed25519 signature.

        Args:
            public_key_b64: Base64-encoded Ed25519 public key (32 bytes)
            nonce: The challenge nonce that was signed
            signature_b64: Base64-encoded signature (64 bytes)

        Returns:
            True if signature is valid

        Raises:
            InvalidSignatureError: If signature verification fails or format is invalid
        """
        try:
            # Decode with validation
            public_key_bytes = b64decode(public_key_b64, validate=True)
            signature_bytes = b64decode(signature_b64, validate=True)

            # Validate sizes
            if len(public_key_bytes) != self.PUBLIC_KEY_SIZE:
                raise InvalidSignatureError(
                    f"Invalid public key length: expected {self.PUBLIC_KEY_SIZE}, "
                    f"got {len(public_key_bytes)}"
                )
            if len(signature_bytes) != self.SIGNATURE_SIZE:
                raise InvalidSignatureError(
                    f"Invalid signature length: expected {self.SIGNATURE_SIZE}, "
                    f"got {len(signature_bytes)}"
                )

            nonce_bytes = nonce.encode("utf-8")

            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature_bytes, nonce_bytes)
            return True
        except InvalidSignature:
            raise InvalidSignatureError("Signature verification failed")
        except InvalidSignatureError:
            raise
        except Exception as e:
            raise InvalidSignatureError(f"Invalid key or signature format: {e}")

    def compute_fingerprint(self, public_key_b64: str) -> str:
        """
        Compute SHA256 fingerprint of a public key.

        Note: This is for display purposes only, not for identity matching.

        Args:
            public_key_b64: Base64-encoded public key

        Returns:
            Fingerprint string like "SHA256:abc123..."
        """
        public_key_bytes = b64decode(public_key_b64, validate=True)
        digest = hashlib.sha256(public_key_bytes).digest()
        # Use first 12 bytes, base64 encoded for compact display
        short = b64encode(digest[:12]).decode("ascii").rstrip("=")
        return f"SHA256:{short}"

    async def find_identity_by_public_key(self, public_key_b64: str) -> HostIdentity | None:
        """
        Find an identity by its public key.

        Args:
            public_key_b64: Base64-encoded public key

        Returns:
            HostIdentity if found, None otherwise

        Raises:
            IdentityRevokedError: If identity exists but is revoked
        """
        stmt = select(HostIdentity).where(HostIdentity.public_key == public_key_b64)
        result = await self.db.execute(stmt)
        identity = result.scalar_one_or_none()

        if identity and identity.revoked_at is not None:
            raise IdentityRevokedError(
                f"Identity {identity.id} (fingerprint: {identity.fingerprint}) has been revoked"
            )

        return identity

    async def find_or_create_host(
        self,
        public_key_b64: str,
        claims: dict,
        hardware: dict | None = None,
    ) -> tuple[Host, HostIdentity, bool]:
        """
        Find existing host by public key or create a new one.

        Handles concurrent registration race conditions via IntegrityError retry.

        Args:
            public_key_b64: Base64-encoded Ed25519 public key
            claims: Machine claims {hostname, machine_id, dmi_uuid}
            hardware: Hardware info {cpu_cores, memory_gb, gpu_name, ...}

        Returns:
            Tuple of (host, identity, is_new)
            - host: The Host object
            - identity: The HostIdentity object
            - is_new: True if this is a new host registration

        Raises:
            IdentityRevokedError: If identity exists but is revoked
        """
        # Validate claims
        self._validate_claims(claims)

        # Check if identity already exists
        identity = await self.find_identity_by_public_key(public_key_b64)

        if identity:
            # Known host reconnecting
            host = await self.db.get(Host, identity.host_id)
            if not host:
                raise IdentityError(f"Host {identity.host_id} not found for identity")

            # Update last seen
            identity.last_seen_at = datetime.now(timezone.utc)
            host.last_heartbeat_at = datetime.now(timezone.utc)

            # Update hardware info if provided
            if hardware:
                self._update_host_hardware(host, hardware)

            await self.db.flush()
            return host, identity, False

        # New host registration - but first check if hostname matches an existing host
        import logging

        logger = logging.getLogger(__name__)
        fingerprint = self.compute_fingerprint(public_key_b64)
        hostname = claims.get("hostname", "unknown")[:128]  # Truncate to column size

        # Check if hostname matches an existing host (key loss recovery scenario)
        stmt = select(Host).where(
            Host.name == hostname,
            Host.status != HostStatus.MERGED.value,
        )
        result = await self.db.execute(stmt)
        existing_host = result.scalar_one_or_none()

        if existing_host:
            # Reuse existing host - attach new identity to it
            logger.info(
                f"Reusing existing host {existing_host.id} for hostname {hostname} "
                f"(new public_key fingerprint: {fingerprint})"
            )

            machine_id = claims.get("machine_id")
            dmi_uuid = claims.get("dmi_uuid")
            claim_hostname = claims.get("hostname")
            hw_fp = self._compute_hw_fingerprint(hardware) if hardware else None

            identity = HostIdentity(
                id=generate_id(),
                host_id=existing_host.id,  # Point to existing host
                public_key=public_key_b64,
                fingerprint=fingerprint,
                claims=json.dumps(claims) if claims else None,
                machine_id=machine_id[:64] if machine_id else None,
                dmi_uuid=dmi_uuid[:64] if dmi_uuid else None,
                hostname=claim_hostname[:128] if claim_hostname else None,
                hw_fingerprint=hw_fp,
                last_seen_at=datetime.now(timezone.utc),
            )
            self.db.add(identity)

            # Update existing host to active and refresh hardware info
            existing_host.status = HostStatus.ACTIVE.value
            existing_host.last_heartbeat_at = datetime.now(timezone.utc)
            if hardware:
                self._update_host_hardware(existing_host, hardware)

            try:
                await self.db.flush()
            except IntegrityError:
                await self.db.rollback()
                # Race condition - another request registered same key
                identity = await self.find_identity_by_public_key(public_key_b64)
                if identity:
                    host = await self.db.get(Host, identity.host_id)
                    if host:
                        return host, identity, False
                raise IdentityError("Failed to register identity due to concurrent request")

            return existing_host, identity, False  # Not a "new" host, reused existing

        # Create new host (no existing host with this hostname)
        host = Host(
            id=generate_id(),
            name=hostname,
            status=HostStatus.ACTIVE.value if self.auto_approve else HostStatus.PENDING.value,
            last_heartbeat_at=datetime.now(timezone.utc),
        )

        # Apply hardware info
        if hardware:
            self._update_host_hardware(host, hardware)

        self.db.add(host)

        # Create identity with normalized claim fields for duplicate detection
        machine_id = claims.get("machine_id")
        dmi_uuid = claims.get("dmi_uuid")
        claim_hostname = claims.get("hostname")
        hw_fp = self._compute_hw_fingerprint(hardware) if hardware else None

        identity = HostIdentity(
            id=generate_id(),
            host_id=host.id,
            public_key=public_key_b64,
            fingerprint=fingerprint,
            claims=json.dumps(claims) if claims else None,
            machine_id=machine_id[:64] if machine_id else None,
            dmi_uuid=dmi_uuid[:64] if dmi_uuid else None,
            hostname=claim_hostname[:128] if claim_hostname else None,
            hw_fingerprint=hw_fp,
            last_seen_at=datetime.now(timezone.utc),
        )
        self.db.add(identity)

        # Handle race condition: another request might have registered the same key
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            # Re-fetch the identity that was created by another request
            identity = await self.find_identity_by_public_key(public_key_b64)
            if identity:
                host = await self.db.get(Host, identity.host_id)
                if host:
                    return host, identity, False
            raise IdentityError("Failed to register identity due to concurrent request")

        # Check for potential duplicates after successful registration
        await self._detect_duplicates(host, identity, claims, hardware)

        return host, identity, True

    def _validate_claims(self, claims: dict) -> None:
        """Validate claims dict to prevent abuse."""
        if not isinstance(claims, dict):
            raise IdentityError("Claims must be a dict")

        # Check total size
        claims_json = json.dumps(claims)
        if len(claims_json) > 4096:
            raise IdentityError("Claims too large (max 4KB)")

        # Validate specific fields
        hostname = claims.get("hostname")
        if hostname and len(str(hostname)) > 128:
            raise IdentityError("Hostname too long (max 128 chars)")

    def _update_host_hardware(self, host: Host, hardware: dict) -> None:
        """Update host hardware fields from hardware dict."""
        if not isinstance(hardware, dict):
            return

        if "cpu_cores" in hardware:
            val = hardware["cpu_cores"]
            if isinstance(val, int) and 0 < val < 10000:
                host.cpu_cores = val

        if "memory_gb" in hardware:
            val = hardware["memory_gb"]
            if isinstance(val, (int, float)) and 0 < val < 100000:
                host.memory_gb = float(val)

        if "disk_gb" in hardware:
            val = hardware["disk_gb"]
            if isinstance(val, (int, float)) and 0 < val < 10000000:
                host.disk_gb = float(val)

        if "gpu_name" in hardware:
            val = hardware["gpu_name"]
            if isinstance(val, str) and len(val) <= 128:
                host.gpu_name = val

        if "gpu_vram_gb" in hardware:
            val = hardware["gpu_vram_gb"]
            if isinstance(val, (int, float)) and 0 < val < 10000:
                host.gpu_vram_gb = float(val)

        if "gpu_count" in hardware:
            val = hardware["gpu_count"]
            if isinstance(val, int) and 0 < val < 100:
                host.gpu_count = val

    async def approve_host(self, host_id: str) -> Host:
        """
        Approve a pending host.

        Args:
            host_id: The host ID to approve

        Returns:
            Updated Host object

        Raises:
            IdentityError: If host not found
        """
        host = await self.db.get(Host, host_id)
        if not host:
            raise IdentityError(f"Host {host_id} not found")

        host.status = HostStatus.ACTIVE.value
        await self.db.flush()
        return host

    async def revoke_identity(self, identity_id: str) -> HostIdentity:
        """
        Revoke an identity.

        Args:
            identity_id: The identity ID to revoke

        Returns:
            Updated HostIdentity object

        Raises:
            IdentityError: If identity not found
        """
        identity = await self.db.get(HostIdentity, identity_id)
        if not identity:
            raise IdentityError(f"Identity {identity_id} not found")

        identity.revoked_at = datetime.now(timezone.utc)
        await self.db.flush()
        return identity

    async def merge_hosts(self, target_host_id: str, source_host_id: str) -> Host:
        """
        Merge two hosts (for key loss recovery).

        Moves all identities from source to target, marks source as merged.

        Args:
            target_host_id: The host ID to keep
            source_host_id: The host ID to merge into target

        Returns:
            The target Host object

        Raises:
            IdentityError: If either host not found
        """
        target = await self.db.get(Host, target_host_id)
        source = await self.db.get(Host, source_host_id)

        if not target:
            raise IdentityError(f"Target host {target_host_id} not found")
        if not source:
            raise IdentityError(f"Source host {source_host_id} not found")

        # Get source's identity IDs before moving
        stmt = select(HostIdentity).where(HostIdentity.host_id == source_host_id)
        result = await self.db.execute(stmt)
        source_identities = list(result.scalars())
        source_identity_ids = {i.id for i in source_identities}

        # Move source's identities to target
        for identity in source_identities:
            identity.host_id = target.id

        # Revoke target's old identities (the ones from lost key)
        stmt = select(HostIdentity).where(
            HostIdentity.host_id == target.id,
            HostIdentity.revoked_at.is_(None),
        )
        result = await self.db.execute(stmt)
        for old_identity in result.scalars():
            if old_identity.id not in source_identity_ids:
                old_identity.revoked_at = datetime.now(timezone.utc)

        # Mark source as merged
        source.status = HostStatus.MERGED.value

        await self.db.flush()
        return target

    async def update_capabilities(self, host_id: str, capabilities: dict) -> Host:
        """
        Update host capabilities from probe results.

        Args:
            host_id: The host ID
            capabilities: Dict of probe results

        Returns:
            Updated Host object
        """
        host = await self.db.get(Host, host_id)
        if not host:
            raise IdentityError(f"Host {host_id} not found")

        host.capabilities = json.dumps(capabilities)
        host.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return host

    async def get_host_by_id(self, host_id: str) -> Host | None:
        """Get a host by ID."""
        return await self.db.get(Host, host_id)

    async def list_pending_hosts(self) -> list[Host]:
        """List all hosts pending approval."""
        stmt = select(Host).where(Host.status == HostStatus.PENDING.value)
        result = await self.db.execute(stmt)
        return list(result.scalars())

    async def set_host_offline(self, host_id: str) -> Host | None:
        """Mark a host as offline."""
        host = await self.db.get(Host, host_id)
        if host:
            host.status = HostStatus.OFFLINE.value
            await self.db.flush()
        return host

    async def set_host_active(self, host_id: str) -> Host | None:
        """Mark a host as active (online)."""
        host = await self.db.get(Host, host_id)
        if host and host.status != HostStatus.PENDING.value:
            host.status = HostStatus.ACTIVE.value
            host.last_heartbeat_at = datetime.now(timezone.utc)
            await self.db.flush()
        return host

    def _compute_hw_fingerprint(self, hardware: dict) -> str | None:
        """Compute a stable hardware fingerprint for duplicate detection."""
        if not hardware:
            return None

        parts = []
        if "cpu_cores" in hardware:
            parts.append(f"cpu:{hardware['cpu_cores']}")
        if "memory_gb" in hardware:
            parts.append(f"mem:{int(hardware['memory_gb'])}")
        if "gpu_name" in hardware:
            parts.append(f"gpu:{hardware['gpu_name']}")
        if "gpu_count" in hardware:
            parts.append(f"gpuc:{hardware['gpu_count']}")

        if not parts:
            return None

        canonical = "|".join(sorted(parts))
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    async def _detect_duplicates(
        self,
        new_host: Host,
        new_identity: HostIdentity,
        claims: dict,
        hardware: dict | None,
    ) -> None:
        """Check for potential duplicate hosts and create candidate records.

        Auto-merges if:
        - High confidence match (score >= 100, e.g., dmi_uuid match)
        - Existing host is offline
        """
        import logging

        logger = logging.getLogger(__name__)

        machine_id = claims.get("machine_id")
        dmi_uuid = claims.get("dmi_uuid")
        hw_fp = new_identity.hw_fingerprint

        if not any([machine_id, dmi_uuid, hw_fp]):
            return

        conditions = []
        if dmi_uuid and dmi_uuid != "00000000-0000-0000-0000-000000000000":
            conditions.append(HostIdentity.dmi_uuid == dmi_uuid)
        if machine_id:
            conditions.append(HostIdentity.machine_id == machine_id)
        if hw_fp:
            conditions.append(HostIdentity.hw_fingerprint == hw_fp)

        if not conditions:
            return

        from sqlalchemy import or_

        stmt = (
            select(HostIdentity)
            .join(Host)
            .where(
                or_(*conditions),
                HostIdentity.id != new_identity.id,
                Host.status != HostStatus.MERGED.value,
                HostIdentity.revoked_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        matches = list(result.scalars())

        seen_hosts = set()
        for match in matches:
            if match.host_id in seen_hosts or match.host_id == new_host.id:
                continue
            seen_hosts.add(match.host_id)

            score = 0
            reasons = []

            if dmi_uuid and match.dmi_uuid == dmi_uuid:
                score += 100
                reasons.append(f"dmi_uuid match: {dmi_uuid}")
            if machine_id and match.machine_id == machine_id:
                score += 80
                reasons.append(f"machine_id match: {machine_id}")
            if hw_fp and match.hw_fingerprint == hw_fp:
                score += 40
                reasons.append("hardware fingerprint match")

            if score >= 40:
                # Check if we should auto-merge
                existing_host = await self.db.get(Host, match.host_id)

                # Auto-merge condition: high confidence AND existing host is offline
                if (
                    score >= 100
                    and existing_host
                    and existing_host.status == HostStatus.OFFLINE.value
                ):
                    logger.info(
                        f"Auto-merging duplicate host: new={new_host.id} ({new_host.name}) "
                        f"-> existing={existing_host.id} ({existing_host.name}), "
                        f"reasons={reasons}"
                    )

                    # Move new host's identity to existing host
                    new_identity.host_id = existing_host.id

                    # Mark new host as merged
                    new_host.status = HostStatus.MERGED.value

                    # Activate the existing host
                    existing_host.status = HostStatus.ACTIVE.value
                    existing_host.last_heartbeat_at = datetime.now(timezone.utc)

                    # Update hardware info on existing host
                    if hardware:
                        self._update_host_hardware(existing_host, hardware)

                    await self.db.flush()

                    # Don't create duplicate candidate for auto-merged hosts
                    return

                # For lower confidence or non-offline hosts, create candidate for manual review
                candidate = HostDuplicateCandidate(
                    id=generate_id(),
                    new_host_id=new_host.id,
                    existing_host_id=match.host_id,
                    score=score,
                    reasons_json=json.dumps(reasons),
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(candidate)

        await self.db.flush()

    async def list_duplicate_candidates(self, resolved: bool = False) -> list:
        """List duplicate candidates, optionally filtered by resolution status."""
        stmt = select(HostDuplicateCandidate)
        if resolved:
            stmt = stmt.where(HostDuplicateCandidate.resolved_at.is_not(None))
        else:
            stmt = stmt.where(HostDuplicateCandidate.resolved_at.is_(None))
        stmt = stmt.order_by(HostDuplicateCandidate.score.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars())

    async def resolve_duplicate(
        self,
        candidate_id: str,
        resolution: str,
        user_id: str,
    ) -> HostDuplicateCandidate:
        """Resolve a duplicate candidate with the given action."""
        candidate = await self.db.get(HostDuplicateCandidate, candidate_id)
        if not candidate:
            raise IdentityError(f"Duplicate candidate {candidate_id} not found")

        if candidate.resolved_at:
            raise IdentityError("Candidate already resolved")

        valid_resolutions = ("merged", "approved_new", "blocked", "ignored")
        if resolution not in valid_resolutions:
            raise IdentityError(f"Invalid resolution: {resolution}")

        if resolution == "merged":
            await self.merge_hosts(candidate.existing_host_id, candidate.new_host_id)

        candidate.resolution = resolution
        candidate.resolved_at = datetime.now(timezone.utc)
        candidate.resolved_by_user_id = user_id
        await self.db.flush()
        return candidate
