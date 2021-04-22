daemon = False
chdir = '/srv/binanace-coin/app'
bind = 'unix:/run/bit.sock'
accesslog = '/var/log/gunicorn/bit-coin-access.log'
errorlog = '/var/log/gunicorn/bit-coin-error.log'
capture_output = True