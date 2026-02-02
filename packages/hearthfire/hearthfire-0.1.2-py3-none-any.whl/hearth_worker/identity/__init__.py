"""
Worker Identity Module

Handles Ed25519 key generation, storage, and signing for worker authentication.
"""

from hearth_worker.identity.manager import IdentityManager
from hearth_worker.identity.claims import collect_claims, collect_hardware

__all__ = ["IdentityManager", "collect_claims", "collect_hardware"]
