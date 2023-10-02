
import os
import time
import telebot
from telebot import types
from web3 import Web3, middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy
import requests
import csv
from collections import deque
from dotenv import load_dotenv


# --------------- Load .env variables -----------------------

load_dotenv()

# import your keys
rpc_url = os.environ.get('RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))
my_address = Web3.to_checksum_address(os.environ.get('YOUR_PUBLIC_KEY'))
my_private_key = os.environ.get('YOUR_PRIVATE_KEY')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
etherscan_api_key = os.environ.get('ETHERSCAN_API_KEY')
tg_chat_id = os.environ.get('TG_CHAT_ID')

# import tg bot settings
with open('current_settings.csv', 'r') as file:
    reader = csv.reader(file)

    # Since you're expecting just one row, you can use next() to retrieve it
    row = next(reader)
    if len(row) >= 2:  # Ensure there are at least two values in the row
        token_address = str(row[0].strip())  # Assign the first value
        token_address = token_address.replace("'", "")
        decimals = int(row[1].strip())  # Convert the second value to float and assign
        buy_tax = float(row[2].strip())
        max_slippage = float(row[3].strip())
        drop_pct = float(row[4].strip())  # Convert the second value to float and assign
        bot_setup = row[5].strip()


# ------------------ Web3 interaction setup -------------------

w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
w3.middleware_onion.add(middleware.simple_cache_middleware)
w3.middleware_onion.add(middleware.time_based_cache_middleware)
w3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)
w3.eth.set_gas_price_strategy(medium_gas_price_strategy)

# Define the Uniswap v2 router contract
router_address = Web3.to_checksum_address('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')  # Uniswap v2 router
router_abi = [{"inputs":[{"internalType":"address","name":"_factory","type":"address"},{"internalType":"address","name":"_WETH","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"WETH","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"amountADesired","type":"uint256"},{"internalType":"uint256","name":"amountBDesired","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"amountTokenDesired","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"addLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"},{"internalType":"uint256","name":"liquidity","type":"uint256"}],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountIn","outputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"reserveIn","type":"uint256"},{"internalType":"uint256","name":"reserveOut","type":"uint256"}],"name":"getAmountOut","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsIn","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"reserveA","type":"uint256"},{"internalType":"uint256","name":"reserveB","type":"uint256"}],"name":"quote","outputs":[{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidity","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETH","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"removeLiquidityETHSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermit","outputs":[{"internalType":"uint256","name":"amountToken","type":"uint256"},{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"token","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountTokenMin","type":"uint256"},{"internalType":"uint256","name":"amountETHMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityETHWithPermitSupportingFeeOnTransferTokens","outputs":[{"internalType":"uint256","name":"amountETH","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint256","name":"liquidity","type":"uint256"},{"internalType":"uint256","name":"amountAMin","type":"uint256"},{"internalType":"uint256","name":"amountBMin","type":"uint256"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"},{"internalType":"bool","name":"approveMax","type":"bool"},{"internalType":"uint8","name":"v","type":"uint8"},{"internalType":"bytes32","name":"r","type":"bytes32"},{"internalType":"bytes32","name":"s","type":"bytes32"}],"name":"removeLiquidityWithPermit","outputs":[{"internalType":"uint256","name":"amountA","type":"uint256"},{"internalType":"uint256","name":"amountB","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapETHForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactETHForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForETHSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint256","name":"amountOutMin","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapExactTokensForTokensSupportingFeeOnTransferTokens","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactETH","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint256","name":"amountInMax","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"deadline","type":"uint256"}],"name":"swapTokensForExactTokens","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]  # ABI for Uniswap V2 router
uniswap2_router = w3.eth.contract(address=router_address, abi=router_abi)

# Define the eth and usdc addresses
eth_address = Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
usdc_address = Web3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')



# ------------------ Web3 Functions -------------------

def check_price(token_address, amount_in):


    # check eth price in usd
    amount_out_ethusd = uniswap2_router.functions.getAmountsOut(Web3.to_wei(amount_in, 'ether'),
                                                         [eth_address, usdc_address]).call()
    eth_price = amount_out_ethusd[1]/1e6/amount_in

    # check token price if you buy
    amount_out_buy = uniswap2_router.functions.getAmountsOut(Web3.to_wei(amount_in, 'ether'), [eth_address, token_address]).call()
    token_price_buy = eth_price / (amount_out_buy[1] / amount_in / 10**(decimals))

    # check token price if you sell
    amount_out_sell = uniswap2_router.functions.getAmountsIn(Web3.to_wei(amount_in, 'ether'), [token_address, eth_address]).call()
    token_price_sell = eth_price / (amount_out_sell[0] / amount_in / 10**(decimals))

    # token expected if you buy
    expected_output_amount_buy = amount_out_buy[1]/10**(decimals)

    return token_price_buy, token_price_sell, expected_output_amount_buy, eth_price




def swap(amount_in, max_slippage, buy_tax):

    # Define the swap parameters

    token_price_buy, token_price_sell, expected_output_amount, eth_price = check_price(token_address, amount_in)
    amount_out_min = expected_output_amount * (1 - max_slippage - buy_tax)

    gas_price, gas_limit = get_gas_estimate()

    base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
    priority_fee = w3.to_wei('2', 'gwei')

    swap = uniswap2_router.functions.swapExactETHForTokens(
        int(amount_out_min),  # Set to 0 for no limit on the amount of token received
        [eth_address, token_address],
        my_address,
        int(time.time()) + 60 * 20  # Must be executed within 20 minutes
    ).build_transaction({
        'chainId': 1,  # Mainnet
        'value': w3.to_wei(amount_in, 'ether'),
        'from': my_address,
        'nonce': w3.eth._get_transaction_count(my_address),
        'gas': int(gas_limit * 1.5),
        'gasPrice': int(gas_price*1e9)
    })

    # Sign the transaction
    signed_txn = w3.eth.account.sign_transaction(swap, my_private_key)

    # Send the transaction
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Wait for the transaction to be mined
    txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)




