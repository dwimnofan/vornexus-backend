from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('job_title', "category", 'created_at')  # tampilkan kolom di list view
    list_filter =  ('job_title', "category") # tambahkan filter di sisi kanan admin
    search_fields = ('job_title', 'company_name')