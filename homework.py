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

WRONG_NAMES_HOMEWORK = [None, '']
RIGHT_STATUS_HOMEWORK_ANSWER_BOT = {
    'rejected': 'К сожалению, в работе нашлись ошибки.',
    'reviewing': 'Ваша работа взята на ревью',
    'approved': 'Ревьюеру всё понравилось, работа зачтена!'}

EXCEPTIONS_OUR_BOT = {
    'wrong_format_homework': 'Неверный ответ сервера: формат домашней работы',
    'wrong_format_json': 'Неверный ответ сервера: формат Json',
    'not_access_by_api': 'Проблема с доступом к API с домашкой',
    'something_with_api': 'При доступе к API с домашкой произошли непонятки',
    'error_send': 'Сообщение не отправлено из-за ошибки'
}

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


def is_valid_format_homework(homework):
    if 'homework_name' not in homework or 'status' not in homework:
        return False
    if homework['homework_name'] in WRONG_NAMES_HOMEWORK:
        return False
    if homework['status'] not in RIGHT_STATUS_HOMEWORK_ANSWER_BOT:
        return False
    return True


def parse_homework_status(homework):
    if not is_valid_format_homework(homework):
        raise Exception(EXCEPTIONS_OUR_BOT['wrong_format_homework'])

    homework_name = homework['homework_name']
    verdict = RIGHT_STATUS_HOMEWORK_ANSWER_BOT[homework['status']]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    url = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(url, headers=headers, params=payload)
        return homework_statuses.json()

    except requests.exceptions.RequestException as e:
        raise Exception(EXCEPTIONS_OUR_BOT['not_access_by_api'] + f': {e}')
    except Exception as e:
        raise Exception(EXCEPTIONS_OUR_BOT['something_with_api'] + f': {e}')


def send_message(message):
    try:
        return bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        # don't want to get Exception again, if message with error don't send
        if not message.startswith('Бот упал с ошибкой:'):
            raise Exception(EXCEPTIONS_OUR_BOT['error_send'] + f': {e}')


def main():
    current_timestamp = int(time.time())
    count_atempts_after_error = 0
    while True:
        logger.debug('Бот проснулся!')
        try:
            list_homework_status = get_homeworks(current_timestamp)
            if 'homeworks' not in list_homework_status:
                raise Exception(EXCEPTIONS_OUR_BOT['wrong_format_json'])
            elif len(list_homework_status['homeworks']) > 0:
                last_howmework = list_homework_status['homeworks'][0]
                message = parse_homework_status(last_howmework)
                send_message(message)
                logger.info(f'Сообщение отправлено: {message}')
            current_timestamp = int(time.time())
            """ Ваше замечание:
                Перед тем как отправиться спать лучше обновлять timestamp.
                У полученной домашней работы есть ключ current_date

                Насколько я понимаю, надо обнолвять current_timestamp после
                удачной проверки ответа API
                и затем удачной посылки сообщения боту
                или после выяснения что посылать ничего не надо.
                и нам нужно текущее время на момент удачи,
                а не время последней проверенной работы.
            """
            logger.debug('Бот заснул!')
            time.sleep(20 * 60)
        except Exception as e:
            err = f'Бот упал с ошибкой: {e}'
            logger.error(err)
            send_message(err)
            if count_atempts_after_error < 3:
                logger.debug('Бот прикорнул!')
                count_atempts_after_error += 1
                time.sleep(5)
            else:
                logger.debug('Бот заснул!')
                count_atempts_after_error = 0
                time.sleep(20 * 60)


if __name__ == '__main__':
    main()
