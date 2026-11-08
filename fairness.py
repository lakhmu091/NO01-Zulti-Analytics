import hashlib, os, re, subprocess
import requests

def verify_server_seed(server_seed, published_hash):
    calculated = hashlib.sha256(server_seed.encode("utf-8")).hexdigest()
    expected = published_hash.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Published hash must be a 64-character SHA-256 hex string.")
    return calculated == expected, calculated

def fetch_ethereum_block_hash(block_number, rpc_url=None):
    rpc_url = rpc_url or os.getenv("ETHEREUM_RPC_URL")
    if not rpc_url:
        raise RuntimeError("Set ETHEREUM_RPC_URL in Streamlit secrets or environment.")
    number = int(block_number)
    if number < 0:
        raise ValueError("Block number cannot be negative.")
    response = requests.post(rpc_url, json={"jsonrpc":"2.0","method":"eth_getBlockByNumber",
        "params":[hex(number),False],"id":1}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    block = payload.get("result")
    if not block or not block.get("hash"):
        raise RuntimeError("Block not found or RPC returned no hash.")
    return block["hash"]

def verify_zulti_result(server_seed, ethereum_block_hash, actual_numbers, max_selectable_number=45, selectable_numbers_count=6):
    if not ethereum_block_hash:
        return {"status":"UNAVAILABLE","message":"Ethereum block hash is required."}
    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", ethereum_block_hash.strip()):
        raise ValueError("Block hash must be 0x followed by 64 hex characters.")
    if not (1 <= selectable_numbers_count <= max_selectable_number <= 1000):
        raise ValueError("Invalid draw range/count.")
    env = os.environ.copy()
    env.update({"NO01_SERVER_SEED":server_seed,"NO01_BLOCK_HASH":ethereum_block_hash.strip(),
                "NO01_MAX":str(max_selectable_number),"NO01_COUNT":str(selectable_numbers_count)})
    script = '''
server_seed = System.get_env("NO01_SERVER_SEED")
block_hash = System.get_env("NO01_BLOCK_HASH")
max_n = String.to_integer(System.get_env("NO01_MAX"))
count = String.to_integer(System.get_env("NO01_COUNT"))
:rand.seed(:default, :erlang.phash2([server_seed, block_hash]))
numbers = 1..max_n |> Enum.to_list() |> Enum.shuffle() |> Enum.take(count) |> Enum.sort()
IO.puts(Enum.join(numbers, ","))
'''
    try:
        proc = subprocess.run(["elixir","-e",script], env=env, capture_output=True,
                              text=True, timeout=30, check=True)
    except FileNotFoundError:
        return {"status":"UNAVAILABLE","message":"Exact draw reproduction requires Elixir/Erlang OTP. This runtime has no Elixir executable; SHA-256 commitment verification still works."}
    except subprocess.CalledProcessError as exc:
        return {"status":"UNAVAILABLE","message":"Elixir failed: " + exc.stderr.strip()}
    reproduced = [int(x) for x in proc.stdout.strip().split(",") if x]
    actual = sorted(int(x) for x in actual_numbers)
    if len(actual) != selectable_numbers_count or len(set(actual)) != len(actual):
        raise ValueError("Published result has incorrect count or duplicate numbers.")
    ok = reproduced == actual
    return {"status":"MATCH" if ok else "MISMATCH", "numbers":reproduced,
            "message":"Reproduced numbers match." if ok else "Reproduced numbers do not match."}
