FROM python:3.7-slim as python-base

RUN         apt -y update && apt -y dist-upgrade && apt -y autoremove
RUN         apt -y install nginx
RUN         apt-get install -y cron
RUN         apt install nano
RUN         apt install vim
# poetry export로 생성된 requirements.txt를 적절히 복사
COPY        ./requirements.txt /tmp/
COPY        ./poetry.lock /tmp/
COPY        ./pyproject.toml /tmp/

ENV         PYTHONUNBUFFERED=1 \
            # prevents python creating .pyc files
            PYTHONDONTWRITEBYTECODE=1 \
            \
            # pip
            PIP_NO_CACHE_DIR=off \
            PIP_DISABLE_PIP_VERSION_CHECK=on \
            PIP_DEFAULT_TIMEOUT=100 \
            \
            # poetry
            # https://python-poetry.org/docs/configuration/#using-environment-variables
            POETRY_VERSION=1.0.3 \
            # make poetry install to this location
            POETRY_HOME="/opt/poetry" \
            # make poetry create the virtual environment in the project's root
            # it gets named `.venv`
            POETRY_VIRTUALENVS_IN_PROJECT=true \
            # do not ask any interactive question
            POETRY_NO_INTERACTION=1 \
            \
             # paths
                                     # this is where our requirements + virtual environment will live
            PYSETUP_PATH="/opt/pysetup" \
            VENV_PATH="/opt/pysetup/.venv"

ENV         PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

            # `builder-base` stage is used to build deps + create our virtual environment


FROM        python-base as builder-base

RUN         apt-get update  && apt-get install --no-install-recommends -y \
            # deps for installing poetry
            curl \
            # deps for building python deps
            build-essential



# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN         curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# copy project requirement files here to ensure they will be cached.
WORKDIR     $PYSETUP_PATH
COPY        poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN         poetry install --no-dev
# `development` image is used during development / testing
FROM        python-base as development
ENV         FASTAPI_ENV=development
WORKDIR     $PYSETUP_PATH
#
# copy in our built poetry + venv
COPY        --from=builder-base $POETRY_HOME $POETRY_HOME
COPY        --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# quicker install as runtime deps are already installed
RUN         poetry install




## 소스코드 복사
COPY        . /srv/binanace-coin
WORKDIR     /srv/binanace-coin/app
#
## Nginx설정파일을 복사, 기본 서버 설정 삭제
RUN         rm /etc/nginx/sites-enabled/default
RUN         cp /srv/binanace-coin/.config/local_dev/bit.nginx /etc/nginx/sites-enabled/
#
## 로그폴더 생성
RUN         mkdir /var/log/gunicorn
#
CMD         /bin/bash