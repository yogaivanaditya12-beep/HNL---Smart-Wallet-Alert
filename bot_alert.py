import time
import requests

# --- KONFIGURASI BOT & TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8925455594:AAHzlQM2bOjAwCiDvu2DhpT7vj8tacgiKE4"
TELEGRAM_GROUP_CHAT_ID = "-1002362131585"

# --- DATABASE SMART WALLET & KOL ---
WATCHED_WALLETS_SOL = {
    # Wallet Smart Money / Whale Sebelumnya
    "GZ1yiJKTq8Mc6RiY2WQrzph8wJcizSLGgyhr4RSgnuUo": "Sol Smart 1",
    "9LxMdvs1m8QRFvFuhvzzMXykAkpaHTJhktULdpBztUMm": "Sol Smart 2",
    "AC44afvZ8zpWa3CXBM1iCQEcPVktaPck4qYG8vKfiYi6": "Sol Smart 3",
    "CEUA7zVoDRqRYoeHTP58UHU6TR8yvtVbeLrX1dppqoXJ": "Sol Smart 4",
    "9vau6AGRB7ZWaNXrL6RfsbztB1qdLu9RkPzFcgD37UMb": "Sol Smart 5",
    "6ANGS6SSCxkv6hV3iymHHMESqDz7EFaecCwHA8qTswpr": "Sol Smart 6",
    # Tambahan Wallet KOL / Alpha Caller Solana
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "Solana Program / KOL Alpha 1",
    "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1": "Raydium Liquidity KOL Pool",
}

WATCHED_WALLETS_EVM = {
    # Wallet Whale Sebelumnya
    "0x29fde8d32398c0fd7aad1e20b655846666666666": "Robinhood Whale 1",
    "0x21faf075bbd36f3eaeb651e118ac26363e3704b6": "Robinhood Whale 2",
    "0xce1d7f8c2588a87d29fa1743ac9f8096c29598ef": "Robinhood Whale 3",
    "0x9d7451dd30a9d264865acf3ca8c4741d97761d9f": "Robinhood Whale 4",
    "0x07fb753a79177927fa871eaa6eb1ef60a00d3473": "Robinhood Whale 5",
    "0x15b8ceec9120d30c7284d9d5eee9efb3659211ef": "Robinhood Whale 6",
    "0x4b10707123c79f6e99be486dcd95d60323988d76": "Robinhood Whale 7",
    "0x150952108f28dcaf4e4542090e67cd2696563944": "Robinhood Whale 8",
    # Tambahan Wallet KOL / Insider EVM
    "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8": "Binance Hot Wallet KOL/Whale",
    "0x28C6c06298d514Db089934071355E5743bf21d60": "Binance 14",
}

last_tx_cache = {}

def send_telegram_alert(network, name, address, tx):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    message = (
        f"🚨 *KOL / SMART WALLET ALERT ({network})* 🚨\n\n"
        f"👤 *Target:* {name}\n"
        f"👛 *Wallet:* `{address[:6]}...{address[-4:]}`\n"
        f"🟢 *Action:* {tx['type']} \n"
        f"💰 *Estimasi Nilai:* `{tx['amount_usd']}`\n"
        f"🪙 *Token:* {tx['token_name']}\n"
        f"📋 *Contract Address (CA):*\n`{tx['ca']}`"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📊 DexScreener", "url": f"https://dexscreener.com/search?q={tx['ca']}"},
                {"text": "🔍 Solscan/Etherscan", "url": f"https://solscan.io/tx/{tx['hash']}" if network == "SOLANA" else f"https://etherscan.io/tx/{tx['hash']}"}
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
        url = f"https://public-api.solscan.io/account/transactions?account={wallet_address}&limit=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                tx_info = data[0]
                tx_hash = tx_info.get("txHash")
                return {
                    "hash": tx_hash,
                    "type": "KOL SWAP / BUY",
                    "amount_usd": "Active Move",
                    "token_name": "Solana Asset",
                    "ca": wallet_address
                }
        return None
    except Exception as e:
        return None

def check_evm_activity(wallet_address):
    try:
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&page=1&offset=1&sort=desc&apikey=YourEtherscanAPIKey"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "1" and len(data["result"]) > 0:
                tx_info = data["result"][0]
                return {
                    "hash": tx_info.get("hash"),
                    "type": "KOL EVM SWAP/TX",
                    "amount_usd": "Whale Activity",
                    "token_name": "ERC-20 Asset",
                    "ca": tx_info.get("to") or wallet_address
                }
        return None
    except Exception as e:
        return None

def main():
    print("Bot Alert KOL & Smart Wallet Berjalan...")
    while True:
        for address, name in WATCHED_WALLETS_SOL.items():
            tx = check_solana_activity(address)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("SOLANA", name, address, tx)
            time.sleep(2)

        for address, name in WATCHED_WALLETS_EVM.items():
            tx = check_evm_activity(address)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("EVM", name, address, tx)
            time.sleep(2)

        time.sleep(30)

if __name__ == "__main__":
    main()
