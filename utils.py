from config import POOL_ADDRESS, PRIVATE_KEY, TARGET_BIN_OFFSET
import math
from web3 import Web3

def getLiquidityConfig(isX):
    deltaIds = []
    distributionX = []
    distributionY = []
    length = TARGET_BIN_OFFSET * 2
    print(isX)
    if isX == True:
        unitX = 1
        unitY = 1 / (length - 0.5)
        for i in range(0, length):
            deltaIds.append(i - length + 1)
            if (i == length - 1):
                distributionX.append(Web3.to_wei(unitX, 'ether'))
                distributionY.append(Web3.to_wei(0.5 * unitY, 'ether') - 1000)
            else:
                distributionX.append(0)
                distributionY.append(Web3.to_wei(unitY, 'ether'))
    else:
        unitX = 1 / (length - 0.5)
        unitY = 1
        for i in range(0, length):
            deltaIds.append(i)
            if (i == 0):
                distributionX.append(Web3.to_wei(0.5 * unitX, 'ether') - 1000)
                distributionY.append(Web3.to_wei(unitY, 'ether'))
            else:
                distributionX.append(Web3.to_wei(unitX, 'ether'))
                distributionY.append(0)
    
    return deltaIds, distributionX, distributionY

def getIdSlippageFromPriceSlippage(priceSlippage, binStep):
    _priceSlippage = priceSlippage / 100
    return math.floor(
      math.log(1 + _priceSlippage) / math.log(1 + binStep / 10_000)
    )