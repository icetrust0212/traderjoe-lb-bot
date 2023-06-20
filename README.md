# traderjoe-lb-bot
## Dependencies
```bash
pip install -r requirements.txt
```
## Environment
You need to edit .env file.
### Env
```bash
AVALANCHE_RPC_URL=
BNB_RPC_URL= 
ARBITRUM_RPC_URL=
NETWORK=avalanche | binance | arbitrum
PRIVATE_KEY=
```
RPC URLs might be any public/private node.
If you want to run bot on BNB chain, you need to set NETWORK as binance.

### Config
Here, you can set necessary settings to run bot
```python
POOL_ADDRESS = '0x717D06B4D8bC6B71D5A2C45D8Cc417930aEC073d' # BTCB-BNB
TARGET_BIN_OFFSET = 2

MAX_TOKEN_X_AMOUNT = Web3.to_wei(100, 'ether') # 100 BTCB
MAX_TOKEN_Y_AMOUNT = Web3.to_wei(100, 'ether') # 100 WBNB

MIN_BIN_COUNT = 10
SLIPPAGE = 0.5
```

## Run

```bash
python index.py
```