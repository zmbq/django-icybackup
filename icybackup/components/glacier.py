from .. import models
from datetime import timedelta, datetime
from boto.glacier.layer2 import Layer2 as Glacier
from dateutil.parser import parse
from django.core.management import CommandError

# upload to amazon glacier

def _get_vault(g, glacier_vault):
	for i in g.list_vaults():
		if glacier_vault == i.arn:
			return i
	else:
		raise CommandError('The specified vault could not be accessed.')

def upload(glacier_vault, output_file, settings):
	g = Glacier(aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
	vault = _get_vault(g, glacier_vault)
	id = vault.upload_archive(output_file)
	
	# record backup internally
	# we don't need this record in order to restore from backup (obviously!)
	# but it makes pruning the backup set easier, and amazon reccomends it
	record = models.GlacierBackup.objects.create(glacier_id=id, date=datetime.now())
	record.save()

def reconcile(glacier_vault, settings):
	g = Glacier(aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
	vault = _get_vault(g, glacier_vault)

	# check any inventory requests that have not been collected,
	# and if they are finished, collect them
	to_be_collected = models.GlacierInventory.objects.filter(collected_date=None)
	if len(to_be_collected) > 0:
		for record in to_be_collected:
			job = vault.get_job(record.inventory_id)
			if job.completed:
				print "Reconciling inventory", record.inventory_id
				_do_reconcile(job.get_output())
				record.collected_date = datetime.now()
				record.save()

	# if there are no collected inventories in the last 14 days,
	# and no requested inventories in the last 3,
	# request another inventory
	max_requested_date = datetime.now() - timedelta(days=3)
	max_collected_date = datetime.now() - timedelta(days=14)
	if models.GlacierInventory.objects.exclude(collected_date__lte=max_collected_date).exclude(requested_date__lte=max_requested_date).count() == 0:
		job_id = vault.retrieve_inventory()
		record = models.GlacierInventory.objects.create(inventory_id=job_id)
		record.save()

def _do_reconcile(inventory):
	for archive in inventory['ArchiveList']:
		id = archive['ArchiveId']
		creation_date = parse(archive['CreationDate'])
		if not models.GlacierBackup.objects.filter(glacier_id=id).exists():
			models.GlacierBackup.objects.create(glacier_id=id, date=creation_date).save()
