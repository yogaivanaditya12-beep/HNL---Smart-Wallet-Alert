import time
import requests
from datetime import datetime
import json

# --- KONFIGURASI BOT & TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8925455594:AAHzlQM2bOjAwCiDvu2DhpT7vj8tacgiKE4"
TELEGRAM_GROUP_CHAT_ID = "-1002362131585"

# --- API KEY (Pastikan ini KEY yang valid) ---
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
    "0x13a78895e2da9f3E373463EAF943a97f4432781A": "Robinhood Whale 1",
    "0x9596dc4D400466Aafeec570E6FE1A73A131fE88a": "Robinhood Whale 2",
    "0x0BD25AAF269cB40d023bE6c80Ab5c8cD08746935": "Robinhood Whale 3",
    "0x16922be511C09fa86acEc67933Fc75568aA7a068": "Robinhood Whale 4",
    "0xAA979e10a3eA1a7A0Ba2f18C6348A73b170a1739": "Robinhood Whale 5",
    "0x9Aa84a6e9c6C6CB62466196E4F364c9ABDf47b0E": "Robinhood Whale 6",
    "0x942B41D990133D8d9989bf3Bb2F89F9aa1d127Fd": "Robinhood Whale 7",
    "0x74fabbd2e02557dD31c1f7AEf193f95197C5c32C": "Robinhood Whale 8",
    "0xEc4b366a0D29853bB36dB07F6c3229ead264Ac02": "Robinhood Whale 9",
    "0x4346169036c8d32C422dF027E5f46e55b489D2ee": "Robinhood Whale 10",
    "0x4c38ac78BFddA318BD6f15312B34585b0cA72D07": "Robinhood Whale 11",
    "0x194d98d18113bDD5720A0a89FE2F98C75ECe7344": "Robinhood Whale 12",
    "0xDd509c9F91F66A18802Ef5b3d54c73B62EA1Ca08": "Robinhood Whale 13",
    "0x4344e42254F0D77a41749BE2B0534571051BdC35": "Robinhood Whale 14",
    "0x39076B6D85ce5dE530a76Fc0f10958cDA7440A63": "Robinhood Whale 15",
    "0xF07CEb21bA7abc6e348E8b2ADA9A664b0714738f": "Robinhood Whale 16",
    "0x218D0Bc869A0DBe8978A985De25D5c5e71F084AC": "Robinhood Whale 17",
    "0x736841752C5380187Ba8a520ab4b60347F311200": "Robinhood Whale 18",
    "0x6f94E1e558d46b1AE95feF5E323B2d792ab7B2Ee": "Robinhood Whale 19",
    "0x6099ff02F63C69162175249c2700c84C0a94DAfa": "Robinhood Whale 20",
    "0xf9b56F4Ce537b0E63a70E1fb20675888b4a01b0E": "Robinhood Whale 21",
    "0x4337021D22Bcd0775a0Fd1B4A6665051DC15d995": "Robinhood Whale 22",
    "0x4337002C5702CE424Cb62A56CA038e31e1D4A93d": "Robinhood Whale 23",
    "0x8BfE79ea33aB2c681A6b51c3793452fc95019216": "Robinhood Whale 24",
    "0x22669AFc9c5C2149768c236cd10a8AB47F2774f3": "Robinhood Whale 25",
    "0x4337050608D02173feea2E27bA65a1AF0f948538": "Robinhood Whale 26",
    "0x0095EEc7043fFD8b0429b8eE726B93a93372C115": "Robinhood Whale 27",
    "0x43370351c9a297bF8377Ca1E46576401a9Ac4bBa": "Robinhood Whale 28",
    "0x4337031ADE3a53D10121f350369907076b6d32A4": "Robinhood Whale 29",
    "0x433705768549b21d1e681fE454A7D2ff26A22E1C": "Robinhood Whale 30",
    "0x43370250bfc02C7F085cB105558DA41E9CDB2D79": "Robinhood Whale 31",
    "0x4337053498BF3De9BaB4D55a345F727DBa05d6aF": "Robinhood Whale 32",
    "0x4337020f43D3d7d2F5E4160397EfeA49AEfa5E7D": "Robinhood Whale 33",
    "0x433702873E33D4846d399A75Aaf96eaCf181D0b2": "Robinhood Whale 34",
    "0x43370108f30Ee5Ed54A9565F37af3BE8502903f5": "Robinhood Whale 35",
    "0x4337004ec9c1417F1c7a26EBD4B4fbed6ACf9E5d": "Robinhood Whale 36",
    "0x43370460D26b10de805D4CdfE4d331aDb7219fFe": "Robinhood Whale 37",
    "0x433702256B464248DcbE403C1334757BE4eD9F26": "Robinhood Whale 38",
    "0x4337038429B76948Ee97EB2d8115513277c3abf5": "Robinhood Whale 39",
}

# Stablecoins yang diabaikan (USDC, USDT, wSOL)
IGNORE_TOKENS = [
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", # USDC Solana
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", # USDT Solana
    "So11111111121111111111111111111111111111112", # wSOL
]

seen_tokens_cache = {}

def log_terminal(message):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] {message}")

