# 나중에 python 으로 설정해주기

d=$(date "+%Y%m%d%H%M")

./app/manage.py crontab remove

cp ./app/db.sqlite3 ./app/db_backup/"$d"_db_backup.sqlite3

./migration_init.sh

./app/manage.py makemigrations
./app/manage.py migrate
./app/manage.py crontab add
