import asyncio
from fetch_orders.fetch import fetch_orders

async def main():
    response = await fetch_orders()
    print(response)

if __name__ == "__main__":
    asyncio.run(main())