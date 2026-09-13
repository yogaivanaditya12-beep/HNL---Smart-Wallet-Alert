import time
import requests

# --- KONFIGURASI BOT & TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8925455594:AAHzlQM2bOjAwCiDvu2DhpT7vj8tacgiKE4"
TELEGRAM_GROUP_CHAT_ID = "-1002362131585"

# --- API KEY ---
ETHERSCAN_API_KEY = "MASUKKAN_API_KEY_ETHERSCAN_DISINI"

# --- DATABASE SMART WALLET & KOL ---
WATCHED_WALLETS_SOL = {
    "GZ1yiJKTq8Mc6RiY2WQrzph8wJcizSLGgyhr4RSgnuUo": "Sol Smart 1",
    "9LxMdvs1m8QRFvFuhvzzMXykAkpaHTJhktULdpBztUMm": "Sol Smart 2",
    "AC44afvZ8zpWa3CXBM1iCQEcPVktaPck4qYG8vKfiYi6": "Sol Smart 3",
    "CEUA7zVoDRqRYoeHTP58UHU6TR8yvtVbeLrX1dppqoXJ": "Sol Smart 4",
    "9vau6AGRB7ZWaNXrL6RfsbztB1qdLu9RkPzFcgD37UMb": "Sol Smart 5",
    "6ANGS6SSCxkv6hV3iymHHMESqDz7EFaecCwHA8qTswpr": "Sol Smart 6",
}

WATCHED_WALLETS_EVM = {
    "0x29fde8d32398c0fd7aad1e20b655846666666666": "Robinhood Whale 1",
    "0x21faf075bbd36f3eaeb651e118ac26363e3704b6": "Robinhood Whale 2",
    "0xce1d7f8c2588a87d29fa1743ac9f8096c29598ef": "Robinhood Whale 3",
    "0x9d7451dd30a9d264865acf3ca8c4741d97761d9f": "Robinhood Whale 4",
    "0x07fb753a79177927fa871eaa6eb1ef60a00d3473": "Robinhood Whale 5",
    "0x15b8ceec9120d30c7284d9d5eee9efb3659211ef": "Robinhood Whale 6",
}

last_tx_cache = {}

def send_telegram_alert(network, name, address, tx):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    message = (
        f"🚨 *SMART WALLET ALERT ({network})* 🚨\n\n"
        f"👤 *Target:* {name}\n"
        f"👛 *Wallet:* `{address[:6]}...{address[-4:]}`\n"
        f"🟢 *Action:* {tx['type']} \n"
        f"💰 *Status:* `{tx['amount_usd']}`\n"
        f"🪙 *Asset:* {tx['token_name']}\n"
        f"📋 *Detail / CA:*\n`{tx['ca']}`"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📊 DexScreener", "url": f"https://dexscreener.com/search?q={tx['ca']}"},
                {"text": "🔍 Explorer", "url": f"https://solscan.io/tx/{tx['hash']}" if network == "SOLANA" else f"https://etherscan.io/tx/{tx['hash']}"}
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

def check_solana_activity(wallet_address):
    try:
        # Menggunakan public RPC Solana JSON-RPC untuk deteksi signature terbaru yang lebih akurat
        rpc_url = "https://api.mainnet-beta.solana.com"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet_address, {"limit": 1}]
        }
        response = requests.post(rpc_url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "result" in data and len(data["result"]) > 0:
                sig_info = data["result"][0]
                tx_hash = sig_info.get("signature")
                return {
                    "hash": tx_hash,
                    "type": "SOLANA SWAP / TX",
                    "amount_usd": "Live Activity Detected",
                    "token_name": "Solana Token",
                    "ca": wallet_address
                }
        return None
    except Exception as e:
        return None

def check_evm_activity(wallet_address):
    try:
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&page=1&offset=1&sort=desc&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and len(data.get("result", [])) > 0:
                tx_info = data["result"][0]
                return {
                    "hash": tx_info.get("hash"),
                    "type": "EVM TX / SWAP",
                    "amount_usd": "Whale Transfer",
                    "token_name": "ERC-20 Asset",
                    "ca": tx_info.get("to") or wallet_address
                }
        return None
    except Exception as e:
        return None

def main():
    print("Bot Alert V2 Berjalan dengan Solana RPC & Etherscan...")
    while True:
        for address, name in WATCHED_WALLETS_SOL.items():
            tx = check_solana_activity(address)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("SOLANA", name, address, tx)
            time.sleep(3)

        for address, name in WATCHED_WALLETS_EVM.items():
            tx = check_evm_activity(address)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("EVM", name, address, tx)
            time.sleep(3)

        time.sleep(20)

if __name__ == "__main__":
    main()
