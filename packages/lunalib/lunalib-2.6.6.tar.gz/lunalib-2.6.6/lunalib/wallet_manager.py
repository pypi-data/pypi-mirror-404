"""Compatibility shim for legacy imports.

Allows `import lunalib.wallet_manager` to work by forwarding to core wallet manager.
"""

from .core.wallet_manager import WalletStateManager, get_wallet_manager

__all__ = ["WalletStateManager", "get_wallet_manager"]
