## Usage

1. Add your Ethereum addresses to `evm.txt` (one per line).
2. Add your proxy list to `proxies.txt` (one per line, format: `http://ip:port` or `socks5://ip:port`).
3. Run the script:
   ```
   python main.py
   ```
4. The script will process the addresses and save eligible claims to `eligible_claims.json`.
5. The output will be in the following format:
```
[
  {
    "address": "0x...",
    "amount": 100,
    "round1": 50,
    "round2": 50
  }
]
```