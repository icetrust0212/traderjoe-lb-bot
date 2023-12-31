from config import POOL_ADDRESS, PRIVATE_KEY, TARGET_BIN_OFFSET
from constants import NETWORK, BNB_GAS_PRICE, ARBITRUM_GAS_PRICE
import math
from web3 import Web3

def getLiquidityConfig(isX, isOut):
    deltaIds = []
    distributionX = []
    distributionY = []
    length = TARGET_BIN_OFFSET
    if isX == True:
        for i in range(0, length):
            if isOut:
                deltaIds.append(i - length)
            else:
                deltaIds.append(i - 2 * length + 1)
            distributionX.append(0)
            distributionY.append(Web3.to_wei(1 / length, 'ether'))
    else:
        for i in range(0, length):
            if isOut:
                deltaIds.append(i + 1)
            else:
                deltaIds.append(i + length)
            distributionY.append(0)
            distributionX.append(Web3.to_wei(1 / length, 'ether'))
    
    return deltaIds, distributionX, distributionY

def getIdSlippageFromPriceSlippage(priceSlippage, binStep):
    _priceSlippage = priceSlippage / 100
    return math.floor(
      math.log(1 + _priceSlippage) / math.log(1 + binStep / 10_000)
    )

def get_build_parameters(chain_id, address, nonce):
    build_parameters = {"chainId": chain_id, "from": address, "nonce": nonce}
    if NETWORK == 'avalanche':
        build_parameters = {"chainId": chain_id, "from": address, "nonce": nonce}
    elif NETWORK == 'binance':
        build_parameters = {"chainId": chain_id, "from": address, "nonce": nonce, "gasPrice": BNB_GAS_PRICE}
    else:
        build_parameters = {"chainId": chain_id, "from": address, "nonce": nonce, "gasPrice": ARBITRUM_GAS_PRICE}
    return build_parameters


