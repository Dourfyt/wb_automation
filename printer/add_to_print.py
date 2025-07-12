import os
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Добавляем корневую папку в путь для импортов
sys.path.append(str(Path(__file__).parent.parent))

from fetch_orders.mocks import mock_get_new_orders

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis не установлен. Установите: pip install redis")

# Импортируем Excel менеджер
from .excel import ExcelReportManager


class PrintQueueManager:
    """Менеджер очереди печати с поддержкой нескольких принтеров"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", excel_filename: str = "print_status_report.xlsx"):
        self.redis_url = redis_url
        self.redis = None
        self.queue_name = "print_queue"
        self.printers_key = "available_printers"
        self.excel_manager = ExcelReportManager(excel_filename)
        
    async def connect(self):
        """Подключение к Redis"""
        if not REDIS_AVAILABLE:
            raise ImportError("Redis не установлен")
        
        self.redis = redis.from_url(self.redis_url)
        await self.redis.ping()
        
    async def add_printer(self, printer_id: str, printer_info: Dict[str, Any]):
        """Добавить принтер в список доступных"""
        if not self.redis:
            await self.connect()
            
        printer_data = {
            "id": printer_id,
            "status": "available",
            "last_activity": datetime.now().isoformat(),
            **printer_info
        }
        
        await self.redis.hset(self.printers_key, printer_id, json.dumps(printer_data))
        
    async def add_to_queue(self, file_path: str, order_data: dict, priority: int = 1) -> str:
        """Добавить задачу в очередь печати"""
        if not self.redis:
            await self.connect()
            
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "file_path": file_path,
            "order_id": order_data.get("id"),
            "article": order_data.get("article"),
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "assigned_printer": None
        }
        
        # Добавляем в очередь с приоритетом (меньше число = выше приоритет)
        await self.redis.zadd(self.queue_name, {json.dumps(task_data): priority})
        
        # Обновляем Excel отчет
        self.excel_manager.update_status(
            str(order_data.get("id")), 
            "В очереди"
        )
        
        return task_id
        
    async def get_next_task(self, printer_id: str) -> Optional[Dict[str, Any]]:
        """Получить следующую задачу для принтера"""
        if not self.redis:
            await self.connect()
            
        # Получаем задачу с наивысшим приоритетом
        tasks = await self.redis.zrange(self.queue_name, 0, 0, withscores=True)
        
        if not tasks:
            return None
            
        task_json, score = tasks[0]
        task_data = json.loads(task_json)
        
        # Помечаем задачу как назначенную
        task_data["assigned_printer"] = printer_id
        task_data["status"] = "printing"
        task_data["assigned_at"] = datetime.now().isoformat()
        
        # Удаляем старую запись и добавляем обновленную
        await self.redis.zrem(self.queue_name, task_json)
        await self.redis.zadd(self.queue_name, {json.dumps(task_data): score})
        
        # Обновляем Excel отчет
        self.excel_manager.update_status(
            str(task_data.get("order_id")), 
            "Печатается", 
            printer_id
        )
        
        return task_data
        
    async def mark_task_completed(self, task_id: str, printer_id: str):
        """Пометить задачу как выполненную"""
        if not self.redis:
            await self.connect()
            
        # Находим задачу в очереди
        tasks = await self.redis.zrange(self.queue_name, 0, -1, withscores=True)
        
        for task_json, score in tasks:
            task_data = json.loads(task_json)
            if task_data["id"] == task_id and task_data["assigned_printer"] == printer_id:
                # Помечаем как выполненную
                task_data["status"] = "completed"
                task_data["completed_at"] = datetime.now().isoformat()
                task_data["completed_by"] = printer_id
                
                # Сохраняем в выполненные задачи
                await self.redis.zadd("completed_tasks", {json.dumps(task_data): score})
                
                # Удаляем из очереди
                await self.redis.zrem(self.queue_name, task_json)
                
                # Обновляем Excel отчет
                self.excel_manager.update_status(
                    str(task_data.get("order_id")), 
                    "Распечатан", 
                    printer_id
                )
                break

    async def remove_task(self, task_id: str) -> bool:
        """Удалить задачу из очереди по task_id"""
        if not self.redis:
            await self.connect()
        tasks = await self.redis.zrange(self.queue_name, 0, -1)
        for task_json in tasks:
            task = json.loads(task_json)
            if task.get("id") == task_id:
                await self.redis.zrem(self.queue_name, task_json)
                return True
        return False

    async def restart_task(self, task_id: str) -> bool:
        """Перезапустить задачу: удалить и добавить обратно со статусом pending и новым id"""
        if not self.redis:
            await self.connect()
        tasks = await self.redis.zrange(self.queue_name, 0, -1, withscores=True)
        for task_json, score in tasks:
            task = json.loads(task_json)
            if task.get("id") == task_id:
                await self.redis.zrem(self.queue_name, task_json)
                import uuid
                task["status"] = "pending"
                task["assigned_printer"] = None
                task["id"] = str(uuid.uuid4())
                await self.redis.zadd(self.queue_name, {json.dumps(task): score})
                return True
        return False


async def add_orders_to_print_queue(redis_url: str = "redis://localhost:6379") -> List[str]:
    """
    Получает новые заказы, находит файлы печати и добавляет их в очередь на печать.
    
    Args:
        redis_url: URL подключения к Redis
        
    Returns:
        List[str]: Список ID задач, добавленных в очередь на печать
    """
    # Получаем новые заказы
    orders_data = await mock_get_new_orders()
    orders = orders_data.get("orders", [])
    
    added_tasks = []
    base_print_path = Path("for_print")
    
    # Инициализируем менеджер очереди
    queue_manager = PrintQueueManager(redis_url)
    
    for order in orders:
        article = order.get("article")
        if not article:
            continue
            
        # Ищем папку с артикулом
        article_folder = base_print_path / article
        if not article_folder.exists():
            print(f"Папка для артикула {article} не найдена: {article_folder}")
            continue
            
        # Ищем файл ПЕЧАТЬ.png
        print_file = article_folder / "ПЕЧАТЬ.png"
        if not print_file.exists():
            print(f"Файл ПЕЧАТЬ.png не найден для артикула {article}: {print_file}")
            continue
            
        # Добавляем файл в очередь на печать
        try:
            task_id = await queue_manager.add_to_queue(str(print_file), order)
            added_tasks.append(task_id)
            print(f"Задача добавлена в очередь на печать: {task_id} для артикула {article}")
        except Exception as e:
            print(f"Ошибка при добавлении файла в очередь: {e}")
    
    return added_tasks


# Функция для демонстрации работы с принтерами
async def setup_printers():
    """Настройка доступных принтеров"""
    queue_manager = PrintQueueManager()
    
    # Добавляем несколько принтеров
    printers = [
        {"name": "Принтер 1", "type": "thermal", "location": "Склад А"},
        {"name": "Принтер 2", "type": "thermal", "location": "Склад Б"},
        {"name": "Принтер 3", "type": "laser", "location": "Офис"}
    ]
    
    for i, printer_info in enumerate(printers, 1):
        await queue_manager.add_printer(f"printer_{i}", printer_info)
        print(f"Добавлен принтер: {printer_info['name']}")


# Для тестирования
if __name__ == "__main__":
    async def main():
        # Настраиваем принтеры
        await setup_printers()
        
        # Добавляем заказы в очередь
        result = await add_orders_to_print_queue()
        print(f"Добавлено задач в очередь: {len(result)}")
        for task_id in result:
            print(f"  - {task_id}")
    
    asyncio.run(main())

