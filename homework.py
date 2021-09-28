import logging
import os
import time
from logging import FileHandler

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import ConnectionError

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logger = logging.getLogger(__name__)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)
handler = FileHandler('my_logger.log', mode='w')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    homework_statuses = requests.get(url, headers=headers, params=payload)
    return homework_statuses.json()


def send_message(message):
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())
    while True:
        logger.debug('Бот проснулся!')
        try:
            list_homework_status = get_homeworks(current_timestamp)
            for one_homework in list_homework_status['homeworks']:
                message = parse_homework_status(one_homework)
                send_message(message)
                logger.info(f'Сообщение отправлено: {message}')
                current_timestamp = int(time.time())
            time.sleep(5 * 60)
        except ConnectionError as e:
            logger.error(f'Нет связи: {e}')
            time.sleep(5)
        except Exception as e:
            message = f'Бот упал с ошибкой: {e}'
            logger.error(message)
            send_message(message)
            time.sleep(5)


if __name__ == '__main__':
    main()
