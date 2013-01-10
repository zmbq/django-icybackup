from django.db import models

class GlacierBackup (models.Model):
	glacier_id = models.CharField(max_length=138, unique=True, verbose_name="Glacier backup ID")
	date = models.DateTimeField()
	class Meta:
		verbose_name = "Glacier backup"
		verbose_name_plural = "Glacier backups"

class GlacierInventory (models.Model):
	inventory_id = models.CharField(max_length=92, unique=True, verbose_name="Glacier inventory ID")
	collected_date = models.DateTimeField(blank=True, null=True, default=None)
	requested_date = models.DateTimeField(auto_now_add=True)