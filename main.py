import re
import os
import time
import json
import uuid
import string
import random
import ctypes
import threading
import tls_client

from loguru import logger
from datetime import datetime, timedelta




pinneaples_collected = 0
cfg = json.load(open('./config.json', encoding='utf-8')) # чтение конфига


start_time = datetime.now()  # Track the start time

def display_stats():
    """Display collected pineapples statistics for each account."""
    logger.info("Статистика собранных ананасов:")
    for account_name, count in accounts_stats.items():
        logger.info(f"[{account_name}] Собрано ананасов: {count}")

    # Calculate total runtime
    end_time = datetime.now()
    total_duration = end_time - start_time
    total_minutes = total_duration.total_seconds() / 60
    total_hours = total_duration.total_seconds() / 3600
    total_days = total_duration.total_seconds() / 86400

    # Calculate average pineapples per account
    total_pineapples = sum(accounts_stats.values())
    num_accounts = len(accounts_stats)

    if num_accounts > 0:
        avg_per_account = total_pineapples / num_accounts
    else:
        avg_per_account = 0

    # Calculate averages per time unit
    if total_minutes > 0:
        avg_per_minute = avg_per_account / total_minutes
    else:
        avg_per_minute = 0

    if total_hours > 0:
        avg_per_hour = avg_per_account / total_hours
    else:
        avg_per_hour = 0

    if total_days > 0:
        avg_per_day = avg_per_account / total_days
    else:
        avg_per_day = 0

    logger.info(f"Общее время работы: {total_duration}")
    logger.info(f"Среднее количество ананасов на аккаунт: {avg_per_account:.2f}")
    logger.info(f"Среднее количество ананасов в минуту: {avg_per_minute:.2f}")
    logger.info(f"Среднее количество ананасов в час: {avg_per_hour:.2f}")
    logger.info(f"Среднее количество ананасов в день: {avg_per_day:.2f}")



# Initialize stats for each account
accounts_stats = {account["account_name"]: 0 for account in cfg["Accounts"]}



def session(config: dict) -> tls_client.Session:
    """Создание tls-client сессии"""
    session = tls_client.Session(client_identifier='okhttp4_android_13') 
    session.headers = {
            "Accept": "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=UTF-8",
            "Host": "api.ozon.ru",
            "MOBILE-GAID": str(uuid.uuid4()),
            "MOBILE-LAT": "0",
            "User-Agent": "ozonapp_android/17.40.1+2518",
            "x-o3-app-name": "ozonapp_android",
            "x-o3-app-version": config["x-o3-app-version"],
            "x-o3-device-type": "mobile",
            "x-o3-fp": Utils.generate_x_o3(),
            "x-o3-sample-trace": "false"
        }  
        
    session.cookies.set("x-o3-app-name", "ozonapp_android")
    session.cookies.set("__Secure-access-token", config["__Secure-access-token"])
    session.cookies.set("__Secure-refresh-token", config["__Secure-refresh-token"])
    if config["abt_data"]:
        session.cookies.set("abt_data", config["abt_data"])
        
    if config["use_proxy"]:
        session.proxies = f"http://{config["proxy"]}"
    
    return session


class Utils():
    @staticmethod
    def generate_x_o3() -> str: # Генерация x-o3-fp заголовка
        return f"1.{''.join(random.choices(string.hexdigits[:16].lower(), k=16))}"
    
    @staticmethod
    def extract(text: str):
        return re.search(r'"hash_value":"(\d+)"', text).group(1), re.search(r'"product_id":"(\d+)"', text).group(1)
    
    @staticmethod
    def sleep_func(account_name: str, error_403=False) -> None:
        """Задержка в софте"""
        if error_403:
            if cfg["Error_handling"]["sleep_if_403_status_code"]:
                sleep_time = random.randint(cfg["Error_handling"]["sleep_time_min"], cfg["Error_handling"]["sleep_time_max"])
                logger.info(f"[{account_name}] [STATUS 403] Аккаунт ушёл в спячку на {sleep_time} минут.")
                time.sleep(sleep_time * 60)
                
            return
        
        if cfg["Sleep_settings"]["sleep_between_pinneaples"]: # Пауза после каждого ананаса
            sleep_time = random.randint(cfg["Sleep_settings"]["min_delay"], cfg["Sleep_settings"]["max_delay"])
            logger.info(f'[{account_name}] Ожидание паузы {sleep_time} секунд.')
            time.sleep(sleep_time)
                            
        if cfg["Sleep_settings"]["afk"]: # Рандомная спячка после сбора
            number = random.randint(1, 100)
            if number <= cfg["Sleep_settings"]["chance_to_afk"]:
                sleep_time = random.randint(cfg["Sleep_settings"]["afk_time_min"], cfg["Sleep_settings"]["afk_time_max"])
                logger.info(f"[{account_name}] Ушел в спячку на {sleep_time} минут.")
                time.sleep(sleep_time * 60)
                                    
    @staticmethod
    def set_title():
        """Название консоли"""
        global pinneaples_collected
        start_time = datetime.now()
        if os.name == 'nt':    
            while True:
                title = f"v1.04 Фармер Ананасов | Используется аккаунтов: {len(cfg["Accounts"])} | Собрано ананасов: {pinneaples_collected} | Времени прошло: {datetime.now() - start_time}"
                ctypes.windll.kernel32.SetConsoleTitleW(title)
                time.sleep(0.2)
                
    
