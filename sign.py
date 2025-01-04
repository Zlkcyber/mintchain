import json
from web3 import Web3
from eth_account.messages import encode_defunct
import random
import requests

# Async function to handle API requests
async def colay(url, method, headers, payload_data=None):
    try:
        if method == 'POST':
            response = requests.post(url, headers=headers, json=payload_data)
        else:  
            response = requests.get(url, headers=headers)

        if not response.ok:
            print(f"HTTP error! Status: {response.status_code}")
            return None

        return response.json()
    except Exception as error:
        print(f"An error occurred: {error}")
        return None

# Load the tokens.json file
with open('token.json', 'r') as file:
    tokens_data = json.load(file)

# Function to sign the message
def sign_message(private_key, message):
    web3 = Web3()
    message_encoded = encode_defunct(text=message)
    signed_message = web3.eth.account.sign_message(message_encoded, private_key)
    return signed_message

# Function to get the address 
async def get_address_from_private_key(private_key):
    web3 = Web3(Web3.HTTPProvider('https://rpc.mintchain.io'))

    if not web3.is_connected():
        raise Exception("Failed to connect to Ethereum network")

    account = web3.eth.account.from_key(private_key)
    return account.address

def get_headers():
    return {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }

# Async login function
async def login(signature, address, message):
    payload = {"address": address, "signature": signature, "message": message}
    headers = get_headers()  
    token = await colay("https://www.mintchain.io/api/tree/login", "POST", headers, payload)
    return token["result"]

# Function to update the token
def update_token_in_json(private_key, new_access_token):
    for token in tokens_data["private_keys_tokens"]:
        if token["private_key"] == private_key:
            token["access_token"] = new_access_token
            break

    with open('token.json', 'w') as file:
        json.dump(tokens_data, file, indent=4)

# update token
async def update_token():
    for token in tokens_data["private_keys_tokens"]:
        private_key = token["private_key"]
        address = await get_address_from_private_key(private_key)  

        nonce = random.randint(1000000, 9999999)
        message = f"You are participating in the Mint Forest event:\n {address}\n\nNonce: {nonce}"
        signed_message = sign_message(private_key, message)
        signature = signed_message.signature.hex()
        token_response = await login(signature, address, message)
        access_token = token_response["access_token"]

        update_token_in_json(private_key, access_token)

        print(f"Address: {address}")
        print(f"Access Token: {access_token}")
