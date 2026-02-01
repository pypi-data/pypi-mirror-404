import eth_lake
import asyncio
import os

RPC_URL = "https://eth.llamarpc.com" 

async def main():
    # --- testing connecting to rpc ---
    # print(f"Connecting to {RPC_URL}...")
    # try:
    #     block_num = await eth_lake.get_latest_block(RPC_URL)
    #     print(f"[SUCCESS!]Latest Block Number: {block_num}")
    # except Exception as e:
    #     print(f"ERROR: {e}")
    
    # --- testing fetch block arrow ---
    # print(f"Fetching block 19000000...")
    # try:
    #     block_hash = await eth_lake.fetch_block_arrow(RPC_URL, 19000000, "block_19000000.parquet")
    #     print(f"[SUCCESS!] Block Hash: {block_hash}")
    # except Exception as e:
    #     print(f"ERROR: {e}")
    
    # --- testing extract range ---
    print(f"Extracting blocks 19000000 to 19000010...")
    await eth_lake.extract_range(RPC_URL, 19000000, 19000010, ".", 5)
    return


if __name__ == "__main__":
    asyncio.run(main())