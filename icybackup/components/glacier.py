from .. import models
from boto.glacier.layer2 import Layer2 as Glacier

# upload to amazon glacier
def upload(glacier_vault, output_file, settings):
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