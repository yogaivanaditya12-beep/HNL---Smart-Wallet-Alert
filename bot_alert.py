import time
import requests

# --- KONFIGURASI BOT & TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8925455594:AAHzlQM2bOjAwCiDvu2DhpT7vj8tacgiKE4"
TELEGRAM_GROUP_CHAT_ID = "-1002362131585"

# --- API KEY ---
ETHERSCAN_API_KEY = "4TG86FPSB6Y3FS4ZJ7BZHGSW3KQ"

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
        f"💰 *Info:* `{tx['amount_usd']}`\n"
        f"🪙 *Asset / Program:* {tx['token_name']}\n"
        f"📋 *Token / Target CA:*\n`{tx['ca']}`"
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
                
                # Ambil detail transaksi untuk melihat interaksi program/token
                tx_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [tx_hash, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                }
                tx_resp = requests.post(rpc_url, json=tx_payload, timeout=10)
                token_ca = wallet_address
                if tx_resp.status_code == 200:
                    tx_data = tx_resp.json().get("result")
                    if tx_data and "transaction" in tx_data:
                        account_keys = tx_data["transaction"]["message"]["accountKeys"]
                        # Cari akun terakhir atau akun yang berinteraksi sebagai contract/token mint
                        if len(account_keys) > 2:
                            token_ca = account_keys[-1].get("pubkey", wallet_address)

                return {
                    "hash": tx_hash,
                    "type": "SOLANA SWAP DETECTED",
                    "amount_usd": "On-Chain Swap",
                    "token_name": "Target Token / Pool",
                    "ca": token_ca
                }
        return None
    except Exception as e:
        return None

def check_evm_activity(wallet_address):
    try:
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&page=1&offset=1&sort=desc&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and len(data.get("result", [])) > 0:
                tx_info = data["result"][0]
                token_symbol = tx_info.get("tokenSymbol", "ERC-20")
                token_contract = tx_info.get("contractAddress", wallet_address)
                return {
                    "hash": tx_info.get("hash"),
                    "type": f"EVM TOKEN TRANSFER ({token_symbol})",
                    "amount_usd": f"Value: {tx_info.get('value', '0')[:6]}...",
                    "token_name": token_symbol,
                    "ca": token_contract
                }
        return None
    except Exception as e:
        return None

def main():
    print("Bot Alert V3 Berjalan (Advanced Token Parsing)...")
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
