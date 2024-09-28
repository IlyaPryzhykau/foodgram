from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()


MIN_AMOUNT = 1
MAX_AMOUNT = 32_000
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32_000


class Tag(models.Model):
    """Модель тега, который может быть присвоен рецепту."""
    name = models.CharField(
        'Тег',
        max_length=32
    )
    slug = models.SlugField(
        'Слаг',
        max_length=32
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента, используемого в рецептах."""
    name = models.CharField(
        'Ингридиент',
        max_length=128
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64
    )

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Модель для связи между рецептами и ингредиентами с указанием количества.
    """
    recipe = models.ForeignKey(
        'Recipe',
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            models.Min(MIN_AMOUNT),
            models.Max(MAX_AMOUNT)
        ]
    )

    class Meta:
        verbose_name = 'ингредиент для рецепта'
        verbose_name_plural = 'ингредиенты для рецептов'
        ordering = ('recipe',)

    def __str__(self):
        return f'Ингридиенты для рецепта "{self.recipe.name}"'


class Recipe(models.Model):
    """
    Модель рецепта с указанием его ингредиентов, автора и других характеристик.
    """
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Список тегов'
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    name = models.CharField(
        'Название',
        max_length=256
    )
    image = models.ImageField(
        'Ссылка на картинку на сайте',
        upload_to='images/',
        blank=True,
        null=True
    )
    text = models.TextField('Описание', blank=True)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        null=True,
        blank=True,
        validators=[
            models.Min(MIN_COOKING_TIME),
            models.Max(MAX_COOKING_TIME)
        ]
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """
    Модель подписки пользователя на другого пользователя (автора рецептов).
    """
    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name='Подписчик',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

    def clean(self):
        """Проверка на попытку подписки на самого себя."""
        if self.user == self.author:
            raise ValidationError("Нельзя подписаться на самого себя.")


class Favorite(models.Model):
    """Модель избранного, позволяющая пользователю сохранять рецепты."""
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('-id',)

    def __str__(self):
        return f'{self.user.email} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """
    Модель списка покупок, позволяющая пользователю сохранять
    рецепты для последующего использования.
    """
    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('-id',)

    def __str__(self):
        return f'{self.user.email} - {self.recipe.name} в списке покупок'
