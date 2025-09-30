import requests
import json

def get_bitcoin_balance(address):
    try:
        # Get data from blockchain.info API
        url = f"https://blockchain.info/rawaddr/{address}"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Create balance information
        balance_info = {
            "address": address,
            "balance_satoshis": data["final_balance"],
            "balance_btc": data["final_balance"] / 100000000,
            "total_received": data["total_received"],
            "total_sent": data["total_sent"],
            "transaction_count": data["n_tx"]
        }
        
        # Save to JSON file
        filename = f"bitcoin_balance_{address}.json"
        with open(filename, 'w') as f:
            json.dump(balance_info, f, indent=2)
        
        return balance_info, filename
        
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch data - {e}")
        return None, None
    except KeyError as e:
        print(f"Error: Unexpected API response format - {e}")
        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

def main():
    # Get Bitcoin address from user input
    address = input("Enter Bitcoin address: ").strip()
    
    if not address:
        print("Error: No address provided!")
        return
    
    print(f"Fetching balance for: {address}")
    
    # Get balance and save to JSON
    balance_data, filename = get_bitcoin_balance(address)
    
    if balance_data and filename:
        print(f"\nBalance information saved to: {filename}")
        print(f"Balance: {balance_data['balance_btc']:.8f} BTC")
        print(f"Satoshis: {balance_data['balance_satoshis']:,}")
        print(f"Total Received: {balance_data['total_received']:,} satoshis")
        print(f"Total Sent: {balance_data['total_sent']:,} satoshis")
        print(f"Transactions: {balance_data['transaction_count']}")
    else:
        print("Failed to get balance information")

if __name__ == "__main__":
    main()
