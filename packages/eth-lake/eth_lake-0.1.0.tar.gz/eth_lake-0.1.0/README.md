# Eth-Lake

A Python library for extracting Ethereum blockchain data directly into Parquet.

## Installation

```bash
pip install eth-lake
```

## Usage

### Bulk Extraction (Pipeline)

Fetch a range of blocks concurrently and write them as Parquet files to a specific directory.

```python
import eth_lake
import asyncio

RPC_URL = "https://eth.llamarpc.com"

async def main():
    # Extract blocks 18M to 18M+50 with 20 concurrent workers
    result = await eth_lake.extract_range(
        rpc_url=RPC_URL,
        start=18000000,
        end=18000050,
        output_dir="./data",
        concurrency=20
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Single Block Fetch

Fetch a single block for inspection or debugging.

```python
file_path = await eth_lake.fetch_block_arrow(
    rpc_url=RPC_URL,
    block_number=19000000,
    output_path="block_19000000.parquet"
)
```

### Utilities

Check the current chain height before starting a job.

```python
tip = await eth_lake.get_latest_block(RPC_URL)
```

## Output

The library produces standard Parquet files containing the following schema:
* `number` (UInt64)
* `hash` (Utf8)
* `parent_hash` (Utf8)

## License

MIT License