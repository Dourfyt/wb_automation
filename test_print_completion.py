#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ожидания завершения печати
"""

import asyncio
import subprocess
from printer.printer_manager import PrinterManager

async def test_printer_status():
    """Тестируем проверку статуса принтера"""
    print("🔍 Тестирование статуса принтера...")
    
    # Получаем принтеры из рабочей группы
    manager = PrinterManager()
    workgroup_printers = await manager.get_workgroup_printers("wb_print_group")
    
    if not workgroup_printers:
        print("❌ Нет принтеров в рабочей группе")
        return
    
    printer_name = workgroup_printers[0]["name"]
    print(f"🎯 Тестируем принтер: {printer_name}")
    
    # Проверяем текущий статус
    cmd = [
        "powershell", 
        "-Command", 
        f"Get-Printer -Name '{printer_name}' | Select-Object Name, PrinterStatus, DriverName | ConvertTo-Json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            import json
            printer_info = json.loads(result.stdout)
            print(f"📋 Информация о принтере:")
            print(f"  Имя: {printer_info.get('Name', 'N/A')}")
            print(f"  Статус: {printer_info.get('PrinterStatus', 'N/A')}")
            print(f"  Драйвер: {printer_info.get('DriverName', 'N/A')}")
        else:
            print(f"❌ Ошибка получения информации: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def test_print_job_monitoring():
    """Тестируем мониторинг заданий печати"""
    print("\n🖨️ Тестирование мониторинга заданий печати...")
    
    # Получаем принтеры из рабочей группы
    manager = PrinterManager()
    workgroup_printers = await manager.get_workgroup_printers("wb_print_group")
    
    if not workgroup_printers:
        print("❌ Нет принтеров в рабочей группе")
        return
    
    printer_name = workgroup_printers[0]["name"]
    
    # Проверяем задания печати
    cmd = [
        "powershell", 
        "-Command", 
        f"Get-PrintJob -PrinterName '{printer_name}' | Select-Object JobId, Document, JobStatus, SubmittedTime | ConvertTo-Json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            import json
            jobs_data = result.stdout.strip()
            
            if jobs_data:
                if jobs_data.startswith('['):
                    jobs = json.loads(jobs_data)
                else:
                    jobs = [json.loads(jobs_data)]
                
                print(f"📋 Заданий печати: {len(jobs)}")
                for job in jobs:
                    print(f"  ID: {job.get('JobId', 'N/A')}")
                    print(f"  Документ: {job.get('Document', 'N/A')}")
                    print(f"  Статус: {job.get('JobStatus', 'N/A')}")
                    print(f"  Время: {job.get('SubmittedTime', 'N/A')}")
                    print("  ---")
            else:
                print("📋 Нет активных заданий печати")
        else:
            print(f"❌ Ошибка получения заданий: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_printer_status())
    asyncio.run(test_print_job_monitoring()) 