import os
import sys
if sys.platform != "emscripten":
    import sqlite3
else:
    sqlite3 = None
import json
import time
from typing import Dict, List, Optional, Any
from lunalib.utils.validation import is_valid_address, is_safe_text
from .indexeddb import IndexedDBStore

# --- Unicode-safe print for Windows console ---
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, 'encoding', 'utf-8')
        print(*(str(a).encode(encoding, errors='replace').decode(encoding) for a in args), **kwargs)


def _safe_home_dir() -> str:
    home = os.path.expanduser("~")
    if home and home != "~":
        return home
    env_home = os.getenv("HOME") or os.getenv("USERPROFILE")
    if env_home:
        return env_home
    return os.getcwd()


def get_default_wallet_dir() -> str:
    """Resolve a writable default wallet directory across platforms."""
    if sys.platform == "emscripten":
        return "."

    override = os.getenv("LUNALIB_DATA_DIR") or os.getenv("LUNALIB_WALLET_DIR")
    if override:
        return override

    home = _safe_home_dir()

    if os.name == "nt":
        base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or home
        return os.path.join(base, "LunaLib")

    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "LunaLib")

    # Mobile (best-effort) + Linux/Unix
    android_base = os.getenv("ANDROID_APP_STORAGE") or os.getenv("ANDROID_DATA")
    if android_base:
        return os.path.join(android_base, "LunaLib")

    xdg_base = os.getenv("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return os.path.join(xdg_base, "LunaLib")


def resolve_wallet_db_path(db_path: Optional[str] = None) -> str:
    """Resolve database path with backward-compatible fallbacks."""
    if db_path:
        return db_path

    default_dir = get_default_wallet_dir()
    default_path = os.path.join(default_dir, "wallets.db")

    legacy_candidates = [
        os.path.join(os.path.expanduser("~"), ".luna_wallet", "wallet.db"),
        os.path.join(os.path.expanduser("~"), ".luna_wallet", "wallets.db"),
        os.path.expanduser("~/.lunawallet/wallets.db"),
    ]

    for candidate in legacy_candidates:
        if os.path.exists(candidate):
            return candidate

    return default_path

class WalletDatabase:
    """Manages wallet data storage"""
    
    def __init__(self, db_path=None):
        self.db_path = resolve_wallet_db_path(db_path)
        self._use_indexeddb = sys.platform == "emscripten"
        self._idb = None
        if not self._use_indexeddb:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize wallet database"""
        if self._use_indexeddb:
            self._idb = IndexedDBStore(
                db_name="lunalib",
                stores=["wallets", "transactions", "pending_transactions"],
            )
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Wallets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                address TEXT PRIMARY KEY,
                label TEXT,
                public_key TEXT,
                encrypted_private_key TEXT,
                balance REAL DEFAULT 0.0,
                created REAL,
                last_accessed REAL,
                metadata TEXT
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tx_hash TEXT PRIMARY KEY,
                wallet_address TEXT,
                tx_type TEXT,
                from_address TEXT,
                to_address TEXT,
                amount REAL,
                fee REAL,
                timestamp REAL,
                block_height INTEGER,
                status TEXT,
                memo TEXT,
                raw_data TEXT,
                FOREIGN KEY (wallet_address) REFERENCES wallets (address)
            )
        ''')
        
        # Pending transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_transactions (
                tx_hash TEXT PRIMARY KEY,
                wallet_address TEXT,
                from_address TEXT,
                to_address TEXT,
                amount REAL,
                fee REAL,
                created_time REAL,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                last_retry REAL,
                raw_data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_wallet(self, wallet_data: Dict) -> bool:
        """Save wallet to database"""
        try:
            address = wallet_data.get("address")
            if not is_valid_address(address):
                safe_print("Save wallet error: invalid address")
                return False
            label = wallet_data.get('label', '')
            if label and not is_safe_text(label, max_len=128):
                safe_print("Save wallet error: invalid label")
                return False
            if self._use_indexeddb and self._idb:
                return self._idb.put("wallets", wallet_data["address"], wallet_data)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO wallets 
                (address, label, public_key, encrypted_private_key, balance, created, last_accessed, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                address,
                label,
                wallet_data.get('public_key', ''),
                wallet_data.get('encrypted_private_key', ''),
                wallet_data.get('balance', 0.0),
                wallet_data.get('created', time.time()),
                time.time(),
                json.dumps(wallet_data.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            safe_print(f"Save wallet error: {e}")
            return False
    
    def load_wallet(self, address: str) -> Optional[Dict]:
        """Load wallet from database"""
        try:
            if self._use_indexeddb and self._idb:
                return self._idb.get("wallets", address)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM wallets WHERE address = ?', (address,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'address': result[0],
                    'label': result[1],
                    'public_key': result[2],
                    'encrypted_private_key': result[3],
                    'balance': result[4],
                    'created': result[5],
                    'last_accessed': result[6],
                    'metadata': json.loads(result[7]) if result[7] else {}
                }
                
        except Exception as e:
            safe_print(f"Load wallet error: {e}")
            
        return None
    
    def save_transaction(self, transaction: Dict, wallet_address: str) -> bool:
        """Save transaction to database"""
        try:
            if not is_valid_address(wallet_address):
                safe_print("Save transaction error: invalid wallet address")
                return False
            from_addr = transaction.get('from', '')
            to_addr = transaction.get('to', '')
            if from_addr and not is_valid_address(from_addr):
                safe_print("Save transaction error: invalid from address")
                return False
            if to_addr and not is_valid_address(to_addr):
                safe_print("Save transaction error: invalid to address")
                return False
            if self._use_indexeddb and self._idb:
                tx_hash = transaction.get("hash", "")
                payload = {
                    "tx_hash": tx_hash,
                    "wallet_address": wallet_address,
                    "timestamp": transaction.get("timestamp", time.time()),
                    "raw_data": transaction,
                }
                return self._idb.put("transactions", tx_hash, payload)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO transactions 
                (tx_hash, wallet_address, tx_type, from_address, to_address, amount, fee, 
                 timestamp, block_height, status, memo, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction.get('hash', ''),
                wallet_address,
                transaction.get('type', 'transfer'),
                transaction.get('from', ''),
                transaction.get('to', ''),
                transaction.get('amount', 0),
                transaction.get('fee', 0),
                transaction.get('timestamp', time.time()),
                transaction.get('block_height'),
                transaction.get('status', 'confirmed'),
                transaction.get('memo', ''),
                json.dumps(transaction)
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            safe_print(f"Save transaction error: {e}")
            return False
    
    def get_wallet_transactions(self, wallet_address: str, limit: int = 100) -> List[Dict]:
        """Get transactions for a wallet"""
        try:
            if self._use_indexeddb and self._idb:
                items = self._idb.get_all_items("transactions")
                txs = []
                for item in items:
                    payload = item.get("value")
                    if payload and payload.get("wallet_address") == wallet_address:
                        txs.append(payload.get("raw_data", {}))
                txs.sort(key=lambda t: t.get("timestamp", 0), reverse=True)
                return txs[:limit]
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT raw_data FROM transactions 
                WHERE wallet_address = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (wallet_address, limit))
            
            results = cursor.fetchall()
            conn.close()
            
            transactions = []
            for result in results:
                try:
                    tx = json.loads(result[0])
                    transactions.append(tx)
                except:
                    continue
                    
            return transactions
            
        except Exception as e:
            safe_print(f"Get transactions error: {e}")
            return []
    
    def save_pending_transaction(self, transaction: Dict, wallet_address: str) -> bool:
        """Save pending transaction"""
        try:
            if self._use_indexeddb and self._idb:
                tx_hash = transaction.get("hash", "")
                payload = {
                    "tx_hash": tx_hash,
                    "wallet_address": wallet_address,
                    "created_time": time.time(),
                    "status": "pending",
                    "raw_data": transaction,
                }
                return self._idb.put("pending_transactions", tx_hash, payload)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO pending_transactions 
                (tx_hash, wallet_address, from_address, to_address, amount, fee, 
                 created_time, status, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction.get('hash', ''),
                wallet_address,
                transaction.get('from', ''),
                transaction.get('to', ''),
                transaction.get('amount', 0),
                transaction.get('fee', 0),
                time.time(),
                'pending',
                json.dumps(transaction)
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            safe_print(f"Save pending transaction error: {e}")
            return False

    def list_wallets(self) -> List[Dict[str, Any]]:
        """List all wallets"""
        try:
            if self._use_indexeddb and self._idb:
                items = self._idb.get_all_items("wallets")
                return [item.get("value") for item in items if item.get("value")]
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM wallets')
            results = cursor.fetchall()
            conn.close()
            wallets = []
            for result in results:
                wallets.append({
                    'address': result[0],
                    'label': result[1],
                    'public_key': result[2],
                    'encrypted_private_key': result[3],
                    'balance': result[4],
                    'created': result[5],
                    'last_accessed': result[6],
                    'metadata': json.loads(result[7]) if result[7] else {},
                })
            return wallets
        except Exception as e:
            safe_print(f"List wallets error: {e}")
            return []