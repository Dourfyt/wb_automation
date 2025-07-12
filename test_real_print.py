#!/usr/bin/env python3
"""
Тестовый скрипт для проверки печати на реальных принтерах из рабочей группы
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

# Добавляем корневую папку в путь для импортов
import sys
sys.path.append(str(Path(__file__).parent))

from printer.add_to_print import PrintQueueManager

async def test_real_print():
    """Тестируем печать на реальных принтерах"""
    print("🧪 Тестирование печати на реальных принтерах...")
    
    # Создаем менеджер очереди
    queue_manager = PrintQueueManager()
    await queue_manager.connect()
    
    # Добавляем тестовую задачу
    order_data = {
        "id": "test_order_001",
        "article": "test-article-001"
    }
    
    print(f"📋 Добавляем тестовую задачу для печати")
    task_id = await queue_manager.add_to_queue("for_print/test-article-001/ПЕЧАТЬ.png", order_data)
    
    # Проверяем, что задача добавлена
    if queue_manager.redis:
        tasks = await queue_manager.redis.zrange(queue_manager.queue_name, 0, -1)
        print(f"📋 Задач в очереди: {len(tasks)}")
    else:
        print("❌ Нет подключения к Redis")
    
    # Запускаем процессор печати
    print("🚀 Запускаем процессор печати...")
    from printer.print_processor import PrintProcessor
    
    processor = PrintProcessor()
    
    # Запускаем обработку на короткое время
    try:
        await asyncio.wait_for(processor.start_processing(check_interval=2), timeout=10)
    except asyncio.TimeoutError:
        print("⏰ Тест завершен по таймауту")
    finally:
        processor.stop()
    
    # Проверяем статус задачи
    if queue_manager.redis:
        final_tasks = await queue_manager.redis.zrange(queue_manager.queue_name, 0, -1)
        print(f"📋 Задач в очереди после обработки: {len(final_tasks)}")
    else:
        print("❌ Нет подключения к Redis")
    
    # Очищаем тестовую задачу
    await queue_manager.remove_task(task_id)
    print("🧹 Тестовая задача удалена")

if __name__ == "__main__":
    asyncio.run(test_real_print()) 