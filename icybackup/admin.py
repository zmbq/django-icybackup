from django.contrib import admin
from .models import GlacierBackup

class GlacierBackupAdmin (admin.ModelAdmin):
	list_display = ('date', 'glacier_id')
	readonly_fields = ('glacier_id', 'date')

admin.site.register(GlacierBackup, GlacierBackupAdmin)