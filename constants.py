import os
from dotenv import load_dotenv
load_dotenv()

API_URL='https://barn.traderjoexyz.com'

AVALANCHE_RPC_URL = os.getenv('AVALANCHE_RPC_URL')
BNB_RPC_URL = os.getenv('BNB_RPC_URL')
ARBITRUM_RPC_URL = os.getenv('ARBITRUM_RPC_URL')
NETWORK = os.getenv('NETWORK')

RPC_URL = AVALANCHE_RPC_URL
ROUTER_ADDRESS = '0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30'
QUOTER_ADDRESS = '0x64b57F4249aA99a812212cee7DAEFEDC40B203cD'

if NETWORK == 'avalanche': # Avalanche C Chain
    RPC_URL = AVALANCHE_RPC_URL
elif NETWORK == 'binance': # BNB chain
    RPC_URL = BNB_RPC_URL
else:
    RPC_URL = ARBITRUM_RPC_URL

BNB_GAS_PRICE = 3000000000
ARBITRUM_GAS_PRICE = 100000000

print(NETWORK)
print(RPC_URL)