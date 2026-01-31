# DerivaDEX Auditor

## What it is
The Auditor is a standalone Python client that:
- Connects to the DerivaDEX Trader API  
- Maintains a Sparse Merkle Tree of on-chain state  
- Processes transaction‐log entries in order  
- Validates state‐root hashes and proofs  
- Exposes a local API/queue for downstream apps

## Configuration
Set via environment variables or CLI flags:
```text
WEB_SERVER_URL        # base HTTP(S) URL of operator node
CONTRACT_DEPLOYMENT   # deployment name, e.g. “geth”
BOOTSTRAP_STATE        # path or JSON blob of genesis parameters
EPOCH_PARAMS          # path or JSON of epoch timing & periods
TRADE_MINING_PARAMS   # path or JSON of trade‐mining settings
COLLATERAL_TRANCHES   # JSON array of [threshold,ratio] pairs
```

## Usage
```bash
python auditor_driver.py \
  --webserver-url $WEB_SERVER_URL \
  --contract-deployment $CONTRACT_DEPLOYMENT \
  --genesis-params $BOOTSTRAP_STATE \
  --epoch-params $EPOCH_PARAMS \
  --trade-mining-params $TRADE_MINING_PARAMS \
  --collateral-tranches $COLLATERAL_TRANCHES
```
Run `python auditor_driver.py --help` for all available flags.
