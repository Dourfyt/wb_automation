#!/usr/bin/env python3
"""
Модуль для печати в Windows
Использует win32print для прямой печати файлов
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional

try:
    import win32print
    import win32api
    import win32con
    WINDOWS_PRINT_AVAILABLE = True
except ImportError:
    WINDOWS_PRINT_AVAILABLE = False
    print("⚠️ win32print не установлен. Установите: pip install pywin32")


class WindowsPrinter:
    """Класс для работы с принтерами в Windows"""
    
    def __init__(self):
        self.available = WINDOWS_PRINT_AVAILABLE and platform.system() == "Windows"
        
    def get_printers(self) -> List[Dict[str, str]]:
        """Получает список доступных принтеров"""
        if not self.available:
            return []
            
        try:
            printers = []
            for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 1):
                printers.append({
                    "name": printer[2],
                    "port": printer[1],
                    "description": printer[3] if len(printer) > 3 else ""
                })
            return printers
        except Exception as e:
            print(f"❌ Ошибка получения списка принтеров: {e}")
            return []
            
    def get_default_printer(self) -> Optional[str]:
        """Получает имя принтера по умолчанию"""
        if not self.available:
            return None
            
        try:
            return win32print.GetDefaultPrinter()
        except Exception as e:
            print(f"❌ Ошибка получения принтера по умолчанию: {e}")
            return None
            
    def print_file(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        Печатает файл на указанном принтере
        
        Args:
            file_path: Путь к файлу для печати
            printer_name: Имя принтера (если None, используется принтер по умолчанию)
            
        Returns:
            bool: Успешность печати
        """
        if not self.available:
            print("❌ Печать недоступна (не Windows или win32print не установлен)")
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
            
            # Открываем принтер
            printer_handle = win32print.OpenPrinter(printer_name)
            
            try:
                # Получаем информацию о принтере
                printer_info = win32print.GetPrinter(printer_handle, 2)
                
                # Открываем документ
                doc_info = ('Print Job', None, 'RAW')
                job_id = win32print.StartDocPrinter(printer_handle, 1, doc_info)
                
                try:
                    # Начинаем страницу
                    win32print.StartPagePrinter(printer_handle)
                    
                    # Для изображений используем ShellExecute
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        # Используем ShellExecute для изображений
                        win32api.ShellExecute(
                            0, 
                            "print", 
                            file_path, 
                            None, 
                            ".", 
                            0
                        )
                    else:
                        # Для других файлов используем ShellExecute с print
                        win32api.ShellExecute(
                            0, 
                            "print", 
                            file_path, 
                            f'"{printer_name}"', 
                            ".", 
                            0
                        )
                    
                    # Завершаем страницу
                    win32print.EndPagePrinter(printer_handle)
                    
                finally:
                    # Завершаем документ
                    win32print.EndDocPrinter(printer_handle)
                    
            finally:
                # Закрываем принтер
                win32print.ClosePrinter(printer_handle)
                
            print(f"✅ Файл отправлен на печать: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка печати: {e}")
            return False
            
    def print_file_simple(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        Простой способ печати через ShellExecute
        
        Args:
            file_path: Путь к файлу
            printer_name: Имя принтера
            
        Returns:
            bool: Успешность печати
        """
        if not self.available:
            return False
            
        try:
            # Для изображений используем прямой способ через win32print
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                return self._print_image_direct(file_path, printer_name)
            else:
                # Для других файлов используем ShellExecute
                if printer_name:
                    win32api.ShellExecute(
                        0, 
                        "print", 
                        file_path, 
                        f'"{printer_name}"', 
                        ".", 
                        0
                    )
                else:
                    win32api.ShellExecute(
                        0, 
                        "print", 
                        file_path, 
                        None, 
                        ".", 
                        0
                    )
                    
                print(f"✅ Файл отправлен на печать (ShellExecute): {file_path}")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка простой печати: {e}")
            return False
            
    def _print_image_direct(self, file_path: str, printer_name: Optional[str] = None) -> bool:
        """
        Прямая печать изображения через win32print
        
        Args:
            file_path: Путь к изображению
            printer_name: Имя принтера
            
        Returns:
            bool: Успешность печати
        """
        try:
            # Определяем принтер
            if not printer_name:
                printer_name = self.get_default_printer()
                if not printer_name:
                    print("❌ Не найден принтер по умолчанию")
                    return False
                    
            print(f"🖨️ Прямая печать изображения: {file_path} на принтере {printer_name}")
            
            # Открываем принтер
            printer_handle = win32print.OpenPrinter(printer_name)
            
            try:
                # Получаем информацию о принтере
                printer_info = win32print.GetPrinter(printer_handle, 2)
                
                # Открываем документ
                doc_info = ('Print Job', None, 'RAW')
                job_id = win32print.StartDocPrinter(printer_handle, 1, doc_info)
                
                try:
                    # Начинаем страницу
                    win32print.StartPagePrinter(printer_handle)
                    
                    # Для изображений используем ShellExecute с принудительной печатью
                    # Это должно отправить задание в очередь принтера
                    win32api.ShellExecute(
                        0, 
                        "print", 
                        file_path, 
                        f'"{printer_name}"', 
                        ".", 
                        0
                    )
                    
                    # Завершаем страницу
                    win32print.EndPagePrinter(printer_handle)
                    
                finally:
                    # Завершаем документ
                    win32print.EndDocPrinter(printer_handle)
                    
            finally:
                # Закрываем принтер
                win32print.ClosePrinter(printer_handle)
                
            print(f"✅ Изображение отправлено на печать: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка прямой печати изображения: {e}")
            return False


def print_file_windows(file_path: str, printer_name: Optional[str] = None) -> bool:
    """
    Функция для печати файла в Windows
    
    Args:
        file_path: Путь к файлу
        printer_name: Имя принтера
        
    Returns:
        bool: Успешность печати
    """
    printer = WindowsPrinter()
    
    # Сначала пробуем простой способ
    if printer.print_file_simple(file_path, printer_name):
        return True
        
    # Если не получилось, пробуем сложный способ
    return printer.print_file(file_path, printer_name)


def get_windows_printers() -> List[Dict[str, str]]:
    """
    Получает список принтеров Windows
    
    Returns:
        List[Dict[str, str]]: Список принтеров
    """
    printer = WindowsPrinter()
    return printer.get_printers()


if __name__ == "__main__":
    # Тестирование
    printer = WindowsPrinter()
    
    print("📋 Доступные принтеры:")
    printers = printer.get_printers()
    for p in printers:
        print(f"  - {p['name']} ({p['port']})")
        
    default = printer.get_default_printer()
    print(f"🖨️ Принтер по умолчанию: {default}")
    
    # Тест печати
    test_file = r"F:\wb_automation\for_print\test-article-001\ПЕЧАТЬ.png"
    if os.path.exists(test_file):
        print(f"🖨️ Тестируем печать: {test_file}")
        success = printer.print_file_simple(test_file)
        print(f"Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
    else:
        print(f"❌ Тестовый файл не найден: {test_file}") 