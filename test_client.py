import asyncio
from macrobot.fred_client import _get


async def main():
    data = await _get("series/search", {
        "search_text": "consumer price index",
        "limit": 2,
    })
    for s in data["seriess"]:
        print(f"\n--- {s['id']} ---")
        for k, v in s.items():
            print(f"  {k}: {str(v)[:80]}")


asyncio.run(main())