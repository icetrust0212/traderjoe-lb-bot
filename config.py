import os
from web3 import Web3
from dotenv import load_dotenv
load_dotenv()

PRIVATE_KEY = os.getenv('PRIVATE_KEY')
POOL_ADDRESS = '0xD446eb1660F766d533BeCeEf890Df7A69d26f7d1' # AVAX-USDC pool
TARGET_BIN_OFFSET = 2

MAX_TOKEN_X_AMOUNT = Web3.to_wei(100, 'ether') # 100 AVAX
MAX_TOKEN_Y_AMOUNT = 100_000_000 # 100 USDC

MIN_BIN_COUNT = 10