#!/usr/bin/env python

import os
import subprocess
from pathlib import Path

DOCKER_ID = 'johnkdo2020'
DOCKER_IMAGE_NAME = 'bit-up'
DOCKER_IMAGE_TAG = f'{DOCKER_ID}/{DOCKER_IMAGE_NAME}'
DOCKER_OPTIONS = [
    ('--rm', ''),
    ('-it', ''),
    ('-d', ''),
    ('-p', '80:80'),
    # ('-p', '5432:5432'),
    ('--name', 'bit-up'),
    # ('-v', '/etc/letsencrypt:/etc/letsencrypt'),
]

USER = 'ubuntu'
HOST = '13.209.232.17'
TARGET = f'{USER}@{HOST}'
HOME = str(Path.home())
APPLICATION_NAME = 'binanace-coin'
IDENTITY_FILE = os.path.join(HOME, '.ssh', 'bitup.pem')
SOURCE = os.path.join(HOME, 'workspace', 'python', 'data-science', f'{APPLICATION_NAME}')
SECRETS_FILE = os.path.join(SOURCE, 'secrets.json')


def run(cmd, ignore_error=False):
    process = subprocess.run(cmd, shell=True)
    if not ignore_error:
        process.check_returncode()


def ssh_run(cmd, ignore_error=False):
    run(f'ssh -o StrictHostKeyChecking=no -i {IDENTITY_FILE} {TARGET} -C {cmd}', ignore_error=ignore_error)


def local_build_push():
    run(f'poetry export -f requirements.txt > requirements.txt')
    run(f'sudo docker build -t {DOCKER_IMAGE_TAG} .')
    run(f'sudo docker push {DOCKER_IMAGE_TAG}')


def server_init():
    ssh_run(f'sudo apt update')
    ssh_run(f'sudo DEBIAN_FRONTEND=noninteractive apt dist-upgrade -y')
    ssh_run(f'sudo apt -y install docker.io')


def server_pull_run():
    ssh_run(f'sudo docker stop {DOCKER_IMAGE_NAME}', ignore_error=True)
    ssh_run(f'sudo docker pull {DOCKER_IMAGE_TAG}')
    ssh_run('sudo docker run {options} {tag} /bin/bash'.format(
        options=' '.join([
            f'{key} {value}' for key, value in DOCKER_OPTIONS
        ]),
        tag=DOCKER_IMAGE_TAG,
    ))


# 3. Host에서 EC2로 secrets.json을 전송, EC2에서 Container로 다시 전송
def copy_secrets():
    run(f'scp -i {IDENTITY_FILE} {SECRETS_FILE} {TARGET}:/tmp', ignore_error=True)
    ssh_run(f'sudo docker cp /tmp/secrets.json {DOCKER_IMAGE_NAME}:/srv/{APPLICATION_NAME}')
    print('coppy secrets!!!!!!!!')


def server_cmd():
    ssh_run(f'sudo docker exec {DOCKER_IMAGE_NAME} /usr/sbin/nginx -s stop', ignore_error=True)
    print('sudo docker nginx stop')

    ssh_run(f'sudo docker exec {DOCKER_IMAGE_NAME} python manage.py collectstatic --noinput')
    ssh_run(f'sudo docker exec {DOCKER_IMAGE_NAME} python manage.py crontab add')
    # ssh_run(f'sudo docker exec {DOCKER_IMAGE_NAME} python manage.py crontab show')
    ssh_run(f'sudo docker exec -it -d {DOCKER_IMAGE_NAME} '
            f'supervisord -c /srv/{APPLICATION_NAME}/.config/local_dev/supervisord.conf -n')
    print('여기까지 문제 없음')


if __name__ == '__main__':
    try:
        local_build_push()
        server_init()
        server_pull_run()
        copy_secrets()
        server_cmd()
    except subprocess.CalledProcessError as e:
        print('deploy Error')
        print(' cmd:', e.cmd)
        print(' return code:', e.returncode)
        print(' output:', e.output)
        print(' stdout:', e.stdout)
        print(' stderr:', e.stderr)
