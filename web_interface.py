#!/usr/bin/env python3
"""
Веб-интерфейс для управления системой печати Wildberries
- Добавление принтеров в рабочую группу
- Запуск процесса печати
- Мониторинг статуса задач
- Управление очередью печати
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Добавляем корневую папку в путь для импортов
sys.path.append(str(Path(__file__).parent))

from printer.add_to_print import PrintQueueManager, add_orders_to_print_queue, setup_printers
from printer.excel import create_print_status_report
from printer.print_processor import PrintProcessor
from printer.printer_manager import PrinterManager


class WebInterface:
    """Веб-интерфейс для управления системой печати"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.app = FastAPI(
            title="WB Print Manager",
            description="Система управления печатью заказов Wildberries",
            version="1.0.0"
        )
        self.redis_url = redis_url
        self.queue_manager = PrintQueueManager(redis_url)
        self.print_processor = None
        self.active_connections: List[WebSocket] = []
        self.printer_manager = PrinterManager()
        
        # Настройка статических файлов и шаблонов
        self.templates = Jinja2Templates(directory="templates")
        
        # Регистрация маршрутов
        self._setup_routes()
        
    def _setup_routes(self):
        """Настройка маршрутов API"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Главная страница дашборда"""
            return self.templates.TemplateResponse("dashboard.html", {"request": request})
            
        @self.app.get("/api/printers")
        async def get_printers():
            """Получить список принтеров из Redis"""
            try:
                await self.queue_manager.connect()
                printers_data = await self.queue_manager.redis.hgetall(self.queue_manager.printers_key)
                
                printers = []
                for printer_id, printer_json in printers_data.items():
                    printer_data = json.loads(printer_json)
                    printers.append({
                        "id": printer_id.decode() if isinstance(printer_id, bytes) else printer_id,
                        **printer_data
                    })
                    
                return {"printers": printers}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/system/printers")
        async def get_system_printers():
            """Получить список системных принтеров"""
            try:
                printers = await self.printer_manager.get_system_printers()
                return {"printers": printers}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/workgroup/printers")
        async def get_workgroup_printers():
            """Получить принтеры из рабочей группы"""
            try:
                printers = await self.printer_manager.get_workgroup_printers()
                return {"printers": printers}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/workgroup/printers/add")
        async def add_printer_to_workgroup(printer_data: Dict[str, Any]):
            """Добавить принтер в рабочую группу"""
            try:
                printer_name = printer_data.get("name")
                workgroup_name = printer_data.get("workgroup", "wb_print_group")
                
                if not printer_name:
                    raise HTTPException(status_code=400, detail="Имя принтера обязательно")
                    
                success = await self.printer_manager.add_printer_to_workgroup(printer_name, workgroup_name)
                
                if success:
                    return {"message": f"Принтер {printer_name} добавлен в рабочую группу"}
                else:
                    raise HTTPException(status_code=500, detail="Не удалось добавить принтер в группу")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/workgroup/printers/add-multiple", response_model=None)
        async def add_multiple_printers_to_workgroup(printer_data: dict = Body(...)):
            """Добавить несколько принтеров в рабочую группу"""
            try:
                printer_names = printer_data.get("names", [])
                workgroup_name = printer_data.get("workgroup", "wb_print_group")
                if not printer_names:
                    raise HTTPException(status_code=400, detail="Список принтеров обязателен")
                results = []
                for name in printer_names:
                    success = await self.printer_manager.add_printer_to_workgroup(name, workgroup_name)
                    results.append({"name": name, "success": success})
                return {"results": results}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/api/workgroup/printers/{printer_name}")
        async def remove_printer_from_workgroup(printer_name: str):
            """Удалить принтер из рабочей группы"""
            try:
                success = await self.printer_manager.remove_printer_from_workgroup(printer_name)
                
                if success:
                    return {"message": f"Принтер {printer_name} удален из рабочей группы"}
                else:
                    raise HTTPException(status_code=500, detail="Не удалось удалить принтер из группы")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/printers")
        async def add_printer(printer_data: Dict[str, Any]):
            """Добавить принтер"""
            try:
                printer_id = printer_data.get("id")
                if not printer_id:
                    raise HTTPException(status_code=400, detail="ID принтера обязателен")
                    
                await self.queue_manager.add_printer(printer_id, printer_data)
                return {"message": f"Принтер {printer_id} добавлен"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.delete("/api/printers/{printer_id}")
        async def remove_printer(printer_id: str):
            """Удалить принтер"""
            try:
                await self.queue_manager.connect()
                await self.queue_manager.redis.hdel(self.queue_manager.printers_key, printer_id)
                return {"message": f"Принтер {printer_id} удален"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/queue")
        async def get_queue():
            """Получить текущую очередь печати"""
            try:
                await self.queue_manager.connect()
                tasks = await self.queue_manager.redis.zrange("print_queue", 0, -1, withscores=True)
                
                queue_tasks = []
                for task_json, score in tasks:
                    task_data = json.loads(task_json)
                    queue_tasks.append({
                        **task_data,
                        "priority": score
                    })
                    
                return {"tasks": queue_tasks}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/orders/add")
        async def add_orders():
            """Добавить заказы в очередь печати"""
            try:
                task_ids = await add_orders_to_print_queue(self.redis_url)
                return {
                    "message": f"Добавлено {len(task_ids)} задач",
                    "task_ids": task_ids
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/processor/start")
        async def start_processor():
            """Запустить процессор печати"""
            try:
                if self.print_processor and self.print_processor.running:
                    return {"message": "Процессор уже запущен"}
                    
                self.print_processor = PrintProcessor(self.redis_url)
                asyncio.create_task(self.print_processor.start_processing())
                return {"message": "Процессор печати запущен"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/processor/stop")
        async def stop_processor():
            """Остановить процессор печати"""
            try:
                if self.print_processor:
                    self.print_processor.stop()
                    self.print_processor = None
                return {"message": "Процессор печати остановлен"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/excel/generate")
        async def generate_excel():
            """Сгенерировать Excel отчет"""
            try:
                filename = await create_print_status_report(self.redis_url)
                return {"message": "Excel отчет создан", "filename": filename}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/status")
        async def get_status():
            """Получить общий статус системы"""
            try:
                await self.queue_manager.connect()
                
                # Статус принтеров
                printers_data = await self.queue_manager.redis.hgetall(self.queue_manager.printers_key)
                printers_count = len(printers_data)
                
                # Статус очереди
                tasks = await self.queue_manager.redis.zrange("print_queue", 0, -1)
                queue_count = len(tasks)
                
                # Статус процессора
                processor_running = self.print_processor and self.print_processor.running
                
                return {
                    "printers_count": printers_count,
                    "queue_count": queue_count,
                    "processor_running": processor_running,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket для real-time обновлений"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Отправляем обновления каждые 5 секунд
                    await asyncio.sleep(5)
                    status = await get_status()
                    await websocket.send_text(json.dumps(status))
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                
        @self.app.delete("/api/queue/task/{task_id}")
        async def delete_queue_task(task_id: str):
            """Удалить задачу из очереди печати по task_id"""
            try:
                await self.queue_manager.connect()
                removed = await self.queue_manager.remove_task(task_id)
                if removed:
                    return {"message": f"Задача {task_id} удалена"}
                else:
                    raise HTTPException(status_code=404, detail="Задача не найдена")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/queue/task/{task_id}/restart")
        async def restart_queue_task(task_id: str):
            """Перезапустить задачу печати по task_id (ставит обратно в очередь)"""
            try:
                await self.queue_manager.connect()
                restarted = await self.queue_manager.restart_task(task_id)
                if restarted:
                    return {"message": f"Задача {task_id} перезапущена"}
                else:
                    raise HTTPException(status_code=404, detail="Задача не найдена")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/completed-tasks")
        async def get_completed_tasks():
            """Получить выполненные задачи"""
            try:
                await self.queue_manager.connect()
                
                # Получаем выполненные задачи из отдельного хранилища
                tasks = await self.queue_manager.redis.zrange("completed_tasks", 0, -1, withscores=True)
                
                completed_tasks = []
                for task_json, score in tasks:
                    task_data = json.loads(task_json)
                    completed_tasks.append({
                        **task_data,
                        "priority": score
                    })
                
                return {"tasks": completed_tasks}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
    async def broadcast_status(self, status: Dict[str, Any]):
        """Отправить статус всем подключенным клиентам"""
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(status))
            except:
                self.active_connections.remove(connection)


# Создание экземпляра приложения
app = WebInterface().app


if __name__ == "__main__":
    print("🚀 Запуск веб-интерфейса системы печати...")
    print("📱 Откройте http://localhost:8000 в браузере")
    print("📚 API документация: http://localhost:8000/docs")
    
    uvicorn.run(
        "web_interface:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 