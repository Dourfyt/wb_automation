import asyncio
from typing import Dict, Any

async def mock_get_new_orders() -> Dict[str, Any]:
    """
    Мок функция для получения новых заказов
    Имитирует ответ от https://marketplace-api.wildberries.ru/api/v3/orders/new
    """
    return {
        "orders": [
            {
                "id": 12345,
                "orderUid": "test_order_123",
                "article": "test-article-001",
                "price": 1500,
                "salePrice": 1800,
                "deliveryType": "fbs",
                "createdAt": "2024-01-15T10:30:00Z",
                "warehouseId": 123,
                "nmId": 456789,
                "chrtId": 987654,
                "skus": ["1234567890123"],
                "comment": "Тестовый заказ",
                "address": {
                    "fullAddress": "Москва, ул. Тестовая, д. 1, кв. 1",
                    "longitude": 37.123456,
                    "latitude": 55.123456
                },
                "offices": ["Москва"],
                "isZeroOrder": False,
                "cargoType": 1
            }
        ]
    }

# Для тестирования
if __name__ == "__main__":
    result = asyncio.run(mock_get_new_orders())
    print(result)
