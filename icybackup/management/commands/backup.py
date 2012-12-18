import os, sys, time
from optparse import make_option
from tempfile import mkdtemp, NamedTemporaryFile
import tarfile
from boto.glacier.layer2 import Layer2 as Glacier
from django.conf import settings

from ... import db, models

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# Based on: http://code.google.com/p/django-backup/
# Based on: http://www.djangosnippets.org/snippets/823/
# Based on: http://www.yashh.com/blog/2008/sep/05/django-database-backup-view/
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-o', '--output', default=None, dest='output',
            help='Write backup to file'),
        make_option('-d', '--outdir', default=None, dest='outdir',
            help='Write backup to timestamped file in a directory'),
        make_option('-g', '--glacier', default=None, dest='glacier',
            help='Upload backup to the Amazon Glacier vault with the given ARN'),
        make_option('-O', '--stdout', action='store_true', dest='stdout',
            help='Output backup tarball to standard output'),
        make_option('--extra', '-e', action='append', default=[], dest='extras',
            help='Include extra directories or files in the backup tarball'),
    )
    help = "Back up a Django installation (database and media directory)."

    def handle(self, *args, **options):
        extras = options.get('extras')
        
        output_file = options.get('output')
        output_dir = options.get('outdir')
        glacier_vault = options.get('glacier')
        output_to_stdout = options.get('stdout')
        output_file_temporary = False
        
        # glacier backups go to a temporary file
        if glacier_vault is not None or output_to_stdout:
            output_file_temporary = True
            output_file_obj = NamedTemporaryFile(delete=False)
            output_file_obj.close() # we'll open it later
            output_file = output_file_obj.name
        
        if output_file is None:
            if output_dir is None:
                raise CommandError('You must specify an output file')
            else:
                output_file = os.path.join(output_dir, '{}.tgz'.format(_time()))
        
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
            
        media_root = settings.MEDIA_ROOT
        
        # Create a temporary directory to perform our backup in
        backup_root = mkdtemp()
        database_root = os.path.join(backup_root, 'databases')
        os.mkdir(database_root)

        # Back up databases
        for name, database in database_list.iteritems():
            db.backup(database, os.path.join(database_root, name))
        
        # create backup gzipped tarball
        with tarfile.open(output_file, 'w:gz') as tf:
            tf.add(database_root, arcname='backup/databases')
            tf.add(media_root, arcname='backup/media')
            if len(extras) > 0:
                extras_mf = NamedTemporaryFile(delete=False)
                for count, extra in enumerate(extras):
                    tf.add(extra, arcname='backup/extras/{}'.format(count))
                    extras_mf.write('{},{}\n'.format(count, extra.replace(',','\\,')))
                extras_mf.close()
                tf.add(extras_mf.name, arcname='backup/extras/manifest')
                os.unlink(extras_mf.name)
        
        # upload to amazon glacier
        if glacier_vault is not None:
            g = Glacier(aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            for i in g.list_vaults():
                if glacier_vault == i.arn:
                    vault = i
                    break
            else:
                raise CommandError('The specified vault could not be accessed.')
            id = vault.upload_archive(output_file)
            
            # record backup internally
            # we don't need this record in order to restore from backup (obviously!)
            # but it makes pruning the backup set easier, and amazon reccomends it
            record = models.GlacierBackup.objects.create(glacier_id=id)
            record.save()
        
        # output to stdout
        if output_to_stdout:
            with open(output_file, 'r') as f:
                sys.stdout.write(f.read())
        
        # clean up
        rm_rf(backup_root)
        if output_file_temporary:
            os.unlink(output_file)
        
def rm_rf(d):
    for path in (os.path.join(d,f) for f in os.listdir(d)):
        if os.path.isdir(path):
            rm_rf(path)
        else:
            os.unlink(path)
    os.rmdir(d)

def _time():
    return time.strftime('%Y%m%d-%H%M%S')
