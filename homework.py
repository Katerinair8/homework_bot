import time
import logging
import sys
import os
import requests
from http import HTTPStatus
from dotenv import load_dotenv

from exceptions import (
    NotSendingError, EmptyListException, ListException,
    AnswerException, SendMessageException)
from telegram import Bot, error

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(filename='log.log', mode='w')
    ],
    format='%(asctime)s, %(name)s, %(levelname)s, %(message)s')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    logging.debug("Начали отправку сообщения")
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except error.TelegramError:
        raise SendMessageException("Ошибка отправки соощения в Telegram")
    else:
        logging.info('Удачная отправка сообщения в Telegram')


def get_api_answer(current_timestamp: int) -> dict:
    """Делает запрос к эндпоинту API-сервиса."""
    params = {'from_date': current_timestamp}
    logging.info("Направляем запрос к API")
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise AnswerException(
                f"Ошибка при запросе к Api."
                f"Статус ответа: {response.status_code}"
            )
    except Exception as error:
        raise Exception(f"Ошибка работы программы: {error}")
    else:
        return response.json()


def check_response(response: dict) -> list:
    """Проверяет ответ API на корректность."""
    logging.debug("Начали проверку ответа сервера")
    homeworks = response["homeworks"]
    if not isinstance(response, dict):
        raise TypeError("В функцию check_response был передан не словарь")
    elif homeworks is None:
        raise EmptyListException('Отсутствуют ожидаемые ключи в ответе API')
    elif response.get("current_date") is None:
        raise ListException("Отсутствует ключ 'current_date' в словаре")
    elif not isinstance(homeworks, list):
        raise KeyError(
            f"Параметр 'howerworks' - не список. Тип: {type(homeworks)}")
    else:
        return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает статус конкретной домашки."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Ошибка статуса {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    if not check_tokens():
        sys.exit(
            message="Отсутствует обязательная переменная окружения"
        )
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                message = "Сервер вернул пустой список"
            else:
                old_message = ""
                message = parse_status(homeworks[0])
                if message != old_message:
                    old_message = message
                else:
                    message = "Статус проверки работы не изменился"
                    logging.debug(message)
            send_message(bot, message)
            current_timestamp = response.get(
                "current_date",
                current_timestamp
            )
        except NotSendingError as error:
            logging.error(error, exc_info=error)
        except AnswerException:
            logging.debug(
                response.status_code,
                response.reason,
                response.reason,
                response.text,
                ENDPOINT,
                HEADERS,
                response.params
            )
        except SystemExit as error:
            logging.critical(error, exc_info=error)
            send_message(bot, error)
        except Exception as error:
            logging.error(error, exc_info=error)
            send_message(bot, error)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
