from django.contrib import admin
from django.utils.html import format_html

from .models import (Recipe, Tag, Ingredient, IngredientInRecipe,
                     TagInRecipe, Favorite, ShoppingCart)


class TagInRecipeAdmin(admin.TabularInline):
    model = TagInRecipe
    autocomplete_fields = ('tag',)


class IngredientInRecipeAdmin(admin.TabularInline):
    model = IngredientInRecipe
    autocomplete_fields = ('ingredient',)
    min_num = 1


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    search_fields = ('name', 'measurement_unit')
    empty_value_display = '-пусто-'


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'slug')
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):

    def image_tag(self, obj):
        return format_html(
            '<img src="{}" height="100"/>'.format(obj.image.url))

    image_tag.short_description = 'Image'

    list_display = ('id', 'name', 'text', 'cooking_time', 'image',
                    'get_tags', 'pub_date', 'image_tag')

    list_display_links = ('id', 'name')

    search_fields = ('name', 'cooking_time', 'author__email',
                     'ingredients__name')
    list_filter = ('pub_date', 'tags',)

    readonly_fields = ['image_tag']

    inlines = (IngredientInRecipeAdmin, TagInRecipeAdmin)
    empty_value_display = '-пусто-'

    def get_tags(self, obj):
        return ', '.join([i.name for i in obj.tags.all()])


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user',)
    search_fields = ('user__email',)
    empty_value_display = '-пусто-'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'user',)
    search_fields = ('user__email',)
    empty_value_display = '-пусто-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
