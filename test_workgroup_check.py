#!/usr/bin/env python3
"""
Тестовый скрипт для проверки принтеров в рабочей группе
"""

import asyncio
from printer.printer_manager import PrinterManager

async def check_workgroup():
    """Проверяем принтеры в рабочей группе"""
    print("🔍 Проверка принтеров в рабочей группе...")
    
    manager = PrinterManager()
    
    # Получаем принтеры из рабочей группы
    workgroup_printers = await manager.get_workgroup_printers("wb_print_group")
    
    print(f"📋 Принтеров в рабочей группе: {len(workgroup_printers)}")
    
    if workgroup_printers:
        for printer in workgroup_printers:
            print(f"  - {printer['name']} ({printer['type']}) - {printer['status']}")
    else:
        print("⚠️ Рабочая группа пуста")
        
        # Показываем системные принтеры
        print("\n📋 Системные принтеры:")
        system_printers = await manager.get_system_printers()
        for printer in system_printers:
            print(f"  - {printer['name']} ({printer['type']}) - {printer['status']}")

if __name__ == "__main__":
    asyncio.run(check_workgroup()) 