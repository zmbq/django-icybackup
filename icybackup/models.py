from django.db import models

class GlacierBackup (models.Model):
	glacier_id = models.CharField(max_length=138, unique=True, verbose_name="Glacier backup ID")
	date = models.DateTimeField(auto_now_add=True)
	class Meta:
		verbose_name = "Glacier backup"
		verbose_name_plural = "Glacier backups"