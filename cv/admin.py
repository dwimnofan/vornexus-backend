from django.contrib import admin
from .models import CV

<<<<<<< HEAD
# Register your models here.
admin.site.register(CV)
=======
@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('id', 'user_id')
    readonly_fields = ('id', 'uploaded_at')
>>>>>>> 1ed4a22 (upload-cv)
