#!/usr/bin/env python3
"""
Процессор для обработки задач печати
Адаптирован для работы с win32print и печати изображений
"""

import asyncio
import json
import os
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

# Добавляем корневую папку в путь для импортов
sys.path.append(str(Path(__file__).parent.parent))

from printer.add_to_print import PrintQueueManager

# Импортируем модули для Windows печати
try:
    import win32print
    import win32ui
    from PIL import Image, ImageWin
    WINDOWS_PRINT_AVAILABLE = True
except ImportError:
    WINDOWS_PRINT_AVAILABLE = False
    print("⚠️ win32print не установлен. Установите: pip install pywin32")

try:
    from printer.powershell_print import print_file_powershell
    POWERSHELL_PRINT_AVAILABLE = True
except ImportError:
    POWERSHELL_PRINT_AVAILABLE = False
    print("⚠️ Модуль PowerShell печати недоступен")


class PrintProcessor:
    """Процессор для обработки задач печати"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.queue_manager = PrintQueueManager(redis_url)
        self.running = False
        self.printers = {}
        
    async def start_processing(self, check_interval: int = 5):
        """
        Запускает обработку очереди печати
        
        Args:
            check_interval: Интервал проверки новых задач в секундах
        """
        self.running = True
        print("🚀 Процессор печати запущен")
        
        try:
            while self.running:
                await self._process_queue()
                await asyncio.sleep(check_interval)
        except KeyboardInterrupt:
            print("\n⏹️ Остановка процессора печати...")
            self.running = False
        except Exception as e:
            print(f"❌ Ошибка в процессоре: {e}")
            self.running = False
            
    async def _process_queue(self):
        """Обрабатывает очередь печати"""
        # Получаем список доступных принтеров
        available_printers = await self._get_available_printers()
        
        if not available_printers:
            print("⚠️ Нет доступных принтеров")
            return
            
        # Обрабатываем задачи для каждого принтера
        for printer_id in available_printers:
            task = await self.queue_manager.get_next_task(printer_id)
            if task:
                print(f"🖨️ Принтер {printer_id} получил задачу: {task['id']}")
                await self._print_task(task, printer_id)
                
    async def _get_available_printers(self) -> List[str]:
        """Получает список доступных принтеров из рабочей группы"""
        try:
            # Импортируем PrinterManager для получения принтеров из рабочей группы
            from .printer_manager import PrinterManager
            
            printer_manager = PrinterManager()
            workgroup_printers = await printer_manager.get_workgroup_printers("wb_print_group")
            
            available = []
            for printer in workgroup_printers:
                printer_name = printer.get("name", "")
                
                # Получаем актуальный статус принтера из системы
                current_status = await self._get_printer_status(printer_name)
                
                # Проверяем статус принтера
                if current_status == 0:  # 0 = готов
                    available.append(printer_name)
                    print(f"✅ Принтер {printer_name} готов (статус: {current_status})")
                else:
                    print(f"⚠️ Принтер {printer_name} не готов (статус: {current_status})")
                    
            if not available:
                print("⚠️ Нет доступных принтеров в рабочей группе")
                
            return available
        except Exception as e:
            print(f"Ошибка при получении принтеров из рабочей группы: {e}")
            return []
            
    async def _get_printer_status(self, printer_name: str) -> int:
        """Получает актуальный статус принтера из системы"""
        try:
            cmd = [
                "powershell", 
                "-Command", 
                f"Get-Printer -Name '{printer_name}' | Select-Object -ExpandProperty PrinterStatus"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                status_str = result.stdout.strip()
                # Новая логика: если строка, проверяем на 'normal', 'idle', 'ready'
                try:
                    return int(status_str)
                except ValueError:
                    status_str_l = status_str.lower()
                    if status_str_l in ["normal", "idle", "ready"]:
                        return 0
                    print(f"⚠️ Неизвестный статус принтера: {status_str}")
                    return 999  # Неизвестный статус
            else:
                print(f"❌ Ошибка получения статуса принтера {printer_name}: {result.stderr}")
                return 999
                
        except Exception as e:
            print(f"❌ Ошибка получения статуса принтера {printer_name}: {e}")
            return 999
            
    async def _print_task(self, task: Dict[str, Any], printer_id: str):
        """
        Выполняет печать задачи
        
        Args:
            task: Данные задачи
            printer_id: ID принтера
        """
        file_path = task.get("file_path")
        task_id = task.get("id")
        
        if not file_path or not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            if task_id:
                await self.queue_manager.mark_task_completed(task_id, printer_id)
            return
            
        try:
            print(f"🖨️ Печатаем файл: {file_path} на принтере {printer_id}")
            
            # Запускаем печать
            success = await self._print_file(file_path, printer_id)
            
            if success:
                # Ждем завершения печати
                if task_id:
                    print(f"⏳ Ожидаем завершения печати: {task_id}")
                    await self._wait_for_print_completion(printer_id, str(task_id))
                    
                    print(f"✅ Печать завершена: {task_id}")
                    await self.queue_manager.mark_task_completed(task_id, printer_id)
            else:
                print(f"❌ Ошибка печати: {task_id}")
                # Возвращаем задачу в очередь
                await self._return_task_to_queue(task)
                
        except Exception as e:
            print(f"❌ Ошибка при печати: {e}")
            await self._return_task_to_queue(task)
            
    async def _print_file(self, file_path: str, printer_id: str) -> bool:
        """
        Запускает печать файла
        
        Args:
            file_path: Путь к файлу
            printer_id: ID принтера
            
        Returns:
            bool: Успешность печати
        """
        try:
            if platform.system() == "Windows":
                # Windows - используем адаптированный код для печати изображений
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    return await self._print_image_windows(file_path, printer_id)
                else:
                    # Для других файлов используем PowerShell
                    return await self._print_file_powershell(file_path, printer_id)
            else:
                # Linux/Mac - используем lp
                result = subprocess.run(
                    ["lp", "-d", printer_id, file_path], 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                if result.returncode == 0:
                    print(f"✅ Файл отправлен на печать: {file_path}")
                    return True
                else:
                    print(f"❌ Ошибка печати: {result.stderr}")
                    return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Таймаут печати: {file_path}")
            return False
        except FileNotFoundError:
            print(f"❌ Команда печати не найдена")
            return False
        except Exception as e:
            print(f"❌ Ошибка печати: {e}")
            return False
            
    async def _print_image_windows(self, file_path: str, printer_id: str) -> bool:
        """
        Печатает изображение в Windows через win32print
        
        Args:
            file_path: Путь к изображению
            printer_id: Имя принтера из рабочей группы
            
        Returns:
            bool: Успешность печати
        """
        if not WINDOWS_PRINT_AVAILABLE:
            print("❌ win32print недоступен")
            return False
            
        try:
            # Используем реальное имя принтера из рабочей группы
            printer_name = printer_id
            print(f"🖨️ Печатаем изображение через win32print: {file_path}")
            
            # Открываем принтер
            hprinter = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(hprinter, 2)
            
            # Создаем DC для принтера
            pdc = win32ui.CreateDC()
            pdc.CreatePrinterDC(printer_name)
            pdc.StartDoc("Image Print Job")
            pdc.StartPage()
            
            # Открываем и вставляем изображение
            img = Image.open(file_path)
            bmp = img.convert("RGB")  # Конвертируем в RGB
            
            # Масштабирование под A4 (например)
            width, height = bmp.size
            dib = ImageWin.Dib(bmp)
            dib.draw(pdc.GetHandleOutput(), (0, 0, width, height))
            
            # Завершаем печать
            pdc.EndPage()
            pdc.EndDoc()
            pdc.DeleteDC()
            
            print(f"✅ Изображение отправлено на печать: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка печати изображения: {e}")
            return False
            
    async def _print_file_powershell(self, file_path: str, printer_id: str) -> bool:
        """
        Печатает файл через PowerShell
        
        Args:
            file_path: Путь к файлу
            printer_id: Имя принтера из рабочей группы
            
        Returns:
            bool: Успешность печати
        """
        try:
            if POWERSHELL_PRINT_AVAILABLE:
                # Используем реальное имя принтера из рабочей группы
                printer_name = printer_id
                success = print_file_powershell(file_path, printer_name)
                return success
            else:
                # Fallback - простой PowerShell с указанием принтера
                print(f"🖨️ Используем PowerShell для печати {file_path} на принтере {printer_id}")
                print_cmd = [
                    "powershell", 
                    "-Command", 
                    f"Start-Process -FilePath '{file_path}' -Verb Print -WindowStyle Hidden"
                ]
                
                result = subprocess.run(print_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✅ Файл отправлен на печать: {file_path}")
                    return True
                else:
                    print(f"❌ Ошибка печати PowerShell: {result.stderr}")
                    return False
                    
        except Exception as e:
            print(f"❌ Ошибка PowerShell печати: {e}")
            return False
            
    async def _wait_for_print_completion(self, printer_id: str, task_id: str, timeout: int = 60):
        """
        Ожидает завершения печати
        
        Args:
            printer_id: ID принтера
            task_id: ID задачи
            timeout: Таймаут ожидания в секундах
        """
        try:
            if platform.system() == "Windows":
                # В Windows используем PowerShell для проверки статуса печати
                await self._wait_for_windows_print_completion(printer_id, task_id, timeout)
            else:
                # В Linux/Mac ждем фиксированное время
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"⚠️ Ошибка при ожидании завершения печати: {e}")
            # В случае ошибки ждем фиксированное время
            await asyncio.sleep(5)
            
    async def _wait_for_windows_print_completion(self, printer_id: str, task_id: str, timeout: int = 60):
        """
        Ожидает завершения печати в Windows
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                # Проверяем задания печати
                cmd = [
                    "powershell", 
                    "-Command", 
                    f"Get-PrintJob -PrinterName '{printer_id}' | Select-Object JobId, Document, JobStatus | ConvertTo-Json"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    jobs_data = result.stdout.strip()
                    
                    if not jobs_data:
                        # Нет заданий печати - принтер готов
                        print(f"✅ Принтер {printer_id} готов (нет активных заданий)")
                        return
                    else:
                        # Есть задания печати - ждем
                        print(f"⏳ Принтер {printer_id} занят (есть активные задания)")
                        
                        # Дополнительно проверяем статус принтера
                        status_cmd = [
                            "powershell", 
                            "-Command", 
                            f"Get-Printer -Name '{printer_id}' | Select-Object -ExpandProperty PrinterStatus"
                        ]
                        
                        status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=5)
                        if status_result.returncode == 0:
                            status = status_result.stdout.strip()
                            print(f"  Статус принтера: {status}")
                else:
                    print(f"⚠️ Ошибка получения заданий печати: {result.stderr}")
                
                # Ждем 3 секунды перед следующей проверкой
                await asyncio.sleep(3)
                
            print(f"⏰ Таймаут ожидания завершения печати для задачи {task_id}")
            
        except Exception as e:
            print(f"❌ Ошибка проверки статуса принтера: {e}")
            
    async def _return_task_to_queue(self, task: Dict[str, Any]):
        """Возвращает задачу в очередь"""
        try:
            # Сбрасываем статус задачи
            task["status"] = "pending"
            task["assigned_printer"] = None
            
            # Добавляем обратно в очередь
            if self.queue_manager.redis:
                await self.queue_manager.redis.zadd(
                    self.queue_manager.queue_name, 
                    {json.dumps(task): task.get("priority", 1)}
                )
            
            print(f"🔄 Задача возвращена в очередь: {task['id']}")
            
        except Exception as e:
            print(f"❌ Ошибка при возврате задачи в очередь: {e}")
            
    def stop(self):
        """Останавливает процессор"""
        self.running = False


# Функция для запуска процессора
async def start_print_processor(redis_url: str = "redis://localhost:6379"):
    """
    Запускает процессор печати
    
    Args:
        redis_url: URL подключения к Redis
    """
    processor = PrintProcessor(redis_url)
    await processor.start_processing()


# Для тестирования
if __name__ == "__main__":
    async def main():
        print("🚀 Запуск процессора печати...")
        await start_print_processor()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Процессор остановлен") 