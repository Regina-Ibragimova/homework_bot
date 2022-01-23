from http import HTTPStatus
import logging
import os
import time

import telegram
import requests
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    # filename='main.log',
    # filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)


def send_message(bot, message):
    """Отправка сообщения об ошибке в лог и в Телеграмм."""
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info('Успешная отправка сообщения.')


def get_api_answer(current_timestamp):
    """Запрос к APIПрактикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == HTTPStatus.OK:
        logger.info('Успешное получение ответа от Практикума')
        return response.json()
    elif response.status_code == HTTPStatus.REQUEST_TIMEOUT:
        raise SystemError(f'Ошибка код {response.status_code}')
    elif response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        raise SystemError(f'Ошибка код {response.status_code}')
    else:
        raise SystemError(
            f'Недоступен Эндпоинт, код {response.status_code}')


def check_response(response):
    """Проверка содержимого ответа."""
    if type(response) == dict:
        if response['current_date'] is not None:
            response['current_date']
            if response['homeworks'] is not None:
                homeworks = response['homeworks']
                if response('homeworks') == list:
                    return homeworks
                else:
                    raise TypeError('Нет списка')
            else:
                raise KeyError('Нет ключа homeworks')
        else:
            raise KeyError('Нет ключа current_date')
    else:
        raise TypeError('Нет словаря')


def parse_status(homework):
    """Праверка ключей в ответе."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_name is None or homework_status is None:
        if homework_status in HOMEWORK_STATUSES:
            verdict = HOMEWORK_STATUSES[homework_status]
            return ('Изменился статус проверки работы'
                    + f'{homework_name}. {verdict}')
        else:
            raise KeyError('нет данных о статусе')
    else:
        raise KeyError('нет данных о статусе или работе')


def check_tokens():
    """Праверка обязательных переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        logger.critical('Отсутствие обязательных переменных окружения')
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise SystemExit('Ошибка импорта токенов')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            homework = get_api_answer(current_timestamp)
            current_timestamp = homework.get('current_date')
            homework = check_response(homework)
            if len(homework) > 0:
                homework = parse_status(homework[0])
                if homework is not None:
                    send_message(bot, homework)
            else:
                logger.debug('нет новых статусов')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()
