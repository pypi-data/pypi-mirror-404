import os
import json
import sys

# --- Unicode-safe print for Windows console ---
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, 'encoding', 'utf-8')
        print(*(str(a).encode(encoding, errors='replace').decode(encoding) for a in args), **kwargs)
import base64
import hmac
from typing import Dict, Optional
from lunalib.utils.hash import derive_key_sm3, hmac_sm3
class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""
    
    def __init__(self):
        self.salt = b'luna_wallet_salt'  # In production, use random salt per wallet
    
    def encrypt_wallet(self, wallet_data: Dict, password: str) -> Dict:
        """Encrypt wallet data"""
        try:
            # Encrypt private key separately
            private_key = wallet_data.get('private_key', '')
            if private_key:
                encrypted_private = self._encrypt_bytes(private_key.encode(), password)
                wallet_data['encrypted_private_key'] = encrypted_private
                del wallet_data['private_key']
            
            # Encrypt entire wallet data
            wallet_json = json.dumps(wallet_data)
            encrypted_wallet = self._encrypt_bytes(wallet_json.encode(), password)
            
            return {
                'encrypted_data': encrypted_wallet,
                'version': '1.0',
                'salt': base64.b64encode(self.salt).decode()
            }
            
        except Exception as e:
            safe_print(f"Encryption error: {e}")
            return {}
    
    def decrypt_wallet(self, encrypted_data: Dict, password: str) -> Optional[Dict]:
        """Decrypt wallet data"""
        try:
            encrypted_wallet = encrypted_data.get('encrypted_data', '')
            if not encrypted_wallet:
                return None

            # Decrypt wallet
            decrypted_data = self._decrypt_bytes(encrypted_wallet, password)
            wallet_data = json.loads(decrypted_data.decode())
            
            # Decrypt private key if present
            encrypted_private = wallet_data.get('encrypted_private_key')
            if encrypted_private:
                private_key = self._decrypt_bytes(encrypted_private, password).decode()
                wallet_data['private_key'] = private_key
                del wallet_data['encrypted_private_key']
            
            return wallet_data
            
        except Exception as e:
            safe_print(f"Decryption error: {e}")
            return None
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password using SM3"""
        return derive_key_sm3(password, self.salt, iterations=100000, dklen=32)

    def _keystream(self, key: bytes, nonce: bytes, length: int) -> bytes:
        output = bytearray()
        counter = 0
        while len(output) < length:
            counter_bytes = counter.to_bytes(4, "big")
            output.extend(hmac_sm3(key, nonce + counter_bytes))
            counter += 1
        return bytes(output[:length])

    def _encrypt_bytes(self, plaintext: bytes, password: str) -> str:
        key = self._derive_key(password)
        nonce = os.urandom(16)
        stream = self._keystream(key, nonce, len(plaintext))
        ciphertext = bytes(a ^ b for a, b in zip(plaintext, stream))
        mac = hmac_sm3(key, nonce + ciphertext)
        token = b"EL3" + nonce + ciphertext + mac
        return base64.urlsafe_b64encode(token).decode()

    def _decrypt_bytes(self, token: str, password: str) -> bytes:
        key = self._derive_key(password)
        raw = base64.urlsafe_b64decode(token.encode())
        if not raw.startswith(b"EL3"):
            raise ValueError("Unsupported encryption format")
        nonce = raw[3:19]
        mac = raw[-32:]
        ciphertext = raw[19:-32]
        expected_mac = hmac_sm3(key, nonce + ciphertext)
        if not hmac.compare_digest(mac, expected_mac):
            raise ValueError("Invalid password or corrupted data")
        stream = self._keystream(key, nonce, len(ciphertext))
        return bytes(a ^ b for a, b in zip(ciphertext, stream))
    
    def verify_password(self, encrypted_data: Dict, password: str) -> bool:
        """Verify password without full decryption"""
        try:
            token = encrypted_data.get('encrypted_data', '')
            if not token:
                return False
            raw = base64.urlsafe_b64decode(token.encode())
            if not raw.startswith(b"EL3"):
                return False
            nonce = raw[3:19]
            mac = raw[-32:]
            ciphertext = raw[19:-32]
            key = self._derive_key(password)
            expected_mac = hmac_sm3(key, nonce + ciphertext)
            return hmac.compare_digest(mac, expected_mac)
        except:
            return False
    
    def encrypt_data(self, data: str, password: str) -> str:
        """Encrypt arbitrary data"""
        return self._encrypt_bytes(data.encode(), password)
    
    def decrypt_data(self, encrypted_data: str, password: str) -> str:
        """Decrypt arbitrary data"""
        return self._decrypt_bytes(encrypted_data, password).decode()