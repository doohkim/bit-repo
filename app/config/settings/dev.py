from .base import *

DEBUG = True

WSGI_APPLICATION = 'config.wsgi.dev.application'
ALLOWED_HOSTS += [
    '*',
]
# INSTALLED_APPS += [
#
# ]
# Database
DATABASE = SECRETS_FULL['DATABASE']['default']
DATABASES = {
    'default': {
        "ENGINE": DATABASE['ENGINE'],
        "HOST": DATABASE['HOST'],
        "PORT": DATABASE['PORT'],
        "NAME": DATABASE['NAME'],
        "USER": DATABASE['USER'],
        "PASSWORD": DATABASE['PASSWORD'],
    }
}
# 이거는 crontab -e 나노에서 주석도 제거하고 직접 설정해줘야 하느거 같아.....왜 그런그저ㅣ...
# 배포하고나서 한번 테스트 해볼 필요가 있어!!!
CRONTAB_COMMAND_SUFFIX = '2>&1'
CRONJOBS = [
    ('* * * * *', 'cron.search_binance', '>>' + BASE_DIR + '/log/binance_log.log'),
    ('* * * * *', 'cron.search_up_bit_first', '>>' + BASE_DIR + '/log/first_bit_up.log'),
    ('* * * * *', 'cron.search_up_bit_second', '>>' + BASE_DIR + '/log/second_bit_up.log'),
    ('* * * * *', 'cron.search_up_bit_third', '>>' + BASE_DIR + '/log/third_bit_up.log'),
    ('* * * * *', 'cron.save_execute_table', '>>' + BASE_DIR + '/log/save_execute_table.log'),
]
