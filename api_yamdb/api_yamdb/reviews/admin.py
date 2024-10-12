from django.conf import settings
from django.contrib import admin

from .models import Category, Comment, Genre, Review, Title, User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'role',
    )
    search_fields = ('username', 'role',)
    list_filter = ('username',)
    empty_value_display = '-пусто-'


class GenreAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )
    search_fields = ('name',)
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'year',
        'category',
        'description',
    )
    search_fields = ('name', 'genre',)
    list_filter = ('genre',)
    empty_value_display = '-пусто-'


class ReviewAdmin(admin.ModelAdmin):
    def get_text(self, obj):
        return obj.text[:settings.SYMBOLS_LIMIT]
    get_text.short_description = "Текст отзыва"

    list_display = (
        'title',
        'get_text',
        'author',
        'score',
        'pub_date',
    )
    list_display_links = ('get_text',)
    search_fields = ('pub_date', 'title__name',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    def get_text(self, obj):
        return obj.text[:settings.SYMBOLS_LIMIT]
    get_text.short_description = "Текст отзыва"

    list_display = (
        'review',
        'get_text',
        'author',
        'pub_date',
    )
    list_display_links = ('get_text',)
    search_fields = ('author__username', 'text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Title, TitleAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Comment, CommentAdmin)
