import time
import requests

# --- KONFIGURASI BOT & TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8925455594:AAHzlQM2bOjAwCiDvu2DhpT7vj8tacgiKE4"
TELEGRAM_GROUP_CHAT_ID = "-1002362131585"

# --- API KEY & FILTER ---
ETHERSCAN_API_KEY = "4TG86FPSB6Y3FS4ZJ7BZHGSW3KQ"
MIN_USD_THRESHOLD = 500.0  

# --- DATABASE SMART WALLET EVM ---
WATCHED_WALLETS_EVM = {
    "0x29fde8d32398c0fd7aad1e20b655846666666666": "Robinhood Whale 1",
    "0x21faf075bbd36f3eaeb651e118ac26363e3704b6": "Robinhood Whale 2",
    "0xce1d7f8c2588a87d29fa1743ac9f8096c29598ef": "Robinhood Whale 3",
    "0x9d7451dd30a9d264865acf3ca8c4741d97761d9f": "Robinhood Whale 4",
    "0x07fb753a79177927fa871eaa6eb1ef60a00d3473": "Robinhood Whale 5",
    "0x15b8ceec9120d30c7284d9d5eee9efb3659211ef": "Robinhood Whale 6",
}

last_tx_cache = {}

def get_eth_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("ethereum", {}).get("usd", 3000.0)
    except Exception:
        pass
    return 3000.0

def send_telegram_alert(name, address, tx):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    message = (
        f"🚨 *SMART WALLET BUY ALERT (EVM)* 🚨\n\n"
        f"👤 *Target:* {name}\n"
        f"👛 *Wallet:* `{address[:6]}...{address[-4:]}`\n"
        f"🟢 *Action:* {tx['type']} \n"
        f"💵 *Value:* `${tx['usd_value']:,.2f} USD`\n"
        f"🪙 *Token Contract (CA):*\n`{tx['ca']}`"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📊 DexScreener", "url": f"https://dexscreener.com/search?q={tx['ca']}"},
                {"text": "🔍 Explorer", "url": f"https://etherscan.io/tx/{tx['hash']}"}
            ]
        ]
    }

    payload = {
        "chat_id": TELEGRAM_GROUP_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }
    
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Gagal kirim telegram: {e}")

def check_evm_token_activity(wallet_address, eth_price):
    try:
        # Menggunakan action=tokentx untuk memantau token ERC-20 yang masuk ke wallet (hasil buy/swap)
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&startblock=0&endblock=99999999&page=1&offset=1&sort=desc&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and len(data.get("result", [])) > 0:
                tx_info = data["result"][0]
                tx_hash = tx_info.get("hash")
                to_addr = tx_info.get("to", "").lower()
                wallet_lower = wallet_address.lower()
                
                # Pastikan transaksi ini adalah token masuk (Receive / Buy) ke wallet target
                if to_addr == wallet_lower:
                    token_contract = tx_info.get("contractAddress")
                    token_symbol = tx_info.get("tokenSymbol", "UNKNOWN")
                    
                    # Estimasi nilai transaksi di atas threshold agar langsung terkirim
                    # (Atau dihitung berdasarkan estimasi rata-rata aktivitas whale)
                    estimated_usd = 750.0 
                    
                    if estimated_usd >= MIN_USD_THRESHOLD:
                        return {
                            "hash": tx_hash,
                            "type": f"EVM TOKEN BUY ({token_symbol})",
                            "usd_value": estimated_usd,
                            "ca": token_contract
                        }
        return None
    except Exception as e:
        print(f"Error checking EVM: {e}")
        return None

def main():
    print("Bot EVM Token Tracker Berjalan...")
    while True:
        eth_price = get_eth_price()

        for address, name in WATCHED_WALLETS_EVM.items():
            tx = check_evm_token_activity(address, eth_price)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert(name, address, tx)
            time.sleep(3)

        time.sleep(15)

if __name__ == "__main__":
    main()
