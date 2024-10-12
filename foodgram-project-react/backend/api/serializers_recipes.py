from django.core.validators import MinValueValidator
from rest_framework import serializers
from recipes.models import (Recipe, Tag, Ingredient, IngredientInRecipe,
                            Favorite, ShoppingCart)
from django.shortcuts import get_object_or_404
from django.core import exceptions
from drf_extra_fields.fields import Base64ImageField
from django.contrib.auth import get_user_model
from .serializers_users import UserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(method_name='get_name')
    measurement_unit = serializers.SerializerMethodField(
        method_name='get_measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class RecipeIngredientModifySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Введите количество.'
            ),
        )
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipesViewSerializer(serializers.ModelSerializer):

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients'
    )

    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    def get_ingredients(self, obj):
        ingredients = (IngredientInRecipe.objects
                       .select_related('ingredient').filter(recipe=obj))
        serializer = RecipeIngredientReadSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    class Meta:
        fields = '__all__'
        model = Recipe


class IngredientViewSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'measurement_unit',)
        model = Ingredient


class RecipesModifySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientModifySerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Введите время приготовления.'
            ),
        )
    )

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Добавьте ингридиенты.'
            )

        ingredients = [item['id'] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    'Такой ингридиент уже есть.'
                )

        return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient_object = get_object_or_404(
                                Ingredient, pk=ingredient['id']
                                )

            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient_object,
                amount=amount
            )

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()

            for ingredient in ingredients:
                amount = ingredient['amount']
                ingredient_object = get_object_or_404(Ingredient,
                                                      pk=ingredient['id'])

                IngredientInRecipe.objects.create(
                    recipe=instance,
                    ingredient=ingredient_object,
                    amount=amount
                )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Вывод данных."""
        serializer = RecipesViewSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    class Meta:
        fields = '__all__'
        model = Recipe
