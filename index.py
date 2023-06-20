from web3 import Web3
from constants import RPC_URL, ROUTER_ADDRESS, NETWORK, QUOTER_ADDRESS
from config import POOL_ADDRESS, PRIVATE_KEY, TARGET_BIN_OFFSET, MAX_TOKEN_X_AMOUNT, MAX_TOKEN_Y_AMOUNT, MIN_BIN_COUNT, SLIPPAGE
from abi.LBRouter import ROUTER_ABI
from abi.LBPair import PAIR_ABI
from abi.ERC20 import ERC20_ABI
from abi.LBQuoter import QUOTER_ABI
from eth_account import Account
import requests
import schedule
import time
from web3.middleware import geth_poa_middleware
from utils import getLiquidityConfig, getIdSlippageFromPriceSlippage, get_build_parameters
import math

# Create web3 instance
web3 = Web3(Web3.HTTPProvider(RPC_URL))

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

# Create LBQuoter
quoter = web3.eth.contract(address=QUOTER_ADDRESS, abi=QUOTER_ABI)

print(tokenXAddress)
print(tokenYAddress)

tokenX = web3.eth.contract(address=tokenXAddress, abi=ERC20_ABI)
tokenY = web3.eth.contract(address=tokenYAddress, abi=ERC20_ABI)

bin_step = pool.functions.getBinStep().call()
chain_id = web3.eth.chain_id

print(chain_id, bin_step)

def approve():
    print('Approve ...')

    allowanceX = tokenX.functions.allowance(account.address, ROUTER_ADDRESS).call()
    allowanceY = tokenY.functions.allowance(account.address, ROUTER_ADDRESS).call()
    if allowanceX == 0:
        nonce = web3.eth.get_transaction_count(account.address)
        build_parameters = get_build_parameters(chain_id, account.address, nonce)
        call_function = tokenX.functions.approve(ROUTER_ADDRESS, 2**256 - 1).build_transaction(build_parameters)
        
        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # Wait for transaction receipt
        web3.eth.wait_for_transaction_receipt(send_tx)

    if allowanceY == 0:
        nonce = web3.eth.get_transaction_count(account.address)
        build_parameters = get_build_parameters(chain_id, account.address, nonce)
        call_function = tokenY.functions.approve(ROUTER_ADDRESS, 2**256 - 1).build_transaction(build_parameters)
        
        signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
        send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # Wait for transaction receipt
        web3.eth.wait_for_transaction_receipt(send_tx)

    isNFTApproved = pool.functions.isApprovedForAll(account.address, ROUTER_ADDRESS).call()
    if isNFTApproved == False:
        nonce = web3.eth.get_transaction_count(account.address)
        build_parameters = get_build_parameters(chain_id, account.address, nonce)
        call_function = pool.functions.approveForAll(ROUTER_ADDRESS, True).build_transaction(build_parameters)
        
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
    url = f"https://barn.traderjoexyz.com/v1/user/bin-position?userAddress={account.address.lower()}&chain={NETWORK}&poolAddress={POOL_ADDRESS.lower()}&pageSize=1000"
    response = requests.get(url)
    binData_raw = response.json()
    binData = []
    bin_ids = []
    for id_data in binData_raw:
        bin_ids.append(id_data['binId'])
        binData.append(id_data)
    
    target_bin_id_X = bin_ids[TARGET_BIN_OFFSET - 1]
    target_bin_id_Y = bin_ids[len(bin_ids) - TARGET_BIN_OFFSET]

    if (len(bin_ids) < MIN_BIN_COUNT):
        print("Bin length is insufficient")
        return

    if active_bin <= target_bin_id_X or active_bin >= target_bin_id_Y:
        swapRoute = []
        swapToken = tokenX
        deleted_data = binData[-1 * TARGET_BIN_OFFSET:]
        maxValue = MAX_TOKEN_X_AMOUNT
        if active_bin <= target_bin_id_X:
            deleted_data = binData[-1 * TARGET_BIN_OFFSET:]
            swapToken = tokenX
            maxValue = MAX_TOKEN_X_AMOUNT
            swapRoute = [tokenXAddress, tokenYAddress]
        else:
            deleted_data = binData[0: TARGET_BIN_OFFSET]
            swapToken = tokenY
            maxValue = MAX_TOKEN_Y_AMOUNT
            swapRoute = [tokenYAddress, tokenXAddress]
        removeLiquidity(deleted_data)
        time.sleep(10)
        swap(swapToken, swapRoute, maxValue)
        time.sleep(10)
        addLiquidity(active_bin, active_bin <= target_bin_id_X, (active_bin <= bin_ids[0]) or (active_bin >= bin_ids[len(bin_ids) - 1]))
        time.sleep(10)

