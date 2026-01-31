import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from binsolver import ApiError, Bin, BinSolver, Item, PackRequest


def main():
    api_key = os.getenv("BINSOLVER_API_KEY", "demo-key")

    client = BinSolver(api_key=api_key)

    try:
        if client.health():
            print("API is healthy")
        else:
            print("API is unhealthy or unreachable")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    request = PackRequest(
        objective="minBins",
        items=[
            Item(id="item-1", w=50, h=50, d=50, quantity=2),
            Item(id="item-2", w=20, h=20, d=20, quantity=5),
        ],
        bins=[Bin(id="standard-box", w=100, h=100, d=100, quantity=1)],
    )

    # 3. Pack
    try:
        print("\nPacking items...")
        response = client.pack(request)

        print(f"Placed: {response.stats.placed}/{response.stats.items}")
        print(f"Bins Used: {response.stats.bins_used}")

        for b in response.bins:
            print(
                f"  Bin {b.bin_id} ({b.template_id}): {len(b.placements)} items, Util: {b.utilization:.1%}"
            )

    except ApiError as e:
        print(f"API Error: {e.message}")
    except Exception as e:
        print(f"Unexpected Error: {e}")


if __name__ == "__main__":
    main()
