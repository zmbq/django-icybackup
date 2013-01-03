import os
from django.core.management.base import CommandError
from tempfile import mkstemp
from subprocess import check_call
from shutil import copy
from django.conf import settings

BACKUP = 1
RESTORE = 2

MYSQL_BIN = settings.get('MYSQL_BIN', 'mysql')
MYSQLDUMP_BIN = settings.get('MYSQLDUMP_BIN', 'mysqldump')
PG_DUMP_BIN = settings.get('PG_DUMP_BIN', 'pg_dump')
PG_RESTORE_BIN = settings.get('PG_RESTORE_BIN', 'pg_restore')

def _database_dict_from_settings(settings):
    if hasattr(settings, 'DATABASES'):
        database_list = settings.DATABASES
    else:
        # database details are in the old format, so convert to the new one
        database_list = {
            'default': {
                'ENGINE': settings.DATABASE_ENGINE,
                'NAME': settings.DATABASE_NAME,
                'USER': settings.DATABASE_USER,
                'PASSWORD': settings.DATABASE_PASSWORD,
                'HOST': settings.DATABASE_HOST,
                'PORT': settings.DATABASE_PORT,
            }
        }
    return database_list

def backup_to(settings, dir):
    for name, database in _database_dict_from_settings(settings).iteritems():
        do(BACKUP, database, os.path.join(dir, name))

def restore_from(settings, dir):
    for name, database in _database_dict_from_settings(settings).iteritems():
        do(RESTORE, database, os.path.join(dir, name))

def do(action, database, f):
    engine = database['ENGINE']
    if 'mysql' in engine:
        __mysql(action, database, f)
    elif 'postgresql' in engine:
        __postgresql(action, database, f)
    elif 'sqlite3' in engine:
        __sqlite(action, database, f)
    else:
        raise CommandError('{} in {} engine not implemented'.format('Backup' if action == BACKUP else 'Restore', engine))

def __sqlite(action, database, f):
    if action == BACKUP:
        copy(database['NAME'], f)
    elif action == RESTORE:
        copy(f, database['NAME'])

def __mysql(action, database, f):
    if action == BACKUP:
        command = [MYSQLDUMP_BIN]
    elif action == RESTORE:
        command = [MYSQL_BIN]
    
    if 'USER' in database:
        command += ["--user=%s" % database['USER']]
    if 'PASSWORD' in database:
        command += ["--password=%s" % database['PASSWORD']]
    if 'HOST' in database:
        command += ["--host=%s" % database['HOST']]
    if 'PORT' in database:
        command += ["--port=%s" % database['PORT']]
    command += [database['NAME']]
    
    if action == BACKUP:
        with open(f, 'w') as fo:
            check_call(command, stdout=fo)
    elif action == RESTORE:
        with open(f, 'r') as fo:
            check_call(command, stdin=fo)

def __postgresql(action, database, f):
    if action == BACKUP:
        command = [PG_DUMP_BIN, '--format=c']
    elif action == RESTORE:
        command = [PG_RESTORE_BIN, '-Oxc']
    
    if 'USER' in database and database['USER']:
        command.append("--username={}".format(database['USER']))
    if 'HOST' in database and database['HOST']:
        command.append("--host={}".format(database['HOST']))
    if 'PORT' in database and database['PORT']:
        command.append("--port={}".format(database['PORT']))
    if 'NAME' in database and database['NAME']:
        if action == RESTORE:
            command.append('--dbname={}'.format(database['NAME']))
        else:
            command.append(database['NAME'])
    
    if 'PASSWORD' in database and database['PASSWORD']:
        # create a pgpass file that always returns the same password, as a secure temp file
        password_fd, password_path = mkstemp()
        password_file = os.fdopen(password_fd, 'w')
        password_file.write('*:*:*:*:{}'.format(database['PASSWORD']))
        password_file.close()
        os.environ['PGPASSFILE'] = password_path
    else:
        command.append('-w')
    
    if action == BACKUP:
        with open(f, 'w') as fo:
            check_call(command, stdout=fo)
    elif action == RESTORE:
        with open(f, 'r') as fo:
            check_call(command, stdin=fo)
        
    # clean up
    if 'PASSWORD' in database and database['PASSWORD']:
        os.remove(password_path)
