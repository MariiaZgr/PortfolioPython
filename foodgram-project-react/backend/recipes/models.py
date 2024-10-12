from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import constraints

User = get_user_model()


class Tag(models.Model):
    """Теги."""
    name = models.CharField(max_length=200, verbose_name='Название тега')
    color = models.CharField(max_length=7, verbose_name='Цвет в HEX')
    slug = models.SlugField(max_length=200, unique=True,
                            verbose_name='Уникальный слаг'
                            )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ингредиенты."""

    name = models.CharField(max_length=200, verbose_name="Имя")
    measurement_unit = models.CharField(max_length=200,
                                        verbose_name="Единица измерения")

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class IngredientInRecipe(models.Model):
    """Ингредиенты в рецепте."""

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE,
                               related_name='recipes')
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE,
                                   related_name='ingredients')
    amount = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        constraints = (
            constraints.UniqueConstraint(
                fields=('recipe', 'ingredient'), name='ingredient_unique'),
        )


class TagInRecipe(models.Model):
    """Теги в рецепте."""

    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)


class Recipe(models.Model):
    """Рецепт."""

    name = models.CharField(max_length=200, verbose_name='Название')

    text = models.TextField(verbose_name='Описание')

    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)')

    image = models.ImageField(
        upload_to='recipe/images/',
        null=True,
        default=None,
        verbose_name='Изображение')

    tags = models.ManyToManyField('Tag',
                                  through='TagInRecipe',
                                  verbose_name='Список тегов',
                                  related_name='recipe_tags'
                                  )

    ingredients = models.ManyToManyField('Ingredient',
                                         through='IngredientInRecipe',
                                         verbose_name="Cписок ингредиентов",
                                         related_name='recipe_ingredients'
                                         )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    """Список покупок."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_card_recipes',
        verbose_name="Рецепт")

    user = models.ForeignKey(
        User,
        related_name='shopping_card_owner',
        on_delete=models.CASCADE,
        verbose_name='Владелец корзины'
    )

    class Meta:
        verbose_name = 'Cписок покупок'
        verbose_name_plural = 'Cписки покупок'
        constraints = (
            constraints.UniqueConstraint(
                fields=('recipe', 'user'), name='shopping_card_unique'),
        )

    def __str__(self):
        return f'{self.user} - {self.recipe.name}'


class Favorite(models.Model):
    "Список избранных рецептов."

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name="Рецепт")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец избранного'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

        # Комментарий по ревью: Проверка на "подписку" на самого себя
        # реализована в методах Subscribe. Ограничение на добавление
        # своего рецепта в избранные не оговорено в ТЗ.

        constraints = (
            constraints.UniqueConstraint(
                fields=('recipe', 'user'), name='favorite_unique'),
        )

    def __str__(self):
        return f'{self.user} - {self.recipe.name}'
