import os
from web3 import Web3
from dotenv import load_dotenv
load_dotenv()

PRIVATE_KEY = os.getenv('PRIVATE_KEY')
# POOL_ADDRESS = '0xD446eb1660F766d533BeCeEf890Df7A69d26f7d1' # AVAX-USDC pool
POOL_ADDRESS = '0xf258929a659F68ace4732e36F626d6D1544878aC' # BTCB-BNB
TARGET_BIN_OFFSET = 2

MAX_TOKEN_X_AMOUNT = Web3.to_wei(100, 'ether') # 100 BTCB
MAX_TOKEN_Y_AMOUNT = Web3.to_wei(100, 'ether') # 100 WBNB

MIN_BIN_COUNT = 10
SLIPPAGE = 0.5