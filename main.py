import requests
import time
import json
from web3 import Web3
from colorama import Fore, Style, init
from utils.banner import banner 
init(autoreset=True)

print(Fore.MAGENTA + Style.BRIGHT + banner + Style.RESET_ALL)
def load_private_keys_tokens(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return [(item['private_key'], item['access_token']) for item in data['private_keys_tokens']]

def colay(url, method, headers, payload_data=None):
    try:
        if method == 'POST':
            response = requests.post(url, headers=headers, json=payload_data)
        else:  
            response = requests.get(url, headers=headers)

        if not response.ok:
            print(f"{Fore.RED}HTTP error! Status: {response.status_code}")
            return None

        return response.json()
    except Exception as error:
        print(f"{Fore.RED}An error occurred: {error}")
        return None

def send_transactions(private_key, recipient_address, sender_address, hex_data, web3):
    
    tx_data = {
        'to': recipient_address,
        'from': sender_address,
        'value': 0,  
        'gas': 100000,  
        'gasPrice': web3.to_wei('0.0001', 'gwei'),  
        'data': hex_data,
        'nonce': web3.eth.get_transaction_count(sender_address),  
    }
    
    signed_tx = web3.eth.account.sign_transaction(tx_data, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"{Fore.GREEN}Transaction sent with hash: {tx_hash.hex()}")

    # Wait for the transaction receipt
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

def main():
    web3 = Web3(Web3.HTTPProvider('https://rpc.mintchain.io'))
    private_keys_tokens = load_private_keys_tokens('token.json')
    ApiUrl = "https://www.mintchain.io/api/tree"
    recipient_address = '0x12906892AaA384ad59F2c431867af6632c68100a'  

    try:
        while True:
            for private_key, access_token in private_keys_tokens:
                account = web3.eth.account.from_key(private_key)
                sender_address = account.address
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
                }
                
                profile = colay(f"{ApiUrl}/user-info?type=", 'GET', headers)
                if profile:
                    balance = profile['result']['energy']
                    treeId = profile['result']['treeId']
                    print(f"{Fore.CYAN}Tree ID: {treeId} | Balance: {balance}")

                    counts = colay(f"{ApiUrl}/turntable/count", 'GET', headers)
                    if counts:
                        count = counts['result']['count']
                        print(f"{Fore.CYAN}Spin used today: {count}/10")
    
                        if count != 10:
                            signIn = colay(f"{ApiUrl}/get-forest-proof?type=Signin", 'GET', headers)
                            if signIn:
                                hex_data = signIn['result']['tx']  
                                print(f"{Fore.YELLOW}Trying to sign-in: {hex_data}")  
                                send_transactions(private_key, recipient_address, sender_address, hex_data, web3)
                                time.sleep(3)
        
                                for spin_count in range(count, 10):
                                    spins = colay(f"{ApiUrl}/get-forest-proof?type=Turntable", 'GET', headers)
                                    if spins:
                                        awards = spins['result']['energy']
                                        hex_data = spins['result']['tx']  
                                        print(f"{Fore.YELLOW}Trying to spin: {hex_data}")
                                        
                                        send_transactions(private_key, recipient_address, sender_address, hex_data, web3)
                                        print(f"{Fore.CYAN}Spin No: {spin_count}, Rewards: {awards}")
                                        time.sleep(5)
                                        
                    if balance > 1000:
                        print(f"{Fore.CYAN} Trying To Inject {balance} To Grow GreenId")
                        payload = {"energy": str(balance), "address": sender_address}
                        inject = colay(f"{ApiUrl}/inject", 'POST', headers, payload)
                        if inject:
                            print(f"{Fore.GREEN}Inject Success: {inject['result']}")
                        else:
                            print(f"{Fore.RED}Failed to inject energy.")
                            
            print(f"{Fore.MAGENTA}All accounts have been processed. Cooldown...")  
            time.sleep(60 * 60)
        
    except Exception as error:
        print(f"{Fore.RED}An error occurred: {error}")

if __name__ == "__main__":
    main()
