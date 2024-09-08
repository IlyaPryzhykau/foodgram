from rest_framework.viewsets import ReadOnlyModelViewSet
from django.contrib.auth import get_user_model
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Tag, Ingredient, Subscription, Recipe
from .serializers import UserSerializer, TagSerializer, IngredientSerializer, SubscriptionSerializer, RecipeSerializer


User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer

    def list(self, request):
        subscriptions = Subscription.objects.filter(user=request.user)
        serializer = UserSerializer(
            [sub.author for sub in subscriptions],
            many=True,
            context={'request': request}
        )
        return Response({"results": serializer.data})

    def create(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        if author == request.user:
            return Response({'error': 'Нельзя подписаться на самого себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscription, created = Subscription.objects.get_or_create(
            user=request.user, author=author)
        if created:
            return Response({'status': 'Подписка создана'},
                            status=status.HTTP_201_CREATED)
        return Response({'status': 'Вы уже подписаны'},
                        status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        try:
            subscription = Subscription.objects.get(user=request.user,
                                                    author=author)
            subscription.delete()
            return Response({'status': 'Подписка удалена'},
                            status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response({'error': 'Подписка не найдена'},
                            status=status.HTTP_404_NOT_FOUND)


class UserViewSet(BaseUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        # Automatically set the author as the current logged-in user
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        # Here, you can implement logic to generate a short link for the recipe
        # For example, return a static link or generate a custom link
        return Response(
            {'short_link': f'http://localhost:8000/api/recipes/{recipe.id}/'})

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        # Only allow the author to delete the recipe
        if request.user != recipe.author:
            return Response(
                {'error': 'You are not allowed to delete this recipe.'},
                status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
