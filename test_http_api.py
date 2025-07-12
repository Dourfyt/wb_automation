#!/usr/bin/env python3
"""
Тестовый скрипт для проверки HTTP API
"""

import requests
import json

def test_http_api():
    """Тестируем HTTP API"""
    base_url = "http://localhost:8000"
    
    print("🧪 Тестирование HTTP API...")
    
    # Тест 1: Получение очереди
    print("\n1️⃣ Получение очереди...")
    try:
        response = requests.get(f"{base_url}/api/queue")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Задач в очереди: {len(data.get('tasks', []))}")
            for task in data.get('tasks', []):
                print(f"  - Задача {task.get('id')}: {task.get('article')}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Тест 2: Добавление заказов
    print("\n2️⃣ Добавление заказов...")
    try:
        response = requests.post(f"{base_url}/api/orders/add")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Добавлено задач: {len(data.get('task_ids', []))}")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: Получение очереди снова
    print("\n3️⃣ Получение очереди после добавления...")
    try:
        response = requests.get(f"{base_url}/api/queue")
        print(f"Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            tasks = data.get('tasks', [])
            print(f"Задач в очереди: {len(tasks)}")
            
            # Тест 4: Удаление первой задачи
            if tasks:
                task_id = tasks[0]['id']
                print(f"\n4️⃣ Удаление задачи {task_id}...")
                
                delete_response = requests.delete(f"{base_url}/api/queue/task/{task_id}")
                print(f"Статус удаления: {delete_response.status_code}")
                if delete_response.status_code == 200:
                    data = delete_response.json()
                    print(f"Результат: {data.get('message')}")
                else:
                    print(f"Ошибка удаления: {delete_response.text}")
                
                # Проверяем, что задача удалена
                print(f"\n5️⃣ Проверка после удаления...")
                check_response = requests.get(f"{base_url}/api/queue")
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    remaining_tasks = check_data.get('tasks', [])
                    print(f"Задач в очереди после удаления: {len(remaining_tasks)}")
                    
                    if len(remaining_tasks) == len(tasks) - 1:
                        print("✅ Удаление прошло успешно!")
                    else:
                        print("❌ Задача не была удалена")
        else:
            print(f"Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_http_api() 