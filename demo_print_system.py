#!/usr/bin/env python3
"""
Демонстрация полного цикла работы системы печати:
1. Добавление заказов в очередь
2. Запуск процессора печати
3. Обработка задач
4. Обновление Excel отчета
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую папку в путь для импортов
# sys.path.append(str(Path(__file__).parent))

from printer.add_to_print import add_orders_to_print_queue, setup_printers
from printer.excel import create_print_status_report
from printer.print_processor import start_print_processor


async def demo_full_cycle():
    """Демонстрация полного цикла работы системы"""
    
    print("🎯 ДЕМОНСТРАЦИЯ СИСТЕМЫ ПЕЧАТИ")
    print("=" * 50)
    
    # Шаг 1: Настройка принтеров
    print("\n1️⃣ Настройка принтеров...")
    await setup_printers()
    
    # Шаг 2: Создание Excel отчета
    print("\n2️⃣ Создание Excel отчета...")
    excel_file = await create_print_status_report()
    print(f"   📊 Отчет создан: {excel_file}")
    
    # Шаг 3: Добавление заказов в очередь
    print("\n3️⃣ Добавление заказов в очередь...")
    task_ids = await add_orders_to_print_queue()
    print(f"   📋 Добавлено задач: {len(task_ids)}")
    for task_id in task_ids:
        print(f"      - {task_id}")
    
    # Шаг 4: Запуск процессора печати
    print("\n4️⃣ Запуск процессора печати...")
    print("   🖨️ Процессор будет обрабатывать задачи каждые 5 секунд")
    print("   ⏹️ Нажмите Ctrl+C для остановки")
    
    try:
        await start_print_processor()
    except KeyboardInterrupt:
        print("\n👋 Демонстрация завершена")
    
    print("\n✅ Система готова к работе!")


async def demo_without_redis():
    """Демонстрация без Redis (только Excel отчет)"""
    
    print("🎯 ДЕМОНСТРАЦИЯ БЕЗ REDIS")
    print("=" * 40)
    
    # Создание Excel отчета
    print("\n1️⃣ Создание Excel отчета...")
    try:
        excel_file = await create_print_status_report()
        print(f"   📊 Отчет создан: {excel_file}")
        print("   🟡 Желтый цвет - не распечатанные артикулы")
        print("   🟢 Зеленый цвет - распечатанные артикулы")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print("\n✅ Демонстрация завершена!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Демонстрация системы печати")
    parser.add_argument(
        "--no-redis", 
        action="store_true", 
        help="Запустить демонстрацию без Redis (только Excel)"
    )
    
    args = parser.parse_args()
    
    if args.no_redis:
        asyncio.run(demo_without_redis())
    else:
        asyncio.run(demo_full_cycle()) 