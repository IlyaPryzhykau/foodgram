from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import UserViewSet, TagViewSet, SubscriptionViewSet, IngredientViewSet, RecipeViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [

    path(
        'users/subscriptions/',
        SubscriptionViewSet.as_view({'get': 'list'}),
        name='user-subscriptions-list'
    ),
    path(
        'users/<int:pk>/subscribe/',
        SubscriptionViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
        name='user-subscription-detail'
    ),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]


