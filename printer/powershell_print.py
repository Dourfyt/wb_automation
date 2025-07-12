#!/usr/bin/env python3
"""
Модуль для печати через PowerShell
Использует PowerShell команды для прямой печати файлов
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional


class PowerShellPrinter:
    """Класс для работы с принтерами через PowerShell"""
    
    def __init__(self):
        self.available = platform.system() == "Windows"
        
    def get_printers(self) -> List[Dict[str, str]]:
        """Получает список доступных принтеров через PowerShell"""
        if not self.available:
            return []
            
        try:
            cmd = [
                "powershell", 
                "-Command", 
                "Get-Printer | Select-Object Name, DriverName, PortName | ConvertTo-Json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                printers_data = json.loads(result.stdout)
                if isinstance(printers_data, list):
                    return printers_data
                else:
                    return [printers_data]
            else:
                print(f"❌ Ошибка получения принтеров: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка получения списка принтеров: {e}")
            return []
            
    def get_default_printer(self) -> Optional[str]:
        """Получает имя принтера по умолчанию через PowerShell"""
        if not self.available:
            return None
            
        try:
            # Сначала пробуем получить принтер по умолчанию
            cmd = [
                "powershell", 
                "-Command", 
                "Get-Printer | Where-Object {$_.Default -eq $true} | Select-Object -ExpandProperty Name"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
                
            # Если не получилось, берем первый доступный принтер
            print("⚠️ Принтер по умолчанию не найден, используем первый доступный")
            printers = self.get_printers()
            if printers:
                return printers[0].get('Name', 'HP DeskJet 2300 series')
            else:
                print(f"❌ Ошибка получения принтера по умолчанию: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка получения принтера по умолчанию: {e}")
            return None
            
    def print_file(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        Печатает файл через PowerShell
        
        Args:
            file_path: Путь к файлу для печати
            printer_name: Имя принтера (если None, используется принтер по умолчанию)
            
        Returns:
            bool: Успешность печати
        """
        if not self.available:
            print("❌ Печать недоступна (не Windows)")
            return False
            
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return False
            
        try:
            # Определяем принтер
            if not printer_name:
                printer_name = self.get_default_printer()
                if not printer_name:
                    print("❌ Не найден принтер по умолчанию")
                    return False
                    
            print(f"🖨️ Печатаем {file_path} на принтере {printer_name}")
            
            # Создаем PowerShell команду для печати
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                # Для изображений используем Start-Process с принудительной печатью
                ps_command = f"""
                $file = "{file_path}"
                $printer = "{printer_name}"
                Start-Process -FilePath $file -Verb Print -PassThru
                Write-Host "Изображение отправлено на печать: $file"
                """
            else:
                # Для других файлов используем стандартную печать
                ps_command = f"""
                $file = "{file_path}"
                $printer = "{printer_name}"
                Start-Process -FilePath $file -Verb Print -PassThru
                Write-Host "Файл отправлен на печать: $file"
                """
                
            # Выполняем PowerShell команду
            cmd = [
                "powershell", 
                "-Command", 
                ps_command
            ]
            
            print(f"🔄 Выполняем команду PowerShell для печати...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ Файл отправлен на печать: {file_path}")
                print(f"📋 Вывод PowerShell: {result.stdout}")
                return True
            else:
                print(f"❌ Ошибка печати PowerShell: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Таймаут печати: {file_path}")
            return False
        except Exception as e:
            print(f"❌ Ошибка печати: {e}")
            return False
            
    def print_file_alternative(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        Альтернативный способ печати через rundll32
        
        Args:
            file_path: Путь к файлу
            printer_name: Имя принтера
            
        Returns:
            bool: Успешность печати
        """
        if not self.available:
            return False
            
        try:
            # Определяем принтер
            if not printer_name:
                printer_name = self.get_default_printer()
                if not printer_name:
                    print("❌ Не найден принтер по умолчанию")
                    return False
                    
            print(f"🔄 Альтернативная печать: {file_path} на принтере {printer_name}")
            
            # Используем rundll32 для печати изображений
            cmd = [
                "rundll32", 
                "shimgvw.dll,ImageView_PrintTo", 
                file_path, 
                printer_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Файл отправлен на печать (rundll32): {file_path}")
                return True
            else:
                print(f"❌ Ошибка печати rundll32: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка альтернативной печати: {e}")
            return False


def print_file_powershell(file_path: str, printer_name: Optional[str] = None) -> bool:
    """
    Функция для печати файла через PowerShell
    
    Args:
        file_path: Путь к файлу
        printer_name: Имя принтера
        
    Returns:
        bool: Успешность печати
    """
    printer = PowerShellPrinter()
    
    # Сначала пробуем PowerShell
    if printer.print_file(file_path, printer_name):
        return True
        
    # Если не получилось, пробуем альтернативный способ
    return printer.print_file_alternative(file_path, printer_name)


def get_powershell_printers() -> List[Dict[str, str]]:
    """
    Получает список принтеров через PowerShell
    
    Returns:
        List[Dict[str, str]]: Список принтеров
    """
    printer = PowerShellPrinter()
    return printer.get_printers()


if __name__ == "__main__":
    # Тестирование
    printer = PowerShellPrinter()
    
    print("📋 Доступные принтеры:")
    printers = printer.get_printers()
    for p in printers:
        print(f"  - {p.get('Name', 'Unknown')} ({p.get('DriverName', 'Unknown')})")
        
    default = printer.get_default_printer()
    print(f"🖨️ Принтер по умолчанию: {default}")
    
    # Тест печати
    test_file = "for_print/test-article-001/ПЕЧАТЬ.png"
    if os.path.exists(test_file):
        print(f"🖨️ Тестируем печать: {test_file}")
        success = printer.print_file(test_file)
        print(f"Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
    else:
        print(f"❌ Тестовый файл не найден: {test_file}") 