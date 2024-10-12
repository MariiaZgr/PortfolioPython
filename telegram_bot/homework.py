import logging
import os
from sys import stdout
import time

import requests
import telegram
from http import HTTPStatus
from dotenv import load_dotenv
from exceptions import EndpointNotAvailableError, RequestExceptionError
from exceptions import NoHomeworkInResponseError, HomeworksTypeError

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stdout)
logger.addHandler(handler)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 10 * 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Бот отправил сообщение: {message}')
    except Exception as e:
        logger.error(f'Бот не смог отправить сообщение: {e}')


def get_api_answer(current_timestamp):
    """Запрос API."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except RequestExceptionError as error:
        message = f'Код ответа API: {error}'
        raise RequestExceptionError(message) from error
    if response.status_code != HTTPStatus.OK:
        message = (
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}')
        raise EndpointNotAvailableError(message)
    return response.json()


def check_response(response):
    """Проверка данных API."""
    if not isinstance(response, dict):
        message = 'API не словарь'
        raise TypeError(message)

    if 'homeworks' not in response:
        message = 'Список домашних работ отсутствует в ответе API'
        raise NoHomeworkInResponseError(message)

    if not isinstance(response['homeworks'], list):
        message = 'Список домашних работ не список'
        raise HomeworksTypeError(message)

    homework = response.get('homeworks')

    return homework


def parse_status(homework):
    """Получение статуса работы."""
    dict = ['status', 'homework_name']
    for key in dict:
        if key not in homework:
            raise KeyError(f'Отсутствует ключ {key} в ответе API')
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Неизвестный статус работы: {homework_status}')
    homework_name = homework['homework_name']
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    message = (
        'Отсутствует обязательная переменная окружения. Программа остановлена')
    if PRACTICUM_TOKEN is None:
        logger.critical(f'{message} PRACTICUM_TOKEN')
    if TELEGRAM_TOKEN is None:
        logger.critical(f'{message} TELEGRAM_TOKEN')
    if TELEGRAM_CHAT_ID is None:
        logger.critical(f'{message} TELEGRAM_CHAT_ID')
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0
    previous_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            if 'current_date' in response:
                current_timestamp = response['current_date']
                homework = check_response(response)

            if homework:
                message = parse_status(homework[0])
                if previous_message != message:
                    send_message(bot, message)
                    previous_message = message
            else:
                logger.debug('Список домашних работ пуст')

            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(funcName)s, %(lineno)s, %(levelname)s, %(message)s',
        encoding='UTF-8')
    main()
