from django.contrib import admin
from .models import Project, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'manager', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'manager')
    search_fields = ('title', 'description')
    filter_horizontal = ('team',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'status')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date', 'created_at', 'updated_at')
        }),
        ('Команда', {
            'fields': ('manager', 'team')
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'assigned_to', 'due_date')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'project')
        }),
        ('Статус и приоритет', {
            'fields': ('status', 'priority')
        }),
        ('Назначение', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Даты', {
            'fields': ('due_date', 'created_at', 'updated_at')
        }),
    )
