from django.db import models

class GlacierBackup (models.Model):
	glacier_id = models.CharField(max_length=138, unique=True)
	date = models.DateTimeField(auto_now_add=True)