from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Subscription

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name', 'date_joined',
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('date_joined', 'email', 'first_name')
    empty_value_display = '-пусто-'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author',)
    search_fields = ('user__email',)
    empty_value_display = '-пусто-'


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(User, UserAdmin)
