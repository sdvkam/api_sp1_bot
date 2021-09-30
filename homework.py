import logging
import os
import sys
import time
from logging import FileHandler

import requests
import telegram
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler_file = FileHandler('my_logger.log', mode='w')
handler_file.setFormatter(formatter)
logger.addHandler(handler_file)
handler_console = logging.StreamHandler(sys.stdout)
handler_console.setFormatter(formatter)
logger.addHandler(handler_console)

bot = telegram.Bot(TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    elif homework['status'] == 'reviewing':
        verdict = 'Ваша работа взята на ревью'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(url, headers=headers, params=payload)
        return homework_statuses.json()
    except requests.exceptions.RequestException as e:
        return f'Проблема с доступом к API с домашкой: {e}'
    except Exception as e:
        return f'При доступе к API с домашкой произошли непонятки: {e}'


def check_format_api_answer(api_anwser):
    list_right_api_status = ['rejected', 'reviewing', 'approved']
    try:
        if len(api_anwser['homeworks']) == 0:
            return True
        if not isinstance(api_anwser['homeworks'][0]['homework_name'], str):
            return False
        if not isinstance(api_anwser['homeworks'][0]['status'], str):
            return False
        if api_anwser['homeworks'][0]['status'] not in list_right_api_status:
            return False
        return True
    except Exception:
        return False


def send_message(message):
    try:
        return bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        return f'Сообщение не отправлено из-за ошибки: {e}'


def main():
    current_timestamp = int(time.time())
    while True:
        logger.debug('Бот проснулся!')
        try:
            list_homework_status = get_homeworks(current_timestamp)
            if isinstance(list_homework_status, str):
                logger.error(list_homework_status)
            elif not check_format_api_answer(list_homework_status):
                logger.error('Неверный ответ сервера')
            elif len(list_homework_status['homeworks']) > 0:
                last_howmework = list_homework_status['homeworks'][0]
                message = parse_homework_status(last_howmework)
                result = send_message(message)
                if isinstance(result, str):
                    logger.error(result)
                else:
                    logger.info(f'Сообщение отправлено: {message}')
                current_timestamp = int(time.time())
            time.sleep(20 * 60)
        except Exception as e:
            message = f'Бот упал с ошибкой: {e}'
            logger.error(message)
            send_message(message)
            time.sleep(5)


if __name__ == '__main__':
    main()