class Ozon():
    def __init__(self, config: dict) -> None:
        self.session = session(config)
        self.account_name = config["account_name"]
        self.config = config
    
    def load_cycle(self) -> None:
       """Посещение страницы акции"""
       while True:
           try:
               for i in range(3):
                   self.session.get("https://www.ozon.ru/landing/pineapple?perehod=pineapple_alert")

               break
           except Exception as e:
               logger.warning(f'Исключение: {e}')
               time.sleep(1)
               continue
    
    def get_pinneaple_product(self) -> None:
        """Функция получения товара с ананасом"""
        global pinneaples_collected
        while True:
            try:
                value = random.randint(11111111, 999999999)
                params = {
                    "url": f"/products/{value}/?layout_container=pdppage2copy&layout_page_index=2"
                }
                        
                response = self.session.get("https://api.ozon.ru/composer-api.bx/page/json/v2", params=params)
                if response.status_code == 200:
                    if "hash" in response.text:
                        clean_text = response.text.replace('\\"', '"')
                        payload = {"product_id":Utils.extract(clean_text)[1],"hash_value":Utils.extract(clean_text)[0]}
                        self.collect_pinneaple(payload)
                
                elif response.status_code == 403:
                    logger.error(f'[{self.account_name}] Ошибка при просмотре товара (403) -> возможно невалид куки.')
                    self.session = session(self.config)
                    self.load_cycle()
                    continue
                    
                elif response.status_code == 404:
                    continue
                    
                else:
                    logger.error(f'[{self.account_name}] Неизвестная ошибка просмотра карточки товара ({response.status_code}) -> {response.text}.')   
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Исключение: {e}")  
                time.sleep(1)   
                continue      
               
    def collect_pinneaple(self, payload: dict) -> None:
        """Сбор ананасов"""
        global pinneaples_collected
        while True:
            try:
                resp = self.session.post("https://api.ozon.ru/composer-api.bx/_action/v2/collapseWidget", json=payload)
                if resp.status_code == 200:
                    pinneaples_collected += 1
                    accounts_stats[self.account_name] += 1

                    logger.success(f"[{self.account_name}] Успешно залутал ананас: {resp.json()['data']['notificationBar']['title']}.")
                    Utils.sleep_func(self.account_name)
                
                elif resp.status_code == 403:
                    logger.error(f'[{self.account_name}] Ошибка получения ананаса (403) -> рейтлимит/невалид куки')
                    Utils.sleep_func(self.account_name, True)
                    
                else:
                    logger.error(f'[{self.account_name}] Неизвестная ошибка при получении ананаса ({resp.status_code}) -> {resp.text}')
                    time.sleep(1)

                return
            except Exception as e:
                logger.warning(f"Исключение: {e}")
                time.sleep(1)
                continue
                    
    
def process_account(account: dict):
    """Поток для каждого аккаунта"""
    ozon = Ozon(account)
    ozon.load_cycle()
    ozon.get_pinneaple_product()

def main():
    """Фукнция запуска"""
    try:
        threading.Thread(target=Utils.set_title).start()
        threads = []
        for account in cfg["Accounts"]:
            thread = threading.Thread(target=process_account, args=(account,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    except Exception as e:
        logger.warning(f"Исключение: {e}")

    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Получен сигнал прерывания (Ctrl+C).")
        display_stats()
        os._exit(0)  # Exit the script

if __name__ == "__main__":
    main()
    
