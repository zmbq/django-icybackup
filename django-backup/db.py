import os
from django.core.management.base import CommandError

def backup(database, outfile):
    engine = database['ENGINE']
    if 'mysql' in engine:
        __mysql_backup(database, outfile)
    elif engine in ('postgresql_psycopg2', 'postgresql') or 'postgresql' in engine:
        __postgresql_backup(database, outfile)
    elif 'sqlite3' in engine:
        __sqlite_backup(database, outfile)
    else:
        raise CommandError('Backup in %s engine not implemented' % engine)

def __sqlite_backup(database, outfile):
    os.system('cp %s %s' % (database['NAME'], outfile))

def __mysql_backup(database, outfile):
    args = []
    if 'USER' in database:
        args += ["--user=%s" % database['USER']]
    if 'PASSWORD' in database:
        args += ["--password=%s" % database['PASSWORD']]
    if 'HOST' in database:
        args += ["--host=%s" % database['HOST']]
    if 'PORT' in database:
        args += ["--port=%s" % database['PORT']]
    args += [database['NAME']]

    os.system('mysqldump %s > %s' % (' '.join(args), outfile))

def __postgresql_backup(database, outfile):
    args = []
    if 'USER' in database:
        args += ["--username=%s" % database['USER']]
    if 'HOST' in database:
        args += ["--host=%s" % database['HOST']]
    if 'PORT' in database:
        args += ["--port=%s" % database['PORT']]
    if 'NAME' in database:
        args += [database['NAME']]
    if 'PASSWORD' in database:
        command = 'PGPASSWORD=%s pg_dump -Ox %s > %s' % (database['PASSWORD'], ' '.join(args), outfile)
    else:
        command = 'pg_dump %s -w > %s' % (' '.join(args), outfile)
    os.system(command)