def removeLiquidity(bin_data):
    print("Remove liquidity")
    amounts = []
    ids = []
    for bin in bin_data:
        id = int(bin['binId'])
        amounts.append(pool.functions.balanceOf(account.address, id).call())
        ids.append(id)
    deadline = web3.eth.get_block('latest').timestamp + 60
    nonce = web3.eth.get_transaction_count(account.address)
    build_parameters = get_build_parameters(chain_id, account.address, nonce)
    call_function = router.functions.removeLiquidity(tokenXAddress, tokenYAddress, bin_step, 0, 0, ids, amounts, account.address, deadline).build_transaction(build_parameters)
    signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
    send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
    print(tx_receipt) # Optional

def swap(swapToken, route, maxValue):
    print("Swap")
    amountIn = min(math.floor(swapToken.functions.balanceOf(account.address).call()), maxValue)
    if amountIn <= 100:
        print("Insufficient Amount")
        return
    
    quote = quoter.functions.findBestPathFromAmountIn(route, amountIn).call()
    versions = quote[3]
    path = {
        "pairBinSteps": [bin_step],
        "versions": versions,
        "tokenPath": route
    }
    nonce = web3.eth.get_transaction_count(account.address)
    deadline = web3.eth.get_block('latest').timestamp + 60

    # Swap half of token
    build_parameters = get_build_parameters(chain_id, account.address, nonce)
    call_function = router.functions.swapExactTokensForTokens(amountIn, 0, path, account.address, deadline).build_transaction(build_parameters)
    
    signed_tx = web3.eth.account.sign_transaction(call_function, private_key=PRIVATE_KEY)
    send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
    print(tx_receipt) # Optional

def addLiquidity(active_bin, isX, isOut):
    print("Add liquidity")
    deltaIds, distributionX, distributionY = getLiquidityConfig(isX, isOut)
    print(deltaIds, distributionX, distributionY)
    idSlippage = getIdSlippageFromPriceSlippage(SLIPPAGE, bin_step)
    nonce = web3.eth.get_transaction_count(account.address)
    deadline = web3.eth.get_block('latest').timestamp + 60
    amountX = min(tokenX.functions.balanceOf(account.address).call(), MAX_TOKEN_X_AMOUNT)
    amountY = min(tokenY.functions.balanceOf(account.address).call(), MAX_TOKEN_Y_AMOUNT)
    amountXMin = 100
    amountYMin = 100
    if isX == True:
        amountX = 0
        amountXMin = 0
    else:
        amountY = 0
        amountYMin = 0


    liquidityParameters = {
        'tokenX': tokenXAddress,
        'tokenY': tokenYAddress,
        'binStep': bin_step,
        'amountX': amountX,
        'amountY': amountY,
        'amountXMin': amountXMin,
        'amountYMin': amountYMin,
        'activeIdDesired': active_bin,
        'idSlippage': idSlippage,
        'deltaIds': deltaIds,
        'distributionX': distributionX,
        'distributionY': distributionY,
        'to': account.address,
        'refundTo': account.address,
        'deadline': deadline
    }

    build_parameters = get_build_parameters(chain_id, account.address, nonce)
    call_function = router.functions.addLiquidity(liquidityParameters).build_transaction(build_parameters)
    
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