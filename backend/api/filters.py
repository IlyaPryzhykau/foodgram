from django_filters import rest_framework as filters

from .models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов по имени."""

    name = filters.CharFilter(lookup_expr='istartswith',)

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов по автору, тегам и состоянию
    в избранном/списке покупок.
    """
    author = filters.NumberFilter(
        field_name='author__id', lookup_expr='exact'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
        conjoined=False
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация рецептов по состоянию в избранном
        для текущего пользователя.
        """
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()

        if value:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация рецептов по состоянию в списке
        покупок для текущего пользователя.
        """
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset.exclude(in_shopping_cart__user=user)
