#!/usr/bin/env python3
"""
Менеджер принтеров для обнаружения системных принтеров
и управления рабочей группой печати
"""

import asyncio
import subprocess
import platform
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class PrinterManager:
    """Менеджер для работы с системными принтерами"""
    
    def __init__(self):
        self.system = platform.system().lower()
        
    async def get_system_printers(self) -> List[Dict[str, Any]]:
        """
        Получить список всех доступных принтеров в системе
        
        Returns:
            List[Dict[str, Any]]: Список принтеров с их характеристиками
        """
        if self.system == "windows":
            return await self._get_windows_printers()
        elif self.system == "linux":
            return await self._get_linux_printers()
        elif self.system == "darwin":  # macOS
            return await self._get_macos_printers()
        else:
            return []
            
    async def _get_windows_printers(self) -> List[Dict[str, Any]]:
        """Получить принтеры в Windows"""
        try:
            # Используем PowerShell для получения информации о принтерах
            cmd = [
                "powershell", 
                "-Command", 
                "Get-Printer | ConvertTo-Json -Depth 3"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                printers_data = json.loads(result.stdout)
                if isinstance(printers_data, dict):
                    printers_data = [printers_data]
                    
                printers = []
                for printer in printers_data:
                    printers.append({
                        "name": printer.get("Name", ""),
                        "id": printer.get("Name", ""),
                        "type": self._detect_printer_type(printer.get("DriverName", "")),
                        "status": printer.get("PrinterStatus", "Unknown"),
                        "location": printer.get("Location", ""),
                        "port": printer.get("PortName", ""),
                        "driver": printer.get("DriverName", ""),
                        "is_shared": printer.get("Shared", False),
                        "is_default": printer.get("Default", False)
                    })
                return printers
            else:
                print(f"Ошибка получения принтеров Windows: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"Ошибка при получении принтеров Windows: {e}")
            return []
            
    async def _get_linux_printers(self) -> List[Dict[str, Any]]:
        """Получить принтеры в Linux"""
        try:
            # Используем lpstat для получения списка принтеров
            result = subprocess.run(
                ["lpstat", "-p", "-d"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                printers = []
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if line.startswith('printer'):
                        # Парсим строку вида: printer HP_LaserJet is idle.  enabled since ...
                        match = re.match(r'printer\s+(\w+)\s+is\s+(\w+)', line)
                        if match:
                            name = match.group(1)
                            status = match.group(2)
                            
                            printers.append({
                                "name": name,
                                "id": name,
                                "type": self._detect_printer_type(name),
                                "status": status,
                                "location": "",
                                "port": "",
                                "driver": "",
                                "is_shared": False,
                                "is_default": False
                            })
                            
                return printers
            else:
                print(f"Ошибка получения принтеров Linux: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"Ошибка при получении принтеров Linux: {e}")
            return []
            
    async def _get_macos_printers(self) -> List[Dict[str, Any]]:
        """Получить принтеры в macOS"""
        try:
            # Используем lpstat для получения списка принтеров
            result = subprocess.run(
                ["lpstat", "-p"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                printers = []
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if line.startswith('printer'):
                        # Парсим строку вида: printer HP_LaserJet is idle.  enabled since ...
                        match = re.match(r'printer\s+(\w+)\s+is\s+(\w+)', line)
                        if match:
                            name = match.group(1)
                            status = match.group(2)
                            
                            printers.append({
                                "name": name,
                                "id": name,
                                "type": self._detect_printer_type(name),
                                "status": status,
                                "location": "",
                                "port": "",
                                "driver": "",
                                "is_shared": False,
                                "is_default": False
                            })
                            
                return printers
            else:
                print(f"Ошибка получения принтеров macOS: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"Ошибка при получении принтеров macOS: {e}")
            return []
            
    def _detect_printer_type(self, name: str) -> str:
        """Определить тип принтера по названию"""
        name_lower = name.lower()
        
        if any(keyword in name_lower for keyword in ['thermal', 'termo', 'термо']):
            return 'thermal'
        elif any(keyword in name_lower for keyword in ['laser', 'лазер']):
            return 'laser'
        elif any(keyword in name_lower for keyword in ['inkjet', 'струй']):
            return 'inkjet'
        elif any(keyword in name_lower for keyword in ['dot', 'матрич']):
            return 'dot_matrix'
        else:
            return 'unknown'
            
    async def add_printer_to_workgroup(self, printer_name: str, workgroup_name: str = "wb_print_group") -> bool:
        """
        Добавить принтер в рабочую группу
        
        Args:
            printer_name: Имя принтера
            workgroup_name: Название рабочей группы
            
        Returns:
            bool: Успешность операции
        """
        try:
            # Проверяем, что принтер существует в системе
            system_printers = await self.get_system_printers()
            printer_exists = any(p["name"] == printer_name for p in system_printers)
            
            if not printer_exists:
                print(f"Принтер {printer_name} не найден в системе")
                return False
            
            # Используем Redis для хранения информации о рабочей группе
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Добавляем принтер в группу
            result = r.sadd(f"workgroup:{workgroup_name}", printer_name)
            
            # Сохраняем информацию о принтере
            printer_info = next((p for p in system_printers if p["name"] == printer_name), None)
            if printer_info:
                # Преобразуем все значения в строки для Redis
                printer_data = {}
                for key, value in printer_info.items():
                    if isinstance(value, bool):
                        printer_data[key] = str(value).lower()
                    else:
                        printer_data[key] = str(value)
                r.hset(f"printer:{printer_name}", mapping=printer_data)
            
            r.close()
            return True
                
        except Exception as e:
            print(f"Ошибка при добавлении принтера в группу: {e}")
            return False
            

            
    async def remove_printer_from_workgroup(self, printer_name: str, workgroup_name: str = "wb_print_group") -> bool:
        """
        Удалить принтер из рабочей группы
        
        Args:
            printer_name: Имя принтера
            workgroup_name: Название рабочей группы
            
        Returns:
            bool: Успешность операции
        """
        try:
            # Используем Redis для удаления принтера из группы
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Удаляем принтер из группы
            r.srem(f"workgroup:{workgroup_name}", printer_name)
            
            # Удаляем информацию о принтере
            r.delete(f"printer:{printer_name}")
            
            r.close()
            return True
                
        except Exception as e:
            print(f"Ошибка при удалении принтера из группы: {e}")
            return False
            

            
    async def get_workgroup_printers(self, workgroup_name: str = "wb_print_group") -> List[Dict[str, Any]]:
        """
        Получить принтеры из рабочей группы
        
        Args:
            workgroup_name: Название рабочей группы
            
        Returns:
            List[Dict[str, Any]]: Список принтеров в группе
        """
        try:
            # Используем Redis для получения принтеров из группы
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Получаем принтеры из группы
            printer_names = r.smembers(f"workgroup:{workgroup_name}")
            
            printers = []
            for printer_name in printer_names:
                # Получаем актуальную информацию о принтере из системы
                system_printers = await self.get_system_printers()
                printer_data = next((p for p in system_printers if p["name"] == printer_name), None)
                
                if printer_data:
                    # Обновляем информацию в Redis
                    printer_info = {}
                    for key, value in printer_data.items():
                        if isinstance(value, bool):
                            printer_info[key] = str(value).lower()
                        else:
                            printer_info[key] = str(value)
                    r.hset(f"printer:{printer_name}", mapping=printer_info)
                    
                    printers.append(printer_data)
                else:
                    # Если принтер не найден в системе, получаем из Redis
                    printer_info = r.hgetall(f"printer:{printer_name}")
                    if printer_info:
                        printer_data = {}
                        for key, value in printer_info.items():
                            if value.lower() in ['true', 'false']:
                                printer_data[key] = value.lower() == 'true'
                            elif value.isdigit():
                                printer_data[key] = int(value)
                            else:
                                printer_data[key] = value
                        printers.append(printer_data)
            
            r.close()
            return printers
                
        except Exception as e:
            print(f"Ошибка при получении принтеров группы: {e}")
            return []
            



# Для тестирования
if __name__ == "__main__":
    async def main():
        manager = PrinterManager()
        
        print("🔍 Поиск системных принтеров...")
        printers = await manager.get_system_printers()
        
        print(f"📋 Найдено принтеров: {len(printers)}")
        for printer in printers:
            print(f"  - {printer['name']} ({printer['type']}) - {printer['status']}")
            
        print("\n🏷️ Принтеры в рабочей группе:")
        workgroup_printers = await manager.get_workgroup_printers()
        print(f"  Найдено: {len(workgroup_printers)}")
        
    asyncio.run(main()) 