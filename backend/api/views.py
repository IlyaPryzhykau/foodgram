
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import viewsets, status,serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from .pagination import CustomLimitPagination
from .filters import IngredientFilter, RecipeFilter
from .models import Tag, Ingredient, Subscription, Recipe, Favorite, ShoppingCart, RecipeIngredient
from .serializers import UserSerializer, TagSerializer, IngredientSerializer, SubscriptionSerializer, RecipeSerializer


User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter



class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomLimitPagination

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author == request.user:
            return Response({'error': 'Нельзя подписаться на самого себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )
        if created:
            serializer = SubscriptionSerializer(subscription, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({'error': 'Вы уже подписаны'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def unsubscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        subscription = Subscription.objects.filter(user=request.user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response({'status': 'Подписка удалена'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Подписка не найдена'},
                        status=status.HTTP_404_NOT_FOUND)


class UserViewSet(BaseUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(detail=False, methods=['get'])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Учетные данные не предоставлены.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_avatar(self, request):
        user = request.user
        avatar = request.data.get('avatar')

        # Проверяем наличие поля 'avatar' и его пустое значение
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
        user = request.user
        user.avatar.delete(
            save=True)  # Удалить аватар и сохранить изменения в модели
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        # Automatically set the author as the current logged-in user
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], url_path='favorite')
    def add_to_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response({'error': 'Рецепт уже в избранном.'},
                            status=status.HTTP_400_BAD_REQUEST)

        Favorite.objects.create(user=user, recipe=recipe)
        return Response({'status': 'Рецепт добавлен в избранное.'},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='favorite')
    def remove_from_favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response({'status': 'Рецепт удалён из избранного.'},
                            status=status.HTTP_204_NO_CONTENT)

        return Response({'error': 'Рецепт не найден в избранном.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_to_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response({'error': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=user, recipe=recipe)
        response_data = {
            'id': recipe.id,
            'name': recipe.name,
            'image': recipe.image.url,
            'cooking_time': recipe.cooking_time
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_from_shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        shopping_cart_item = ShoppingCart.objects.filter(user=user,
                                                         recipe=recipe)
        if shopping_cart_item.exists():
            shopping_cart_item.delete()
            return Response({'status': 'Рецепт удалён из списка покупок.'},
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart',
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).select_related(
            'recipe')

        # Сбор ингредиентов по всем рецептам пользователя
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

        # Создаем текстовый файл с отсортированным списком ингредиентов
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'

        sorted_ingredients = sorted(ingredients.items(), key=lambda x: x[0])  # сортировка по имени ингредиента

        for name, data in sorted_ingredients:
            response.write(f"{name} - {data['amount']} {data['unit']}\n")

        return response

    @action(detail=True, methods=['get'])
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = f'http://127.0.0.1:8000/api/s/{recipe.id}'
        return Response({'short-link': short_link})

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if request.user != recipe.author:
            return Response(
                {'error': 'Вы не можете обновлять чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        # Only allow the author to delete the recipe
        if request.user != recipe.author:
            return Response(
                {'error': 'You are not allowed to delete this recipe.'},
                status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
