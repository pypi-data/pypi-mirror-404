# BinSolver Python SDK

Official Python SDK for the [BinSolver API](https://binsolver.com).

## Installation

```bash
pip install binsolver
```

## Usage

```python
from binsolver import BinSolver, PackRequest, Item, Bin

client = BinSolver(api_key="your-api-key")

# Check API health
if client.health():
    print("API is healthy")

# Pack items
try:
    response = client.pack(
        PackRequest(
            objective="minBins",
            items=[
                Item(id="item-1", w=5, h=5, d=5, quantity=12)
            ],
            bins=[
                Bin(id="box-small", w=10, h=10, d: 10, quantity=10),
                Bin(id="box-large", w=20, h: 20, d: 20, quantity=5)
            ]
        )
    )

    print(f"Placed {response.stats.placed} items in {response.stats.bins_used} bins.")

    for bin_result in response.bins:
        print(f"Bin {bin_result.bin_id}: {len(bin_result.placements)} items")

except Exception as e:
    print(f"Packing failed: {e}")
```

## Features

- **Fully Typed:** Pydantic models for request and response validation.
- **Modern:** Uses `httpx` for efficient HTTP requests.
- **Easy to Use:** Pythonic interface for the BinSolver API.

## License

MIT
