import os
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import json

# Загружаем переменные окружения из .env файла
load_dotenv()

def get_auth_headers() -> Dict[str, str]:
    """
    Создает заголовки авторизации с токеном из .env файла
    
    Returns:
        Dict[str, str]: Словарь с заголовками авторизации
    """
    token = os.getenv("WB_TOKEN")
    if not token:
        raise ValueError("WB_TOKEN не найден в .env файле. Пожалуйста, создайте файл .env и добавьте ваш токен Wildberries API: WB_TOKEN=your_token_here")
    
    return {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

async def make_get_request(url: str, params: Optional[Dict[str, Any]] = None, session: Optional[aiohttp.ClientSession] = None) -> aiohttp.ClientResponse:
    """
    Выполняет асинхронный GET запрос с авторизационным токеном
    
    Args:
        url (str): URL для запроса
        params (Optional[Dict[str, Any]]): Параметры запроса
        session (Optional[aiohttp.ClientSession]): Сессия aiohttp (если не передана, создается новая)
        
    Returns:
        aiohttp.ClientResponse: Ответ от сервера
        
    Raises:
        aiohttp.ClientError: При ошибке запроса
        ValueError: Если токен не найден
    """
    headers = get_auth_headers()
    
    try:
        if session is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    print(f"Response status: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Error response: {error_text}")
                    response.raise_for_status()
                    return response
        else:
            async with session.get(url, headers=headers) as response:
                print(f"Response status: {response.status}")
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                response.raise_for_status()
                return response
    except aiohttp.ClientError as e:
        print(f"Ошибка GET запроса к {url}: {e}")
        raise

async def make_post_request(url: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, session: Optional[aiohttp.ClientSession] = None) -> aiohttp.ClientResponse:
    """
    Выполняет асинхронный POST запрос с авторизационным токеном
    
    Args:
        url (str): URL для запроса
        data (Optional[Dict[str, Any]]): Данные для отправки (form-data)
        json_data (Optional[Dict[str, Any]]): JSON данные для отправки
        session (Optional[aiohttp.ClientSession]): Сессия aiohttp (если не передана, создается новая)
        
    Returns:
        aiohttp.ClientResponse: Ответ от сервера
        
    Raises:
        aiohttp.ClientError: При ошибке запроса
        ValueError: Если токен не найден
    """
    headers = get_auth_headers()
    
    try:
        if session is None:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data, json=json_data) as response:
                    response.raise_for_status()
                    return response
        else:
            async with session.post(url, headers=headers, data=data, json=json_data) as response:
                response.raise_for_status()
                return response
    except aiohttp.ClientError as e:
        print(f"Ошибка POST запроса к {url}: {e}")
        raise

async def make_patch_request(url: str, data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None, session: Optional[aiohttp.ClientSession] = None) -> aiohttp.ClientResponse:
    """
    Выполняет асинхронный PATCH запрос с авторизационным токеном
    
    Args:
        url (str): URL для запроса
        data (Optional[Dict[str, Any]]): Данные для отправки (form-data)
        json_data (Optional[Dict[str, Any]]): JSON данные для отправки
        session (Optional[aiohttp.ClientSession]): Сессия aiohttp (если не передана, создается новая)
        
    Returns:
        aiohttp.ClientResponse: Ответ от сервера
        
    Raises:
        aiohttp.ClientError: При ошибке запроса
        ValueError: Если токен не найден
    """
    headers = get_auth_headers()
    
    try:
        if session is None:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, data=data, json=json_data) as response:
                    response.raise_for_status()
                    return response
        else:
            async with session.patch(url, headers=headers, data=data, json=json_data) as response:
                response.raise_for_status()
                return response
    except aiohttp.ClientError as e:
        print(f"Ошибка PATCH запроса к {url}: {e}")
        raise

async def get_json_response(url: str, params: Optional[Dict[str, Any]] = None, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """
    Выполняет асинхронный GET запрос и возвращает JSON ответ
    
    Args:
        url (str): URL для запроса
        params (Optional[Dict[str, Any]]): Параметры запроса
        session (Optional[aiohttp.ClientSession]): Сессия aiohttp (если не передана, создается новая)
        
    Returns:
        Dict[str, Any]: JSON ответ от сервера
    """
    response = await make_get_request(url, params, session)
    response_text = await response.text()
    print(f"Raw response: {response_text}")
    
    if not response_text.strip():
        print("Empty response received")
        return {}
    
    try:
        return await response.json()
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response text: {response_text}")
        return {}

async def post_json_data(url: str, json_data: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """
    Выполняет асинхронный POST запрос с JSON данными и возвращает JSON ответ
    
    Args:
        url (str): URL для запроса
        json_data (Dict[str, Any]): JSON данные для отправки
        session (Optional[aiohttp.ClientSession]): Сессия aiohttp (если не передана, создается новая)
        
    Returns:
        Dict[str, Any]: JSON ответ от сервера
    """
    response = await make_post_request(url, json_data=json_data, session=session)
    return await response.json()

async def patch_json_data(url: str, json_data: Dict[str, Any], session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """
    Выполняет асинхронный PATCH запрос с JSON данными и возвращает JSON ответ
    
    Args:
        url (str): URL для запроса
        json_data (Dict[str, Any]): JSON данные для отправки
        session (Optional[aiohttp.ClientSession]): Сессия aiohttp (если не передана, создается новая)
        
    Returns:
        Dict[str, Any]: JSON ответ от сервера
    """
    response = await make_patch_request(url, json_data=json_data, session=session)
    return await response.json()

async def make_multiple_requests(urls: list, method: str = 'GET', **kwargs) -> list:
    """
    Выполняет несколько асинхронных запросов одновременно
    
    Args:
        urls (list): Список URL для запроса
        method (str): HTTP метод ('GET', 'POST', 'PATCH')
        **kwargs: Дополнительные параметры для запросов
        
    Returns:
        list: Список ответов
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for url in urls:
            if method.upper() == 'GET':
                task = make_get_request(url, session=session, **kwargs)
            elif method.upper() == 'POST':
                task = make_post_request(url, session=session, **kwargs)
            elif method.upper() == 'PATCH':
                task = make_patch_request(url, session=session, **kwargs)
            else:
                raise ValueError(f"Неподдерживаемый HTTP метод: {method}")
            
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
