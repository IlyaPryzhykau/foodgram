from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as BaseUserViewSet

from .encoding import encode_id, decode_id
from .pagination import CustomLimitPagination
from .filters import IngredientFilter, RecipeFilter
from .models import (Tag, Ingredient, Subscription, Recipe, Favorite,
                     ShoppingCart, RecipeIngredient)
from .serializers import (UserSerializer, TagSerializer, IngredientSerializer,
                          SubscriptionSerializer, RecipeSerializer,
                          RecipeShortSerializer)

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Обрабатывает запросы к тегам."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Обрабатывает запросы к ингредиентам."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Обрабатывает подписки пользователей."""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomLimitPagination

    def get_queryset(self):
        """Возвращает список подписок текущего пользователя."""
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        """Подписаться на автора."""
        author = get_object_or_404(User, pk=pk)
        if author == request.user:
            return Response({'error': 'Нельзя подписаться на самого себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )
        if created:
            serializer = SubscriptionSerializer(subscription,
                                                context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'error': 'Вы уже подписаны'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def unsubscribe(self, request, pk=None):
        """Отменить подписку на автора."""
        author = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(user=request.user,
                                                   author=author)
        if subscription.exists():
            subscription.delete()
            return Response({'status': 'Подписка удалена'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Подписка не найдена'},
                        status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(BaseUserViewSet):
    """Обрабатывает запросы к пользователям."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Получить данные текущего пользователя."""
        if not request.user.is_authenticated:
            return Response({'detail': 'Учетные данные не предоставлены.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_avatar(self, request):
        """Обновить аватар пользователя."""
        user = request.user
        avatar = request.data.get('avatar')

        if avatar is None or avatar == '':
            return Response({'avatar': 'Это поле не может быть пустым.'},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user, data=request.data, partial=True,
                                    context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({'avatar': user.avatar.url})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'])
    def delete_avatar(self, request):
        """Удалить аватар пользователя."""
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Обрабатывает запросы к рецептам."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        """Сохранить новый рецепт с автором как текущего пользователя. """
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        """Добавить рецепт в избранное."""
        recipe = self.get_object()
        user = request.user
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response({'error': 'Рецепт уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        Favorite.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request}
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='favorite')
    def remove_from_favorite(self, request, pk=None):
        """Удалить рецепт из избранного."""
        recipe = self.get_object()
        user = request.user
        favorite_item = Favorite.objects.filter(user=user, recipe=recipe)

        if not favorite_item.exists():
            raise ValidationError({'error': 'Рецепт не в избранном.'},
                                  code=status.HTTP_400_BAD_REQUEST)

        favorite_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def add_to_shopping_cart(self, request, pk=None):
        """Добавить рецепт в список покупок."""
        recipe = self.get_object()
        user = request.user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response({'error': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=user, recipe=recipe)

        serializer = RecipeShortSerializer(recipe,
                                           context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_from_shopping_cart(self, request, pk=None):
        """Удалить рецепт из списка покупок."""
        recipe = self.get_object()
        user = request.user
        shopping_cart_item = ShoppingCart.objects.filter(user=user,
                                                         recipe=recipe)

        if not shopping_cart_item.exists():
            raise ValidationError({'error': 'Рецепт не в списке покупок.'},
                                  code=status.HTTP_400_BAD_REQUEST)

        shopping_cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список ингредиентов из списка покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).select_related(
            'recipe')

        ingredients = {}
        for item in shopping_cart:
            recipe_ingredients = RecipeIngredient.objects.filter(
                recipe=item.recipe).select_related('ingredient')
            for recipe_ingredient in recipe_ingredients:
                ingredient = recipe_ingredient.ingredient
                name = ingredient.name
                amount = recipe_ingredient.amount
                unit = ingredient.measurement_unit

                if name in ingredients:
                    ingredients[name]['amount'] += amount
                else:
                    ingredients[name] = {'amount': amount, 'unit': unit}

        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )

        sorted_ingredients = sorted(ingredients.items(), key=lambda x: x[0])

        for name, data in sorted_ingredients:
            response.write(f"{name} - {data['amount']} {data['unit']}\n")

        return response

    @action(detail=True, methods=['get'])
    def get_short_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        recipe = self.get_object()
        short_link = (
            f'http://richi-host.zapto.org/api/s/{encode_id(recipe.id)}'
        )

        return Response({'short-link': short_link})

    @action(detail=False, methods=['get'])
    def redirect_to_recipe(self, request, encoded_id):
        """Перенаправить на рецепт по закодированному ID."""
        recipe = get_object_or_404(Recipe, id=decode_id(encoded_id))

        return redirect(f'http://richi-host.zapto.org/recipes/{recipe.id}')

    def update(self, request, *args, **kwargs):
        """Обновить рецепт."""
        recipe = self.get_object()
        if request.user != recipe.author:
            return Response(
                {'error': 'Вы не можете обновлять чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Удалить рецепт."""
        recipe = self.get_object()
        if request.user != recipe.author:
            return Response(
                {'error': 'Вы не можете удалять чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
