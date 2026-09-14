import time
import requests
from datetime import datetime

# --- KONFIGURASI BOT & TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8925455594:AAHzlQM2bOjAwCiDvu2DhpT7vj8tacgiKE4"
TELEGRAM_GROUP_CHAT_ID = "-1002362131585"

# --- API KEY ---
ETHERSCAN_API_KEY = "4TG86FPSB6Y3FS4ZJ7BZHGSW3KQ"

# --- DATABASE SMART WALLET ---
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

# Stablecoins yang diabaikan (USDC, USDT, Wrapped SOL)
IGNORE_TOKENS = [
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", # USDC Solana
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", # USDT Solana
    "So11111111121111111111111111111111111111112", # wSOL
]

last_tx_cache = {}

def log_terminal(message):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] {message}")

def send_telegram_alert(network, name, address, tx):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"🚨 *SMART WALLET BUY ALERT ({network})* 🚨\n\n"
        f"👤 *Target:* {name}\n"
        f"👛 *Wallet:* `{address[:6]}...{address[-4:]}`\n"
        f"🟢 *Action:* {tx['type']}\n"
        f"🪙 *Token/CA:*\n`{tx['ca']}`"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📊 DexScreener", "url": f"https://dexscreener.com/solana/{tx['ca']}" if network == "SOLANA" else f"https://dexscreener.com/search?q={tx['ca']}"},
                {"text": "🔍 Explorer", "url": f"https://solscan.io/tx/{tx['hash']}" if network == "SOLANA" else f"https://etherscan.io/tx/{tx['hash']}"}
            ]
        ]
    }

    try:
        requests.post(url, json={"chat_id": TELEGRAM_GROUP_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": reply_markup}, timeout=10)
        log_terminal(f"✅ ALERT TERKIRIM: {name} ({network}) mendeteksi token baru!")
    except Exception as e:
        log_terminal(f"❌ Gagal kirim Telegram: {e}")

def check_solana_activity(wallet_address):
    try:
        rpc_url = "https://api.mainnet-beta.solana.com"
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress", "params": [wallet_address, {"limit": 1}]}
        response = requests.post(rpc_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and len(data["result"]) > 0:
                tx_hash = data["result"][0].get("signature")
                
                tx_payload = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [tx_hash, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]}
                tx_resp = requests.post(rpc_url, json=tx_payload, timeout=10)
                
                if tx_resp.status_code == 200 and tx_resp.json().get("result"):
                    meta = tx_resp.json()["result"]["meta"]
                    token_mint = None
                    
                    # Mencari CA token apa saja yang berinteraksi/masuk ke wallet (kecuali stablecoin)
                    for pb in meta.get("postTokenBalances", []):
                        if pb.get("owner") == wallet_address:
                            mint = pb.get("mint")
                            if mint and mint not in IGNORE_TOKENS:
                                token_mint = mint
                                break
                    
                    if token_mint:
                        return {"hash": tx_hash, "type": "SOLANA TOKEN ACTIVITY", "ca": token_mint}
        return None
    except Exception:
        return None

def check_evm_activity(wallet_address):
    try:
        # Menggunakan tokentx untuk melacak penerimaan token ERC-20
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&page=1&offset=1&sort=desc&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and len(data.get("result", [])) > 0:
                tx_info = data["result"][0]
                
                # Memastikan transaksi adalah token IN (masuk) ke wallet
                if tx_info.get("to", "").lower() == wallet_address.lower():
                    tx_hash = tx_info.get("hash")
                    token_contract = tx_info.get("contractAddress")
                    token_symbol = tx_info.get("tokenSymbol", "TOKEN")
                    
                    return {"hash": tx_hash, "type": f"EVM BUY ({token_symbol})", "ca": token_contract}
        return None
    except Exception:
        return None

def main():
    log_terminal("Memulai Bot Pelacak Smart Wallet CA (Ringan & Cepat)...")
    while True:
        for address, name in WATCHED_WALLETS_SOL.items():
            log_terminal(f"Memindai {name} (SOL)...")
            tx = check_solana_activity(address)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("SOLANA", name, address, tx)
            time.sleep(2) # Jeda untuk hindari limit RPC

        for address, name in WATCHED_WALLETS_EVM.items():
            log_terminal(f"Memindai {name} (EVM)...")
            tx = check_evm_activity(address)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("EVM", name, address, tx)
            time.sleep(2) # Jeda untuk hindari limit Etherscan

        log_terminal("Siklus selesai. Jeda 15 detik...")
        time.sleep(15)

if __name__ == "__main__":
    main()
