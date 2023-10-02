# Dip Sniper Telegram bot

This bot provides functionality for monitoring and trading ERC-20 tokens on the Ethereum blockchain via Uniswap V2. It integrates with Telegram to allow users to set various parameters and receive alerts.

## Features:

- Monitor specific token prices in real-time.
- Check the current Ether price in USD.
- Make swaps on Uniswap.
- Integrate with Etherscan to fetch Ether balance.
- Allow users to set a token address, buy tax, max slippage, and price drop percentage via Telegram commands.
- Send alerts and notifications via Telegram.

## Installation

1. **Prerequisites**: 
   - Python 3.x
   - An Ethereum wallet (with some ETH to cover gas fees).
   - Telegram bot token.

2. **Python packages required**:
     - pyTelegramBotAPI
     - web3
     - requests
     - python-dotenv

3. **Personal Keys required**:
     - An ethereum RPC URL: I use alchemy, just go to their website, register and you can activate an RPC
     - A private and public key of a hot wallet (THIS WALLET IS NOT SAFE ANYMORE WHEN YOU PUT IT IN THE CODE)
     - An etherscan API: you can get one for free on their website, you need this for gas estimation
     - Telegram Bot Token: if you followed my [Mirror Guide](https://mirror.xyz/0x0992ee967aCd2c8A8d6f42a2623C6850028Bae7E/Qw4vKOPfSWSsQn6HVyulxDsDdTKI9oIB5D44B9hc8Ho), you should already have one, otherwise follow the guide to get it.

4. **How to get your telegram chat ID**:

Paste this in your python editor:

```python
import telebot

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['getid'])
def send_chat_id(message):
    bot.reply_to(message, f"Your Chat ID is: {message.chat.id}")

bot.polling(none_stop=True)
```

Click run, then go to your telegram bot chat and type /getid. You will get the telegram chat ID, you need it to send messages to the chat from Python. You can now delete the code shown, you don't need it anymore.

5. **Setup a .env file**
Create a file called .env in your main folder, open it with notepad and paste this:

```
RPC_URL = ''
YOUR_PUBLIC_KEY = ''
YOUR_PRIVATE_KEY = ''
TELEGRAM_BOT_TOKEN = ''
ETHERSCAN_API_KEY = ''
TG_CHAT_ID = ''
```

Now fill every variable with yours. You should get something like this
```
RPC_URL = 'https://eth-mainnet.g.alchemy.com/v2/oiiUosdhjgfskg-d9u5o8DOjRkdflgLi'
YOUR_PUBLIC_KEY = '0x45fcba20AdE9047464EA41a80d1846901E9Fd'
YOUR_PRIVATE_KEY = '102ab0bdeccbc8169adFb02890ebcafe09493821e5e090c3c2c80c0'
TELEGRAM_BOT_TOKEN = '6645609846:AAElisiodfjn34-mdpfgsdofg-4mh0jOl4ZI'
ETHERSCAN_API_KEY = 'CJKG375D435SYOHNFD4935BISUIO'
TG_CHAT_ID = '1032566890'
```

6. **Get the code and settings**
- Copy or download the tgbot_dip_sniper.py and the current_settings.csv in a folder.
-  Put the .env file in the same folder

You're good to go!



# How it works

Let's see what's inside the code. First of all, the code is divided in 7 parts:


1. Imports and keys setup: you will set the private and public keys of a hot wallet, etherscan API key to retrieve gas info, the tg bot token, an RPC key (I use alchemy, you only need to go to the website and create an API key for ethereum for free)

2. Web3 interaction setup: a bunch of initial stuff like setting up uniswap router ABI, weth and usdc address, etc.

3. Web3 interaction logics:
   - A check_price() function to monitor the price
   - A get_max_from_window() function to know the maximum price of the last 5 minutes
   - A get_gas_estimate() function to retrieve the current gas info from etherscan
   - A swap() function to make the swap on uniswap
   - A get_ether_balance() to know your current eth in the hot wallet

4. Telegram bot interaction setup: here you setup your bot and a few items like the buttons you will see when you buy

5. Telegram commands:
   - set_token, to set your token address
   - set_price_drop
   - set_buy_tax (retrieving it automatically is quite complex, I will leave it for the next guide)
   - set_slippage, to edit the slippage you’re willing to accept in addition to token tax
   - current_settings to show the current configuration

6. Telegram logics:
   - Send the alert
   - Send a generic notification
   - Buy when the button is clicked

7. Main script: this part is the core of the bot. As said earlier, when you run the code, it loops the check_price() function to watch the price of the token. When the price drops, it breaks the loop and send the alert


# Imports and Keys setup

This code imports all the packages needed, load the variables contained in the .env file and the current bot settings in the current_settings.csv

```python

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


```

# Web3 interactions setup

This code setup a bunch of things needed to interact with the blockchain and with uniswap in particcular.

```python

# ------------------ Web3 interaction setup -------------------
w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
w3.middleware_onion.add(middleware.simple_cache_middleware)
w3.middleware_onion.add(middleware.time_based_cache_middleware)
w3.middleware_onion.inject(middleware.geth_poa_middleware, layer=0)
w3.eth.set_gas_price_strategy(medium_gas_price_strategy)

# Define the Uniswap v2 router contract
router_address = Web3.to_checksum_address('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')  # Uniswap v2 router
router_abi = [...]

# Define the eth and usdc addresses
eth_address = Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
usdc_address = Web3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')
```


# Web3 functions

This part contains the main functions we need. In particular:

1. **Check_price()**: this function takes as input the token address and the amount to exchange and invoke the getAmountsOut() function of UniswapV2 router to get the current eth price, the current token price in weth and calculate the current price of the token in dollars. It returns the prices for both a buy and a sell action, the expected amount of token received if you buy and the eth price.

```python
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
```


2. **get_gas_estimate()**: this function call etherscan API to get the current gas price (usually between 15 and 50 in normal days). As you can see, it retrieves the 'FastGasPrice', because in this ccase we need for the transaction to be as fast as possible since we want to snipe dips. After retrieving gas price, the function calls the uniswap router to get the optimal gas limit (usually between 150,000 and 500,000) that is needed to build the transaction later.


```python
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
```


3. **Swap()**: this function invokes the swapExactETHForTokens function of uniswap Router, that lets you swap a fixed amount of eth for another token. It takes in input the amount you want to swap and the maximum slippage (that you have set through the telegram bot).
The function calculates the amount_out_min to be sure you don't get eaten on slippage, and then uses the gas_estimate() function to retrieve the best settings for the gas.


```python

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
```


4. Get_ether_balance(): this function retrieves your current eth balance using etherscan

```python

def get_ether_balance(my_address):
    base_url = "https://api.etherscan.io/api"

    parameters = {
        "module": "account",
        "action": "balance",
        "contractaddress": token_address,
        "address": my_address,
        "tag": "latest",
        "apikey": etherscan_api_key
    }

    response = requests.get(base_url, params=parameters)
    balance = response.json()['result']
    return balance

```

5. get_max_from_window(): this function retrieves the max price of the selected windows (set to 5 minutes)

```python
def get_max_from_window(prices_window):
    # retrieve the maximum price of the last 5 min
    return max(price for price, _ in prices_window)
```




# Telegram Setup

This portion of code just setup the tg bot using the bot token and defines the buttons used to buy.

```python
# ------------------ TG interaction setup -------------------

bot = telebot.TeleBot(BOT_TOKEN)
markup = types.InlineKeyboardMarkup(row_width=2)
button1 = types.InlineKeyboardButton("Ape 0.05e", callback_data="button1_data")
button2 = types.InlineKeyboardButton("Ape 0.1e", callback_data="button2_data")
markup.add(button1, button2)

```


# Telegram Functions

This part contains the logics used to use the telegram commands and interactions. First of all, let's define how the telegram commands works. Let's start with the set_token command.

The first thing to do is to set the hook to the bot using
`@bot.message_handler(commands=['set_token'])`
Then you define the logics, that do the following:
1. Retrive the new token_address from the user message
2. Retrieve the token decimals
3. Update the current_settings.csv with the new values

```python
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


```

All the other telegram commands (set_buy_tax, set_slippage, set_price_drop) work in the same way except for /current_settings that just send a notification with the current configuration:

```python
@bot.message_handler(commands=['current_settings'])
def current_settings(message):
    bot.reply_to(message, f"Token_address: {token_address} \n"
                          f"Buy tax = {buy_tax*100}% \n"
                          f"Max slippage = {max_slippage*100}% \n"
                          f"Price drop alert: -{drop_pct*100}% \n")

```


# Telegram buttons setup

Now we define what happens when we click the buttons in the chat on telegram. As you can see, we send a notificcation with "buying x 🕐", then we run a swap using the swap() function. At the end, we send the confirmation.

You can customize the default amounts to swap as you want. In future I probably will show how to make a "set custom buy" to edit directly in the chat.

```python

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "button1_data":
        send_notification("buying 0.05e 🕐")

        swap(0.05, max_slippage)

        send_notification("bought 0.05e ✅")

    elif call.data == "button2_data":
        send_notification("buying 0.1e 🕐")

        swap(0.1, max_slippage)

        send_notification("bought 0.1e ✅")

```


# Telegram notifications

Here we define the function that sends the alert, to trigger when the price drops

```python
def send_alert(message_text):
    chat_id = tg_chat_id
    bot.send_message(chat_id, message_text, reply_markup=markup)

```


# Main code

The main code is the code that will be run and contains the loops in which the code will continuously check price. Let's begin and initialize some variables, the current time and current token price:

```python
if __name__ == "__main__":

    prices_window = deque()
    current_drop_pct = 0
    n = 0
    last_gas_update_time = time.time()
    price_data = check_price(token_address, 0.05)
    current_price = price_data[0]
    max_price = current_price
```

Now if the bot has been started once (technically if a token address has been set one time at least), the code starts a loop in which:
1. It checks the price
2. Add the current price to the memory
3. Get from the memory the max price of the last 5 minutes
4. Slides the 5 minutes window
5. Calculate if a drop > than the % set has happened in the last 5 minutes



```python

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
```

If the price has dropped, the code breaks the loop and do the following:

1. check the current gas stats
2. check your current eth balance
3. send an alert 

The message you will receive is something like this

![image](https://github.com/lekos22/tgbot-dip-sniper/assets/140423090/0be0cc67-b4fb-438a-b1a4-0b9e0b3652fd)


The code checks your balance and alert you if you don't have enough eth to make the transaction.

```python

        # check current gas price and owner balance
        gas_price, gas_limit = get_gas_estimate()
        gas_price = int(gas_price) * 1e9
        gas_price_usd = "{:.2f}".format(int((gas_price * gas_limit / 1e18 * price_data[3]) * 100) / 100)



        eth_balance = float(get_ether_balance(my_address))/1e18

        # send the alert
        if eth_balance > 0.053:
            balance_msg = f"Current balance: {eth_balance} ETH ✅"
        else:
            balance_msg = f"Current balance is low: {eth_balance} ETH ❌"

        message = (f"Price dropped {current_drop_pct}% in the last 5 minutes, want to buy?"
                                      f"\nPrice changed from {max_price}$ to {current_price}$ "
                                      f"\nGas price: {int(gas_price)}gwei ~ {gas_price_usd}$"
                                      f"\n{balance_msg}")


        send_alert(message)
    bot.polling(none_stop=True)
```

The `bot.polling(none_stop=True)` code is a function that make the bot in idle when the loop is completed.


# How to run the bot

In order for the bot to work (meaning bot watching the price AND being able to update the settings), the python code must be running. This means you can do one of the following:

1. Use your own pc to run the code, and make it run only when you (for example) go outside with no access to it, in order to be able to snipe the dips from the phone. To do this, when you go outside just run the code and let it go (SUGGESTED)

2. Setup a server that lets you host python code to constantly run (some security concerns...)


# Conclusions

That's all for this first guide, hope you enjoyed it. follow me at my [Twitter](https://twitter.com/ponzinomics21) and subscribe to my [Mirror](https://mirror.xyz/0x0992ee967aCd2c8A8d6f42a2623C6850028Bae7E)
