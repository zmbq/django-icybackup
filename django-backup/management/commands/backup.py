import os, popen2, time
from datetime import datetime
from optparse import make_option
from tempfile import mkdtemp
import tarfile

from ... import db

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.sites.models import Site

# Based on: http://code.google.com/p/django-backup/
# Based on: http://www.djangosnippets.org/snippets/823/
# Based on: http://www.yashh.com/blog/2008/sep/05/django-database-backup-view/
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-o', '--output', default=None, dest='output',
            help='File to write backup to'),
        make_option('--email', '-m', default=None, dest='email',
            help='Sends email with attached dump file'),
        make_option('--directory', '-d', action='append', default=[], dest='directories',
            help='Include Directories'),
        make_option('--backup_docs', '-b', action='store_true', default=False,
            dest='backup_docs', help='Backup your docs directory alongside the DB dump.'),

    )
    help = "Backup database. Only Mysql, Postgresql and Sqlite engines are implemented"

    def _time_suffix(self):
        return time.strftime('%Y%m%d-%H%M%S')

    def handle(self, *args, **options):
        self.email = options.get('email')
        self.directories = options.get('directories')
        
        output_file = options.get('output')
        if output_file is None:
            raise CommandError('You must specify an output file')
        
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

        # Backuping directoris
        dir_outfiles = []
        for directory in self.directories:
            dir_outfile = os.path.join(backup_dir, '%s_%s.tar.gz' % (os.path.basename(directory), self._time_suffix()))
            dir_outfiles.append(dir_outfile)
            print("Compressing '%s' to '%s'" % (directory, dir_outfile))
            self.compress_dir(directory, dir_outfile)
        
        # create backup gzipped tarball
        with tarfile.open(output_file, 'w:gz') as tf:
            tf.add(database_root, arcname='backup/databases')
            tf.add(media_root, arcname='backup/media')

        # Sending mail with backups
        if self.email:
            print "Sending e-mail with backups to '%s'" % self.email
            self.sendmail(settings.SERVER_EMAIL, [self.email], dir_outfiles + [outfile])
        
        rm_rf(backup_root)

    def sendmail(self, address_from, addresses_to, attachements):
        subject = "Your DB-backup for %s %s" % (datetime.now().strftime("%d %b %Y"), self.current_site)
        body = "Timestamp of the backup is " + datetime.now().strftime("%d %b %Y")

        email = EmailMessage(subject, body, address_from, addresses_to)
        email.content_subtype = 'html'
        for attachement in attachements:
            email.attach_file(attachement)
        email.send()
        
def rm_rf(d):
    for path in (os.path.join(d,f) for f in os.listdir(d)):
        if os.path.isdir(path):
            rm_rf(path)
        else:
            os.unlink(path)
    os.rmdir(d)

