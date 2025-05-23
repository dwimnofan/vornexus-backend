from django.contrib import admin
from .models import JobCategory, JobSource, Job

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'source', 'location', 'posted_date', 'created_at')
    list_filter = ('category', 'source', 'posted_date', 'created_at')
    search_fields = ('title', 'company', 'description', 'location')
    date_hierarchy = 'created_at'


# Register your models here.
