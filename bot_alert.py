import time
import requests

# --- KONFIGURASI BOT & TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8925455594:AAHzlQM2bOjAwCiDvu2DhpT7vj8tacgiKE4"
TELEGRAM_GROUP_CHAT_ID = "-1002362131585"

# --- API KEY & FILTER ---
ETHERSCAN_API_KEY = "4TG86FPSB6Y3FS4ZJ7BZHGSW3KQ"
MIN_USD_THRESHOLD = 500.0  # Minimal pembelian dalam USD agar masuk notifikasi

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

def get_crypto_prices():
    """Mengambil harga terkini SOL dan ETH dalam USD dari CoinGecko Public API"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,ethereum&vs_currencies=usd"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            sol_price = data.get("solana", {}).get("usd", 100.0)
            eth_price = data.get("ethereum", {}).get("usd", 2500.0)
            return sol_price, eth_price
    except Exception:
        pass
    return 100.0, 2500.0  # Fallback harga default jika API limit

def send_telegram_alert(network, name, address, tx):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    message = (
        f"🚨 *SMART WALLET BUY ALERT ({network})* 🚨\n\n"
        f"👤 *Target:* {name}\n"
        f"👛 *Wallet:* `{address[:6]}...{address[-4:]}`\n"
        f"🟢 *Action:* {tx['type']} \n"
        f"💵 *Spent:* `${tx['usd_value']:,.2f} USD`\n"
        f"🪙 *Token CA:*\n`{tx['ca']}`"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📊 DexScreener", "url": f"https://dexscreener.com/solana/{tx['ca']}" if network == "SOLANA" else f"https://dexscreener.com/search?q={tx['ca']}"},
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

def check_solana_activity(wallet_address, sol_price):
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
                
                tx_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [tx_hash, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                }
                tx_resp = requests.post(rpc_url, json=tx_payload, timeout=10)
                token_mint = wallet_address
                spent_usd = 0.0
                
                if tx_resp.status_code == 200:
                    result_data = tx_resp.json().get("result")
                    if result_data and "meta" in result_data:
                        meta = result_data["meta"]
                        
                        account_keys = result_data["transaction"]["message"]["accountKeys"]
                        pre_balances = meta.get("preBalances", [])
                        post_balances = meta.get("postBalances", [])
                        
                        for idx, acc in enumerate(account_keys):
                            pubkey = acc.get("pubkey") if isinstance(acc, dict) else acc
                            if pubkey == wallet_address and idx < len(pre_balances) and idx < len(post_balances):
                                diff_lamports = pre_balances[idx] - post_balances[idx]
                                if diff_lamports > 0:
                                    spent_sol = diff_lamports / 1e9
                                    spent_usd = spent_sol * sol_price
                                break

                        post_token_balances = meta.get("postTokenBalances", [])
                        for pb in post_token_balances:
                            if pb.get("owner") == wallet_address:
                                mint = pb.get("mint")
                                if mint and mint != "So11111111121111111111111111111111111111112":
                                    token_mint = mint
                                    break
                        if token_mint == wallet_address and post_token_balances:
                            for pb in post_token_balances:
                                mint = pb.get("mint")
                                if mint and mint != "So11111111121111111111111111111111111111112":
                                    token_mint = mint
                                    break

                # Filter berdasarkan minimal USD threshold
                if spent_usd >= MIN_USD_THRESHOLD:
                    return {
                        "hash": tx_hash,
                        "type": "SOLANA SWAP",
                        "usd_value": spent_usd,
                        "ca": token_mint
                    }
        return None
    except Exception:
        return None

def check_evm_activity(wallet_address, eth_price):
    try:
        url = f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&page=1&offset=1&sort=desc&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and len(data.get("result", [])) > 0:
                tx_info = data["result"][0]
                tx_hash = tx_info.get("hash")
                to_address = tx_info.get("to") or wallet_address
                
                value_wei = int(tx_info.get("value", "0"))
                value_eth = value_wei / 1e18
                spent_usd = value_eth * eth_price
                
                # Filter berdasarkan minimal USD threshold
                if spent_usd >= MIN_USD_THRESHOLD:
                    return {
                        "hash": tx_hash,
                        "type": "EVM TX / SWAP",
                        "usd_value": spent_usd,
                        "ca": to_address
                    }
        return None
    except Exception:
        return None

def main():
    print("Bot Alert V7 Berjalan (Dengan Filter Minimal $500 USD & Format USD)...")
    while True:
        # Ambil harga konversi terbaru setiap siklus pengecekan
        sol_price, eth_price = get_crypto_prices()

        for address, name in WATCHED_WALLETS_SOL.items():
            tx = check_solana_activity(address, sol_price)
            if tx and tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("SOLANA", name, address, tx)
            time.sleep(3)

        for address, name in WATCHED_WALLETS_EVM.items():
            tx = check_evm_activity(address, eth_price)
            if tx and tx["hash"] != last_tv_cache.get(address) if 'last_tv_cache' in globals() else tx["hash"] != last_tx_cache.get(address):
                last_tx_cache[address] = tx["hash"]
                send_telegram_alert("EVM", name, address, tx)
            time.sleep(3)

        time.sleep(20)

if __name__ == "__main__":
    main()
