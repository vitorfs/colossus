#!/bin/bash

su - colossus -c "git -C ~/colossus pull origin master"

migrations="$(/home/colossus/venv/bin/python /home/colossus/colossus/manage.py showmigrations --plan | grep -v '\[X\]')"

if [[ $migrations = *[!\ ]* ]]; then
  githash="$(git -C /home/colossus/colossus rev-parse --short HEAD^1)"
  now=`date +%Y%m%d%H%M%S`
  dumpfile="colossus_db_backup_${githash}_${now}.sql"
  su - postgres -c "pg_dump colossus > ${dumpfile}"
  echo "Created database backup (${dumpfile}) due to changes on schema."
else
  echo "Skipped backup. No changes on the database schema."
fi

su - colossus -c "~/venv/bin/pip install -r ~/colossus/requirements.txt"
su - colossus -c "~/venv/bin/python ~/colossus/manage.py migrate"
su - colossus -c "~/venv/bin/python ~/colossus/manage.py collectstatic --noinput"

sudo supervisorctl restart colossus_gunicorn
sudo supervisorctl restart colossus_celery_worker
sudo supervisorctl restart colossus_celery_beat

exit 0
