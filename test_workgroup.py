#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функциональности рабочей группы принтеров
"""

import asyncio
import json
import aiohttp
from printer.printer_manager import PrinterManager

async def test_workgroup_functionality():
    """Тестирование функциональности рабочей группы"""
    print("🧪 Тестирование функциональности рабочей группы принтеров...")
    
    # Создаем менеджер принтеров
    printer_manager = PrinterManager()
    
    # Получаем системные принтеры
    print("\n📋 Получение системных принтеров...")
    system_printers = await printer_manager.get_system_printers()
    print(f"Найдено принтеров: {len(system_printers)}")
    
    for printer in system_printers:
        print(f"  - {printer['name']} ({printer['type']})")
    
    if not system_printers:
        print("❌ Принтеры не найдены в системе")
        return
    
    # Выбираем первый принтер для тестирования
    test_printer = system_printers[0]['name']
    print(f"\n🎯 Тестируем с принтером: {test_printer}")
    
    # Тестируем добавление в рабочую группу
    print("\n➕ Добавление принтера в рабочую группу...")
    success = await printer_manager.add_printer_to_workgroup(test_printer, "wb_print_group")
    if success:
        print("✅ Принтер успешно добавлен в группу")
    else:
        print("❌ Ошибка при добавлении принтера в группу")
        return
    
    # Тестируем получение принтеров из группы
    print("\n📋 Получение принтеров из рабочей группы...")
    workgroup_printers = await printer_manager.get_workgroup_printers("wb_print_group")
    print(f"Принтеров в группе: {len(workgroup_printers)}")
    
    for printer in workgroup_printers:
        print(f"  - {printer['name']} ({printer['type']})")
    
    # Тестируем удаление из группы
    print("\n➖ Удаление принтера из рабочей группы...")
    success = await printer_manager.remove_printer_from_workgroup(test_printer, "wb_print_group")
    if success:
        print("✅ Принтер успешно удален из группы")
    else:
        print("❌ Ошибка при удалении принтера из группы")
    
    # Проверяем, что группа пуста
    workgroup_printers = await printer_manager.get_workgroup_printers("wb_print_group")
    print(f"Принтеров в группе после удаления: {len(workgroup_printers)}")
    
    print("\n🎉 Тестирование завершено!")

async def test_web_api():
    """Тестирование веб-API"""
    print("\n🌐 Тестирование веб-API...")
    
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем системные принтеры
            async with session.get(f"{base_url}/api/system/printers") as response:
                if response.status == 200:
                    data = await response.json()
                    printers = data["printers"]
                    print(f"✅ Системных принтеров: {len(printers)}")
                    
                    if printers:
                        test_printer = printers[0]["name"]
                        print(f"🎯 Тестируем с принтером: {test_printer}")
                        
                        # Добавляем принтер в группу
                        data = {
                            "name": test_printer,
                            "workgroup": "wb_print_group"
                        }
                        
                        async with session.post(
                            f"{base_url}/api/workgroup/printers/add",
                            json=data
                        ) as response:
                            if response.status == 200:
                                print("✅ Принтер успешно добавлен в группу через API")
                            else:
                                error_text = await response.text()
                                print(f"❌ Ошибка API: {response.status} - {error_text}")
                        
                        # Получаем принтеры из группы
                        async with session.get(f"{base_url}/api/workgroup/printers") as response:
                            if response.status == 200:
                                data = await response.json()
                                workgroup_printers = data["printers"]
                                print(f"✅ Принтеров в группе: {len(workgroup_printers)}")
                            else:
                                print(f"❌ Ошибка получения группы: {response.status}")
                else:
                    print(f"❌ Ошибка получения системных принтеров: {response.status}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Не удалось подключиться к веб-серверу. Убедитесь, что он запущен.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов рабочей группы принтеров...")
    
    # Тестируем базовую функциональность и веб-API
    asyncio.run(test_workgroup_functionality())
    asyncio.run(test_web_api()) 