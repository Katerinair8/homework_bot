import time
import logging
import sys
import os
import requests
from http import HTTPStatus
from dotenv import load_dotenv

from exceptions import EmptyListException, ListException, AnswerException
from telegram import Bot

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    format='%(asctime)s, %(name)s, %(levelname)s, %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        chat_id = TELEGRAM_CHAT_ID
        message = 'Обновился статус домашки!'
        bot.send_message(chat_id, message)
        logging.info('Удачная отправка сообщения в Telegram')
    except Exception as error:
        logging.error(
            f'Неудачная попытка отправить сообщение в Telegram: {error}')
        return bot.send_message(chat_id, message)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise AnswerException('Не получилось сделать запрос к API')
        else:
            return response.json()
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')


def check_response(response):
    """Проверяет ответ API на корректность."""
    homeworks = response['homeworks']
    if homeworks is None:
        error = ('Отсутствуют ожидаемые ключи в ответе API')
        logging.error(error)
        raise EmptyListException(error)
    elif not isinstance(homeworks, list):
        raise ListException
    else:
        logging.info(response['homeworks'])
        return response['homeworks']


def parse_status(homework):
    """Извлекает статус конкретной домашки."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Ошибка статуса {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    for token in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        if token is None:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {token}')
            return False
    return True


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            send_message(bot, message)

            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)

        except Exception as error:
            logging.error(f'Ошибка при запросе к API: {error}')
            logging.error(f'Отсутствуют ожидаемые ключи в ответе API: {error}')
            logging.error(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)
        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
