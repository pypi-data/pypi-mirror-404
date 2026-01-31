# LunaLib

LunaLib is a modular cryptocurrency ecosystem library with wallet, blockchain, mining, storage, mempool, and P2P components.

## Installation

```bash
pip install -e .
```

## Quick Start

### Wallet

```python
from lunalib.core.wallet import LunaWallet

wallet = LunaWallet()
wallet_data = wallet.create_wallet("main", "password")
wallet.unlock_wallet(wallet_data["address"], "password")
```

### Blockchain Manager

```python
from lunalib.core.blockchain import BlockchainManager

chain = BlockchainManager(endpoint_url="https://bank.linglin.art")
latest = chain.get_latest_block()
```

### Mempool

```python
from lunalib.core.mempool import MempoolManager

mempool = MempoolManager()
```

### Daemon (Authoritative Validation)

```python
from lunalib.core.blockchain import BlockchainManager
from lunalib.core.mempool import MempoolManager
from lunalib.core.daemon import BlockchainDaemon

chain = BlockchainManager(endpoint_url="https://bank.linglin.art")
mempool = MempoolManager()
daemon = BlockchainDaemon(chain, mempool)
```

### P2P Client

```python
from lunalib.core.p2p import P2PClient

p2p = P2PClient(
    "https://bank.linglin.art",
    peer_seed_urls=["https://peer.example"],
    prefer_peers=False,
)
```

### Hybrid Client

```python
from lunalib.core.p2p import HybridBlockchainClient
from lunalib.core.blockchain import BlockchainManager
from lunalib.core.mempool import MempoolManager

chain = BlockchainManager(endpoint_url="https://bank.linglin.art")
mempool = MempoolManager()
hybrid = HybridBlockchainClient("https://bank.linglin.art", chain, mempool)
```

### Scan Full Chain with Fallback

```python
from lunalib.core.blockchain import BlockchainManager

chain = BlockchainManager(endpoint_url="https://bank.linglin.art")
full_chain = chain.scan_chain(peer_urls=["https://peer.example"])
```

## Web Builds (Pyodide)

- SQLite is disabled on web builds; IndexedDB is used automatically for cache and wallet storage.
- Threaded broadcast loops are disabled on Pyodide; mempool broadcasts run inline.

## Testing

```bash
pytest -q
```

### Test Coverage Highlights

- Daemon validation for blocks and transactions
- P2P primary/peer fallback behavior
- Full-chain scan fallback
- SM2 signing and verification
- Encryption integrity and tamper detection
- Mempool validation rules

## Module Initialization Guide

| Module | Purpose | Initialize |
| --- | --- | --- |
| Wallet | Key management and local wallet operations | `LunaWallet()` |
| Blockchain | Network chain queries and scans | `BlockchainManager(endpoint_url=...)` |
| Mempool | Pending transaction tracking and broadcast | `MempoolManager()` |
| Daemon | Authoritative validation and peer registry | `BlockchainDaemon(chain, mempool)` |
| P2P | Peer discovery and sync | `P2PClient(primary_url, ...)` |
| Hybrid | Primary + P2P combined mode | `HybridBlockchainClient(primary_url, chain, mempool)` |
| Storage | Local encrypted data and cache | `EncryptionManager()` / `BlockchainCache()` |

## Notes

- Prefer the primary node for validation, but allow P2P fallback for availability.
- For purely decentralized setups, use `prefer_peers=True` and provide seed peers.

## Environment Flags

Set these with standard environment variable mechanisms (e.g., PowerShell `$env:NAME="value"`).

### Networking / Serialization

- `LUNALIB_HTTP_GZIP` (default: `1`) — Enable gzip for HTTP payloads where supported.
- `LUNALIB_P2P_GZIP` (default: `1`) — Enable gzip for P2P traffic.
- `LUNALIB_USE_MSGPACK` (default: `0`) — Use msgpack when available.
- `LUNALIB_BLOCK_SUBMIT_TIMEOUT` (default: `30`) — Submit timeout (seconds).
- `LUNALIB_SUBMIT_CONFIRM_RETRIES` (default: `3`) — Post-submit confirmation retries.
- `LUNALIB_SUBMIT_CONFIRM_DELAY` (default: `1.0`) — Delay between confirmation retries (seconds).

### Wallet / Sync

- `LUNALIB_REWARD_CONFIRMATIONS` (default: `1`) — Reward confirmations required before counted.
- `LUNALIB_BALANCE_UPDATE_INTERVAL` (default: `15`) — Balance refresh cadence (seconds).
- `LUNALIB_WALLET_MONITOR_INTERVAL` (default: `5`) — Wallet monitor interval (seconds).
- `LUNALIB_SCAN_TX_LIMIT` (default: `5000`) — Max transactions kept per scan.
- `LUNALIB_CONFIRMED_CACHE` (default: `5000`) — Confirmed transaction cache size.
- `LUNALIB_PENDING_CACHE` (default: `2000`) — Pending transaction cache size.
- `LUNALIB_SEEN_TX_CACHE` (default: `20000`) — Seen transaction hash cache size.
- `LUNALIB_UI_DEBOUNCE` (default: `0.25`) — Debounce window for UI callbacks (seconds).

### Mining / Daemon

- `LUNALIB_TRUSTED_PEERS` (default: empty) — Comma-separated list of trusted peer IDs.
- `LUNALIB_SEEN_TX_MAX` (default: `50000`) — Daemon seen-tx cache size.
- `LUNALIB_MINER_STATUS_INTERVAL` (default: `5`) — Mining status update interval (seconds).
- `LUNALIB_MINER_CONCISE` (default: `1`) — Concise mining console status output.
- `LUNALIB_BLOCK_REWARD_MODE` (default: `linear`) — Reward mode for non-empty blocks (`linear` or `exponential`).