def send_telegram_alert(network, name, address, tx):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = (
        f"🚨 *NEW TOKEN DETECTED ({network})* 🚨\n\n"
        f"👤 *Target:* {name}\n"
        f"👛 *Wallet:* `{address[:6]}...{address[-4:]}`\n"
        f"🟢 *Action:* {tx['type']}\n"
        f"🪙 *Token/CA:*\n`{tx['ca']}`"
    )
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "📊 DexScreener", "url": f"https://dexscreener.com/solana/{tx['ca']}" if network == "SOLANA" else f"https://dexscreener.com/search?q={tx['ca']}"},
                {"text": "🔍 Explorer", "url": f"https://solscan.io/token/{tx['ca']}" if network == "SOLANA" else f"https://etherscan.io/token/{tx['ca']}"}
            ]
        ]
    }

    try:
        requests.post(url, json={"chat_id": TELEGRAM_GROUP_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": reply_markup}, timeout=15)
        log_terminal(f"✅ ALERT SENT: {name} ({network}) mendeteksi token baru!")
    except Exception as e:
        log_terminal(f"❌ Gagal kirim Telegram: {e}")

def is_token_new_for_wallet(wallet_address, token_ca):
    if wallet_address not in seen_tokens_cache:
        seen_tokens_cache[wallet_address] = set()
    
    if token_ca in seen_tokens_cache[wallet_address]:
        return False
    
    seen_tokens_cache[wallet_address].add(token_ca)
    return True

# --- FUNGSI SOLANA ---
def check_solana_activity(wallet_address, name):
    try:
        rpc_url = "https://api.mainnet-beta.solana.com"
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress", "params": [wallet_address, {"limit": 5}]}
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(rpc_url, json=payload, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    break 
                else:
                    log_terminal(f"SOLANA API Error (Attempt {attempt+1}/{max_retries}): {response.status_code}")
                    time.sleep(3)
            except Exception as e:
                log_terminal(f"SOLANA Connection Error (Attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(3)
        else:
            log_terminal(f"❌ {name}: Gagal mendapatkan signature setelah retry.")
            return None
        
        if "result" in data and len(data["result"]) > 0:
            for sig_info in data["result"][:2]:
                tx_hash = sig_info.get("signature")
                tx_payload = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [tx_hash, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]}
                
                try:
                    tx_resp = requests.post(rpc_url, json=tx_payload, timeout=15)
                    if tx_resp.status_code == 200:
                        result_data = tx_resp.json().get("result")
                        if result_data and "meta" in result_data:
                            meta = result_data["meta"]
                            if meta.get("postTokenBalances"):
                                for pb in meta.get("postTokenBalances", []):
                                    if pb.get("owner") == wallet_address:
                                        mint = pb.get("mint")
                                        ui_amount = pb.get("uiTokenAmount", {})
                                        decimals = ui_amount.get("decimals", 0)
                                        
                                        if mint and mint not in IGNORE_TOKENS and decimals > 0:
                                            if is_token_new_for_wallet(wallet_address, mint):
                                                return {"type": "NEW SOLANA TOKEN", "ca": mint}
                except Exception as e:
                    log_terminal(f"❌ Gagal mendetailkan transaksi SOL {tx_hash}: {e}")

        return None
    except Exception as e:
        log_terminal(f"❌ Fatal Error di check_solana_activity {name}: {e}")
        return None

# --- FUNGSI EVM ---
def check_evm_activity(wallet_address, name):
    try:
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&page=1&offset=5&sort=desc&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and len(data.get("result", [])) > 0:
                for tx_info in data["result"][:3]:
                    if tx_info.get("to", "").lower() == wallet_address.lower():
                        token_contract = tx_info.get("contractAddress")
                        token_symbol = tx_info.get("tokenSymbol", "TOKEN")
                        
                        if is_token_new_for_wallet(wallet_address, token_contract):
                            return {"type": f"NEW EVM TOKEN ({token_symbol})", "ca": token_contract}
        elif response.status_code == 429:
             log_terminal(f"❌ {name}: Etherscan Rate Limit 429. Jeda terlalu singkat.")
        return None
    except Exception as e:
        log_terminal(f"❌ Fatal Error di check_evm_activity {name}: {e}")
        return None

def main():
    log_terminal(f"Memulai Ulang Bot Smart Wallet (Total EVM: {len(WATCHED_WALLETS_EVM)} Wallet)...")
    while True:
        # --- BLOK SOLANA ---
        log_terminal("--- Memulai Pemindaian Solana ---")
        for address, name in WATCHED_WALLETS_SOL.items():
            log_terminal(f"Memindai {name}...")
            tx = check_solana_activity(address, name)
            if tx:
                send_telegram_alert("SOLANA", name, address, tx)
            time.sleep(4)

        # --- BLOK EVM ---
        log_terminal("--- Memulai Pemindaian EVM (Etherscan) ---")
        for address, name in WATCHED_WALLETS_EVM.items():
            log_terminal(f"Memindai {name}...")
            tx = check_evm_activity(address, name)
            if tx:
                send_telegram_alert("EVM", name, address, tx)
            # Jeda 3.5 detik sangat penting untuk menghindari Error 429 di Etherscan Free Tier
            time.sleep(3.5)

        log_terminal("Siklus selesai. Jeda 30 detik...")
        time.sleep(30)

if __name__ == "__main__":
    main()
