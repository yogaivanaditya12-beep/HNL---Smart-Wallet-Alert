def check_solana_activity(wallet_address):
    try:
        rpc_url = "https://api.mainnet-beta.solana.com"
        # Perlebar batas pencarian menjadi 3 transaksi terakhir (bukan cuma 1)
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSignaturesForAddress", "params": [wallet_address, {"limit": 3}]}
        response = requests.post(rpc_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data and len(data["result"]) > 0:
                # Cek 3 transaksi terakhir secara berurutan
                for sig_info in data["result"]:
                    tx_hash = sig_info.get("signature")
                    tx_payload = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [tx_hash, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]}
                    tx_resp = requests.post(rpc_url, json=tx_payload, timeout=10)
                    
                    if tx_resp.status_code == 200 and tx_resp.json().get("result"):
                        meta = tx_resp.json()["result"]["meta"]
                        
                        for pb in meta.get("postTokenBalances", []):
                            if pb.get("owner") == wallet_address:
                                mint = pb.get("mint")
                                decimals = pb.get("uiTokenAmount", {}).get("decimals", 0)
                                
                                # Jika itu koin asli (desimal > 0) dan bukan stablecoin
                                if mint and mint not in IGNORE_TOKENS and decimals > 0:
                                    if is_token_new_for_wallet(wallet_address, mint):
                                        return {"type": "NEW SOLANA TOKEN", "ca": mint}
        return None
    except Exception:
        return None


def check_evm_activity(wallet_address):
    try:
        # Perlebar batas pencarian menjadi 5 transaksi terakhir agar tidak ada koin yang tertumpuk
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet_address}&page=1&offset=5&sort=desc&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and len(data.get("result", [])) > 0:
                # Cek 5 transaksi terakhir dari yang paling baru
                for tx_info in data["result"]:
                    # Pastikan transaksi adalah token IN (masuk ke dompet target)
                    if tx_info.get("to", "").lower() == wallet_address.lower():
                        token_contract = tx_info.get("contractAddress")
                        token_symbol = tx_info.get("tokenSymbol", "TOKEN")
                        
                        # Cek apakah contract address (CA) ini baru pertama kali dilihat oleh dompet ini
                        if is_token_new_for_wallet(wallet_address, token_contract):
                            return {"type": f"NEW EVM TOKEN ({token_symbol})", "ca": token_contract}
        return None
    except Exception:
        return None
