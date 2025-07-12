#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API удаления задач
"""

import asyncio
import json
import sys
from pathlib import Path

# Добавляем корневую папку в путь для импортов
sys.path.append(str(Path(__file__).parent))

from printer.add_to_print import PrintQueueManager

async def test_delete_api():
    """Тестируем API удаления задач"""
    print("🧪 Тестирование API удаления задач...")
    
    # Создаем менеджер очереди
    queue_manager = PrintQueueManager()
    await queue_manager.connect()
    
    # Добавляем тестовую задачу
    order_data = {
        "id": "test_order_delete",
        "article": "test-article-delete"
    }
    
    print("📋 Добавляем тестовую задачу...")
    task_id = await queue_manager.add_to_queue("for_print/test-article-001/ПЕЧАТЬ.png", order_data)
    print(f"✅ Задача добавлена: {task_id}")
    
    # Проверяем, что задача в очереди
    tasks = await queue_manager.redis.zrange("print_queue", 0, -1)
    print(f"📋 Задач в очереди: {len(tasks)}")
    
    # Тестируем удаление
    print(f"🗑️ Удаляем задачу: {task_id}")
    removed = await queue_manager.remove_task(task_id)
    print(f"✅ Результат удаления: {removed}")
    
    # Проверяем, что задача удалена
    tasks_after = await queue_manager.redis.zrange("print_queue", 0, -1)
    print(f"📋 Задач в очереди после удаления: {len(tasks_after)}")
    
    if len(tasks_after) == 0:
        print("✅ Тест пройден успешно!")
    else:
        print("❌ Тест не пройден - задача не удалена")

if __name__ == "__main__":
    asyncio.run(test_delete_api()) 