def get_ether_balance(my_address):
    base_url = "https://api.etherscan.io/api"

    parameters = {
        "module": "account",
        "action": "balance",
        "address": my_address,
        "tag": "latest",
        "apikey": etherscan_api_key
    }

    response = requests.get(base_url, params=parameters)
    balance = response.json()['result']
    return balance

def get_max_from_window(prices_window):
    # retrieve the maximum price of the last 5 min
    return max(price for price, _ in prices_window)


def get_gas_estimate():
    base_url = "https://api.etherscan.io/api"
    payload = {
        "module": "gastracker",
        "action": "gasOracle",
        "apikey": etherscan_api_key
    }

    response = requests.get(base_url, params=payload)
    data = response.json()
    fast_gas_price = int(data['result']['FastGasPrice'])

    uniswap_function = uniswap2_router.functions.swapExactETHForTokens(
        0,
        [eth_address, token_address],
        my_address,
        int(time.time()) + 60 * 20
    )
    gas_limit = uniswap_function.estimate_gas({
        'from': my_address,
        'value': w3.to_wei(0.001, 'ether')
    })

    return fast_gas_price, gas_limit




# ------------------ TG interaction setup -------------------

bot = telebot.TeleBot(BOT_TOKEN)
markup = types.InlineKeyboardMarkup(row_width=2)
button1 = types.InlineKeyboardButton("Ape 0.05e", callback_data="button1_data")
button2 = types.InlineKeyboardButton("Ape 0.1e", callback_data="button2_data")
markup.add(button1, button2)


# ------------------ TG Functions -------------------


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the bot! Use /set_token to set the token address you wish to monitor.")

