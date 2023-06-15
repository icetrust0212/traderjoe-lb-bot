from web3 import Web3
from constants import INFURA_URL, ROUTER_ADDRESS
from config import POOL_ADDRESS, PRIVATE_KEY, TARGET_BIN_OFFSET, MIN_TOKEN_X_AMOUNT, MIN_TOKEN_Y_AMOUNT
from abi.LBRouter import ROUTER_ABI
from abi.LBPair import PAIR_ABI
from abi.ERC20 import ERC20_ABI
from eth_account import Account
import requests
import schedule
import time
from web3.middleware import geth_poa_middleware
from utils import getLiquidityConfig, getIdSlippageFromPriceSlippage
import math

# Create web3 instance
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

web3.middleware_onion.inject(geth_poa_middleware, layer=0)
# Get wallet
account = Account.from_key(PRIVATE_KEY)

# Get a balance of wallet
balance = web3.eth.get_balance(account.address)

# Create LBRouter contract instance
router = web3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)

# Create LBPool
pool = web3.eth.contract(address=POOL_ADDRESS, abi=PAIR_ABI)
tokenXAddress = pool.functions.getTokenX().call()
tokenYAddress = pool.functions.getTokenY().call()

tokenX = web3.eth.contract(address=tokenXAddress, abi=ERC20_ABI)
tokenY = web3.eth.contract(address=tokenYAddress, abi=ERC20_ABI)

bin_step = pool.functions.getBinStep().call()
chain_id = web3.eth.chain_id

def approve():
    print('Approve ...')

    allowanceX = tokenX.functions.allowance(account.address, ROUTER_ADDRESS).call()
    allowanceY = tokenY.functions.allowance(account.address, ROUTER_ADDRESS).call()

    if allowanceX == 0:
        nonce = web3.eth.get_transaction_count(account.address)
        call_function = tokenX.functions.approve(ROUTER_ADDRESS, 2**256 - 1).build_transaction({"chainId": chain_id, "from": account.address, "nonce": nonce})
        
        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # Wait for transaction receipt
        web3.eth.wait_for_transaction_receipt(send_tx)

    if allowanceY == 0:
        nonce = web3.eth.get_transaction_count(account.address)
        call_function = tokenY.functions.approve(ROUTER_ADDRESS, 2**256 - 1).build_transaction({"chainId": chain_id, "from": account.address, "nonce": nonce})
        
        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # Wait for transaction receipt
        web3.eth.wait_for_transaction_receipt(send_tx)
    print('Approve Done')

def job():
    print("Running job...")
    active_bin = pool.functions.getActiveId().call()
    print(active_bin)

    # Get all bin ids
    url = f"https://barn.traderjoexyz.com/v1/user/bin-position?userAddress={account.address.lower()}&chain=avalanche&poolAddress={POOL_ADDRESS.lower()}&pageSize=1000"
    response = requests.get(url)
    binData_raw = response.json()
    binData = []
    bin_ids = []
    for id_data in binData_raw:
        if id_data['tokenX']['amount'] >= MIN_TOKEN_X_AMOUNT or id_data['tokenY']['amount'] >= MIN_TOKEN_Y_AMOUNT:
            bin_ids.append(id_data['binId'])
            binData.append(id_data)
    
    target_bin_id_X = bin_ids[TARGET_BIN_OFFSET - 1]
    target_bin_id_Y = bin_ids[len(bin_ids) - TARGET_BIN_OFFSET]

    print(bin_ids)
    
    print(target_bin_id_X)
    print(target_bin_id_Y)

    if active_bin <= target_bin_id_X or active_bin >= target_bin_id_Y:
        swapRoute = []
        swapToken = tokenX
        deleted_data = binData[-1 * TARGET_BIN_OFFSET:]

        if active_bin == target_bin_id_X:
            deleted_data = binData[-1 * TARGET_BIN_OFFSET:]
            swapToken = tokenX
            swapRoute = [tokenXAddress, tokenYAddress]
        else:
            deleted_data = binData[0: TARGET_BIN_OFFSET]
            swapToken = tokenY
            swapRoute = [tokenYAddress, tokenXAddress]
        removeLiquidity(deleted_data)
        time.sleep(10)
        swap(swapToken, swapRoute)
        time.sleep(10)
        addLiquidity(active_bin, active_bin <= target_bin_id_X)
        time.sleep(10)

def removeLiquidity(bin_data):
    print("Remove liquidity")
    amounts = []
    ids = []
    for bin in bin_data:
        amounts.append(int(bin['liquidity']))
        ids.append(int(bin['binId']))
    deadline = web3.eth.get_block('latest').timestamp + 60
    nonce = web3.eth.get_transaction_count(account.address)
    call_function = router.functions.removeLiquidity(tokenXAddress, tokenYAddress, bin_step, 0, 0, ids, amounts, account.address, deadline).build_transaction({"chainId": chain_id, "from": account.address, "nonce": nonce})
    signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
    send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
    print(tx_receipt) # Optional

def swap(swapToken, route):
    print("Swap")
    path = {
        "pairBinSteps": [bin_step],
        "versions": [1],
        "tokenPath": route
    }
    nonce = web3.eth.get_transaction_count(account.address)
    deadline = web3.eth.get_block('latest').timestamp + 60
    amountIn = math.floor(swapToken.functions.balanceOf(account.address).call() / 2)
    # Swap half of token
    call_function = router.functions.swapExactTokensForTokens(amountIn, 0, path, account.address, deadline).build_transaction({"chainId": chain_id, "from": account.address, "nonce": nonce})
    
    signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
    send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
    print(tx_receipt) # Optional

def addLiquidity(active_bin, isX):
    print("Add liquidity")
    deltaIds, distributionX, distributionY = getLiquidityConfig(isX)
    idSlippage = getIdSlippageFromPriceSlippage(0.5, bin_step)
    nonce = web3.eth.get_transaction_count(account.address)
    deadline = web3.eth.get_block('latest').timestamp + 60
    amountX = tokenX.functions.balanceOf(account.address).call()
    amountY = tokenY.functions.balanceOf(account.address).call()
    amountMin = 100

    print(deltaIds)
    print(idSlippage)
    print(distributionX)
    print(distributionY)
    print(amountX)
    print(amountY)
    liquidityParameters = {
        'tokenX': tokenXAddress,
        'tokenY': tokenYAddress,
        'binStep': bin_step,
        'amountX': amountX,
        'amountY': amountY,
        'amountXMin': amountMin,
        'amountYMin': amountMin,
        'activeIdDesired': active_bin,
        'idSlippage': idSlippage,
        'deltaIds': deltaIds,
        'distributionX': distributionX,
        'distributionY': distributionY,
        'to': account.address,
        'refundTo': account.address,
        'deadline': deadline
    }
    call_function = router.functions.addLiquidity(liquidityParameters).build_transaction({"chainId": chain_id, "from": account.address, "nonce": nonce})
    
    signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
    send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
    print(tx_receipt) # Optional

approve()
job()
# Schedule the job to run every minute
schedule.every(2).minutes.do(job)

# Run the scheduled jobs continuously
while True:
    schedule.run_pending()
    time.sleep(1)