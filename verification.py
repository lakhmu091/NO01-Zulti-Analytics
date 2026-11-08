import hashlib
import requests

def verify_server_seed(server_seed, published_hash):
    computed = hashlib.sha256(server_seed.encode("utf-8")).hexdigest()
    return computed.lower() == published_hash.strip().lower(), computed

def fetch_ethereum_block_hash(block_number, rpc_url="https://cloudflare-eth.com"):
    payload = {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":[hex(int(block_number)), False],"id":1}
    response = requests.post(rpc_url, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data["error"].get("message", "Ethereum RPC error"))
    result = data.get("result")
    if not result or not result.get("hash"):
        raise ValueError("Block not found or RPC returned no hash.")
    return result["hash"]