@bot.message_handler(commands=['set_token'])
def set_token(message):
    global token_address
    try:
        # Extract the token address from the message text. Assuming the format is "/set_token <token_address>"
        new_token_address = Web3.to_checksum_address(message.text.split()[1])  # Get the second part of the message after the space
        token_address = str(new_token_address)
        # retrieve token decimals
        ABI = [{
            "constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
            "payable": False, "stateMutability": "view", "type": "function"
        }]
        token_contract = w3.eth.contract(address=token_address, abi=ABI)
        decimals = token_contract.functions.decimals().call()

        with open('current_settings.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([new_token_address, decimals, buy_tax, max_slippage, drop_pct, 'True'])

        bot.reply_to(message, f"Token address set to: {token_address}")
    except IndexError:
        bot.reply_to(message, "Please provide the token address you want to monitor. \nUse: /set_token <token_address>")


@bot.message_handler(commands=['set_buy_tax'])
def set_buy_tax(message):
    global buy_tax
    try:
        # Extract the token address from the message text. Assuming the format is "/set_token <token_address>"
        new_buy_tax = message.text.split()[1]  # Get the second part of the message after the space
        buy_tax = float(new_buy_tax)/100

        with open('current_settings.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([token_address, decimals, buy_tax, max_slippage, drop_pct, 'True'])

        bot.reply_to(message, f"Buy tax set to: {buy_tax*100}%")
    except IndexError:
        bot.reply_to(message, "Please provide the buy tax of your token. (e.g. type 2 for 2%) \nUse: /set_buy_tax <buy_tax>")

@bot.message_handler(commands=['set_slippage'])
def set_buy_tax(message):
    global max_slippage
    try:
        # Extract the token address from the message text. Assuming the format is "/set_token <token_address>"
        new_max_slippage = message.text.split()[1]  # Get the second part of the message after the space
        max_slippage = float(new_max_slippage)/100

        with open('current_settings.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([token_address, decimals, buy_tax, max_slippage, drop_pct, 'True'])

        bot.reply_to(message, f"Max slippage set to: {max_slippage*100}%")
    except IndexError:
        bot.reply_to(message, "Please provide the max slippage you're willing to accept (in addition to token tax). (e.g. type 2 for 2%) \nUse: /set_slippage <max_slippage>")

@bot.message_handler(commands=['set_price_drop'])
def set_price_drop(message):
    global drop_pct
    try:
        # Extract the token address from the message text. Assuming the format is "/set_token <token_address>"
        new_drop_pct = float(message.text.split()[1])/100  # Get the second part of the message after the space
        drop_pct = new_drop_pct

        with open('current_settings.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([token_address, decimals, buy_tax, max_slippage, new_drop_pct])

        bot.reply_to(message, f"% set to: {new_drop_pct}")
    except IndexError:
        bot.reply_to(message, "Please provide the percentage drop in price that will trigger the alert. (e.g. type 20 for 20%) \nUse: /set_price_drop <drop_percentage>")


@bot.message_handler(commands=['current_settings'])
def current_settings(message):
    bot.reply_to(message, f"Token_address: {token_address} \n"
                          f"Buy tax = {buy_tax*100}% \n"
                          f"Max slippage = {max_slippage*100}% \n"
                          f"Price drop alert: -{drop_pct*100}% \n")

# TG button

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "button1_data":
        send_notification("buying 0.05e 🕐")

        swap(0.001, max_slippage)

        send_notification("bought 0.05e ✅")
    elif call.data == "button2_data":
        send_notification("buying 0.1e 🕐")

        swap(0.1, max_slippage)

        send_notification("bought 0.1e ✅")


# TG Notifications

def send_alert(message_text):
    chat_id = tg_chat_id
    bot.send_message(chat_id, message_text, reply_markup=markup)


def send_notification(message_text):
    chat_id = tg_chat_id
    bot.send_message(chat_id, message_text)




 #############################      MAIN CODE        ################################



if __name__ == "__main__":

    prices_window = deque()
    current_drop_pct = 0
    n = 0
    last_gas_update_time = time.time()
    price_data = check_price(token_address, 0.05)
    current_price = price_data[0]
    max_price = current_price


    if bot_setup == True:
        while n == 0:
            price_data = check_price(token_address, 0.05)
            current_price = price_data[0]
            current_timestamp = time.time()

            # Add the current price and timestamp to the deque
            prices_window.append((current_price, current_timestamp))

            # Remove prices older than 5 minutes from the front of the deque
            while prices_window and current_timestamp - prices_window[0][1] >= 300:
                prices_window.popleft()

            # Get the max price in the current window
            max_price = get_max_from_window(prices_window)

            # Check if the current price has dropped by 20% compared to the max
            if current_price < (1 - drop_pct) * max_price:
                n = 1
                current_drop_pct = (1 - (current_price/max_price))*100
                break
            # Wait for 5 seconds before the next price check
            time.sleep(5)


        # check current gas price and owner balance
        gas_price, gas_limit = get_gas_estimate()
        gas_price = int(gas_price) * 1e9
        gas_price_usd = "{:.2f}".format(int((gas_price * gas_limit / 1e18 * price_data[3]) * 100) / 100)



        eth_balance = float(get_ether_balance(my_address))/1e18
        nonce = w3.eth._get_transaction_count(my_address)

        # send the alert
        if eth_balance > 0.053:
            balance_msg = f"Current balance: {eth_balance} ETH ✅"
        else:
            balance_msg = f"Current balance is low: {eth_balance} ETH ❌"

        message = (f"Price dropped {current_drop_pct}% in the last 5 minutes, want to buy?"
                                      f"\nPrice changed from {int(max_price*100)/100}$ to {int(current_price*100)/100}$ "
                                      f"\nGas price: {int(gas_price)}gwei ~ {gas_price_usd}$"
                                      f"\n{balance_msg}")


        send_alert(message)
    bot.polling(none_stop=True)