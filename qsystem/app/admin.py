from django.contrib import admin
from .models import Activity, Counter, CounterActivityAssignment, QueueNumber, CounterActivity, StaffProfile

# Register the Activity model
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'mode')
    search_fields = ('name', 'code')
    list_filter = ('mode',)

# Register the Counter model
@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    search_fields = ('name',)
    list_filter = ('status',)

# Register the CounterActivityAssignment model
@admin.register(CounterActivityAssignment)
class CounterActivityAssignmentAdmin(admin.ModelAdmin):
    list_display = ('counter', 'activity', 'date')
    search_fields = ('counter__name', 'activity__name')
    list_filter = ('date',)

# Register the QueueNumber model
@admin.register(QueueNumber)
class QueueNumberAdmin(admin.ModelAdmin):
    list_display = ('activity', 'number', 'issued_at', 'called_at', 'status', 'counter', 'date',  'is_recalled')
    search_fields = ('activity__name', 'number',  'is_recalled')
    list_filter = ('status', 'issued_at', 'called_at', 'counter', 'date')

# Register the CounterActivity model
@admin.register(CounterActivity)
class CounterActivityAdmin(admin.ModelAdmin):
    list_display = ('counter', 'activity', 'status')
    search_fields = ('counter__name', 'activity__name')
    list_filter = ('status',)

admin.site.register(StaffProfile)
