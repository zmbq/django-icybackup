"""
This runs the tests for icybackup.

We're not using Django's unit test framework because this is really only one big test,
and Django likes to use an in-memory sqlite database, which can't be backed up.
"""
import hashlib
from django.conf import settings
import os

from django.test import TestCase
from ...models import Blah
from django.core.management import call_command, BaseCommand

IMAGE_SHA1 = "65c31668e9a889849e7ee8797f50e41d01a4bdcc"

TEST_POSTGRES = "This is the test content for the Postgres database"
TEST_MYSQL = "This is the test content for the MySQL database"
TEST_SQLITE = "This is the test content for the SQLite database"

class Command(BaseCommand):
	def handle(self, *args, **options):
		# Create DB objects
		pg_test = Blah.objects.create(text=TEST_POSTGRES)
		pg_test.save(using='postgres')
		mysql_test = Blah.objects.create(text=TEST_MYSQL)
		mysql_test.save(using='mysql')
		sqlite_test = Blah.objects.create(text=TEST_SQLITE)
		sqlite_test.save()

		# perform backup
		call_command('backup', output='backup.tgz')

		# delete everything
		pg_test.delete()
		mysql_test.delete()
		sqlite_test.delete()
		os.unlink(os.path.join(settings.MEDIA_ROOT, 'test_image.jpg'))

		# perform restore
		call_command('restore', input='backup.tgz')

		# check that the file is present
		img_path = os.path.join(settings.MEDIA_ROOT, 'test_image.jpg')
		assert os.path.exists(img_path)
		assert hashfile(img_path) == IMAGE_SHA1

		# check that the postgres db entry is there
		qs = Blah.objects.using('postgres').all()
		assert len(qs) == 1
		assert qs[0].text == TEST_POSTGRES

		# check that the mysql db entry is there
		qs = Blah.objects.using('mysql').all()
		assert len(qs) == 1
		assert qs[0].text == TEST_MYSQL

		# check that the sqlite db entry is there
		qs = Blah.objects.using('default').all()
		assert len(qs) == 1
		assert qs[0].text == TEST_SQLITE


def hashfile(filepath):
	sha1 = hashlib.sha1()
	f = open(filepath, 'rb')
	try:
		sha1.update(f.read())
	finally:
		f.close()
	return sha1.hexdigest()
