
from lunalib.storage.database import WalletDatabase, get_default_wallet_dir, resolve_wallet_db_path
import json


class WalletDB:
    def __init__(self, data_dir=None):
        # data_dir is kept for compatibility, but db_path is passed to WalletDatabase
        import os
        self.data_dir = data_dir or get_default_wallet_dir()
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_path = resolve_wallet_db_path(
            os.path.join(self.data_dir, "wallets.db") if data_dir else None
        )
        print(f"[WalletDB] data_dir: {self.data_dir}")
        print(f"[WalletDB] db_path: {self.db_path}")
        self.db = WalletDatabase(db_path=self.db_path)

    def save_wallet(self, address, label, public_key, encrypted_private_key, is_locked, created, balance, available_balance):
        # Compose wallet_data dict for WalletDatabase
        wallet_data = {
            'address': address,
            'label': label,
            'public_key': public_key,
            'encrypted_private_key': encrypted_private_key,
            'balance': balance,
            'created': created,
            'metadata': {'is_locked': bool(is_locked), 'available_balance': available_balance}
        }
        return self.db.save_wallet(wallet_data)

    def load_wallet(self, address):
        w = self.db.load_wallet(address)
        if w:
            # For compatibility, flatten metadata fields
            meta = w.get('metadata', {})
            w['is_locked'] = meta.get('is_locked', False)
            w['available_balance'] = meta.get('available_balance', 0.0)
        return w

    def list_wallets(self):
        # Return list of tuples for compatibility: (address, label, is_locked, balance, available_balance)
        wallets = self.db.list_wallets()
        result = []
        for wallet in wallets:
            address = wallet.get("address")
            label = wallet.get("label", "")
            balance = wallet.get("balance", 0.0)
            meta = wallet.get("metadata", {}) or {}
            is_locked = meta.get("is_locked", False)
            available_balance = meta.get("available_balance", 0.0)
            result.append((address, label, is_locked, balance, available_balance))
        return result


    def close(self):
        # No persistent connection to close in WalletDatabase
        pass

# Example usage:
if __name__ == "__main__":
    db = WalletDB()
    print("Wallets:", db.list_wallets())
    db.close()
