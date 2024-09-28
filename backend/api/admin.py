from django.contrib import admin

from .models import (Recipe, Tag, Ingredient, RecipeIngredient,
                     Subscription, Favorite, ShoppingCart)


class RecipeIngredientInline(admin.TabularInline):
    """Inline отображение для ингредиентов рецепта в админке."""

    model = RecipeIngredient
    extra = 1
    fields = ('id', 'ingredient', 'amount')


class RecipeAdmin(admin.ModelAdmin):
    """Админ-класс для управления рецептами."""

    list_display = ('id', 'name', 'author', 'cooking_time', 'favorites_count')
    inlines = [RecipeIngredientInline]
    filter_horizontal = ('tags',)
    list_display_links = ('name',)
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'author')

    def favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorites.count()

    favorites_count.short_description = 'Добавлено в избранное'


class IngredientAdmin(admin.ModelAdmin):
    """Админ-класс для управления ингредиентами."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-класс для управления списками покупок."""

    list_display = ('user', 'recipe')
    list_filter = ('user',)
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-класс для управления подписками."""

    list_display = ('user', 'author')
    list_filter = ('user',)
    list_display_links = ('user', 'author')
    search_fields = ('user__email', 'author__email')


class FavoriteAdmin(admin.ModelAdmin):
    """Админ-класс для управления избранными рецептами."""

    list_display = ('user', 'recipe')
    list_filter = ('user',)
    list_display_links = ('user', 'recipe')
    search_fields = ('user__email', 'recipe__name')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
