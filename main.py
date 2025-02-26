import requests
import time
import json
from web3 import Web3
from colorama import Fore, Style, init
from utils.banner import banner 
import random
from sign import update_token
import asyncio

init(autoreset=True)
def prompt_auto_steal():
    user_input = input(f"{Fore.YELLOW}Would you like to enable auto steal? (y/yes - n/no): ").strip().lower()
    if user_input in ['yes', 'y']:
        return True
    elif user_input in ['no', 'n']:
        return False
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")
        return prompt_auto_steal()  
print(Fore.MAGENTA + Style.BRIGHT + banner + Style.RESET_ALL)
auto_steal_enabled = prompt_auto_steal()
if auto_steal_enabled:
    print("Auto steal is enabled.")
else:
    print("Auto steal is disabled.")


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

        if response.status_code == 401:        
            return "Unauthorized"
        elif not response.ok:
            print(f"{Fore.RED}HTTP error! Status: {response.status_code}")
            return None

        return response.json()
    except Exception as error:
        print(f"{Fore.RED}An error occurred: {error}")
        return None
    
def generate_random_id():
    return random.randint(1, 440506)

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
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"{Fore.GREEN}Transaction sent with hash: {tx_hash.hex()}")

    # Wait for the transaction receipt
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

def main():
    web3 = Web3(Web3.HTTPProvider('https://rpc.mintchain.io'))
    ApiUrl = "https://www.mintchain.io/api/tree"
    recipient_address = '0x12906892AaA384ad59F2c431867af6632c68100a'  

    try:
        while True:
            private_keys_tokens = load_private_keys_tokens('token.json')
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
                if profile == "Unauthorized":
                    print(f"{Fore.RED}Unauthorized. Trying update the access token.")
                    asyncio.run(update_token())
                    break
                if profile and profile.get('result'):
                    balance = profile['result']['energy']
                    treeId = profile['result']['treeId']
                    stealCount = profile['result']['stealCount']
                    
                    print(f"{Fore.CYAN}Tree ID: {treeId} | Balance: {balance} | Steal Count: {stealCount}/8")

                    counts = colay(f"{ApiUrl}/turntable/count", 'GET', headers)
                    if counts and counts.get('result'):
                        count = counts['result']['count']
                        print(f"{Fore.CYAN}Spin used today: {count}/10")
    
                        if count != 10:
                            signIn = colay(f"{ApiUrl}/get-forest-proof?type=Signin", 'GET', headers)
                            if signIn and signIn.get('result'):
                                hex_data = signIn['result']['tx']  
                                print(f"{Fore.YELLOW}Trying to sign-in for: {sender_address}")  
                                send_transactions(private_key, recipient_address, sender_address, hex_data, web3)
                                time.sleep(3)
        
                                for spin_count in range(count, 10):
                                    spins = colay(f"{ApiUrl}/get-forest-proof?type=Turntable", 'GET', headers)
                                    if spins and spins.get('result'):
                                        awards = spins['result']['energy']
                                        hex_data = spins['result']['tx']  
                                        print(f"{Fore.YELLOW}Trying to spin for: {sender_address}")
                                        
                                        send_transactions(private_key, recipient_address, sender_address, hex_data, web3)
                                        print(f"{Fore.CYAN}Spin No: {spin_count + 1}, Rewards: {awards}")
                                        time.sleep(5)
                                        
                    if balance > 1000:
                        print(f"{Fore.CYAN}Trying To Inject {balance} To Grow GreenId")
                        payload = {"energy": str(balance - 1000), "address": sender_address}
                        inject = colay(f"{ApiUrl}/inject", 'POST', headers, payload)
                        if inject and inject.get('result'):
                            print(f"{Fore.GREEN}Inject Success: {inject['result']}")
                        else:
                            print(f"{Fore.RED}Failed to inject energy.")
                            
                    while stealCount < 8 and auto_steal_enabled:
                        random_id = generate_random_id()
                        check_acc = colay(f"https://www.mintchain.io/api/tree/steal/energy-list?id={random_id}", 'GET', headers)
                        print(f"Checking account ID: {random_id} {check_acc}")
                        
                        if check_acc and check_acc.get('result'):
                            stealable = check_acc['result'][0].get('stealable', False) 
                                                                                    
                            if stealable:
                                steal = colay(f"https://www.mintchain.io/api/tree/get-forest-proof?type=Steal&id={random_id}", 'GET', headers)
                                print(f"Steal action initiated for ID: {random_id}")
                                
                                if steal and steal.get('result'):
                                    hex_data = steal['result']['tx']  
                                    print("send transactions for stealing...")
                                    send_transactions(private_key, recipient_address, sender_address, hex_data, web3)
                                    stealCount += 1
                                    print(f"{Fore.GREEN}Steal Successfully - Steal count left: {stealCount}")
                            else:
                                print("Energy not stealable.")
                        else:
                            print("Cannot stealing this account.")

            print(f"{Fore.MAGENTA}All accounts have been processed. Cooldown 1 hour...")  
            time.sleep(60 * 60) # 1 hour
        
    except Exception as error:
        print(f"{Fore.RED}An error occurred: {error}")

if __name__ == "__main__":
    main()
