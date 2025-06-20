from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'birth_date', 'created_at')
    search_fields = ('user__username', 'location')
    list_filter = ('location',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Kullanıcı Bilgileri', {
            'fields': ('user',)
        }),
        ('Profil Detayları', {
            'fields': ('bio', 'location', 'birth_date')
        }),
        ('Sistem Bilgileri', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    ordering = ('-created_at',)
