from datetime import datetime, timedelta
from django.test import TestCase
from .models import GlacierBackup

class GlacierTests (TestCase):
	def setUp(self):
		GlacierBackup.objects.create(
			glacier_id = '11111',
			date = datetime.now() - timedelta(days=1),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '22222',
			date = datetime.now() - timedelta(days=2),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '33333',
			date = datetime.now() - timedelta(days=32),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '44444',
			date = datetime.now() - timedelta(days=32, hours=1),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '55555',
			date = datetime.now() - timedelta(days=33),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '66666',
			date = datetime.now() - timedelta(days=91),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '77777',
			date = datetime.now() - timedelta(days=91),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '88888',
			date = datetime.now() - timedelta(days=92),
		).save()
		GlacierBackup.objects.create(
			glacier_id = '99999',
			date = datetime.now() - timedelta(days=99),
		).save()

	def test_prune(self):
		pass