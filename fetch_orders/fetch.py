import asyncio
import aiohttp
from fetch_orders.methods import get_json_response

async def fetch_orders():
    """
    Fetch orders from the API
    """
    url = "https://marketplace-api-sandbox.wildberries.ru/api/v3/orders/new"
    try:
        response = await get_json_response(url)
        return response
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please create a .env file with your Wildberries API token:")
        print("WB_TOKEN=your_actual_token_here")
        return None
    except aiohttp.ClientError as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching orders: {e}")
        return None

async def main():
    response = await fetch_orders()
    print(response)

if __name__ == "__main__":
    asyncio.run(main())