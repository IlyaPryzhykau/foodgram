from rest_framework.routers import DefaultRouter
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from .views import (UserViewSet, TagViewSet, SubscriptionViewSet,
                    IngredientViewSet, RecipeViewSet)

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
        SubscriptionViewSet.as_view(
            {'post': 'subscribe', 'delete': 'unsubscribe'}
        ),
        name='user-subscription-detail'
    ),
    path(
        'users/me/avatar/',
        UserViewSet.as_view(
            {'put': 'update_avatar', 'delete': 'delete_avatar'}
        ),
        name='user-avatar-detail'
    ),

    path(
        'recipes/<int:pk>/get-link/',
        RecipeViewSet.as_view(
            {'get': 'get_short_link'}
        ),
        name='recipe-short-link'
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        RecipeViewSet.as_view(
            {'post': 'add_to_shopping_cart',
             'delete': 'remove_from_shopping_cart'}
        ),
        name='recipe-shopping-cart'
    ),
    path(
        'recipes/<int:pk>/favorite/',
        RecipeViewSet.as_view(
            {'post': 'add_to_favorite', 'delete': 'remove_from_favorite'}
        ),
        name='recipe-favorite'
    ),
    path(
        's/<str:encoded_id>/',
        RecipeViewSet.as_view(
            {'get': 'redirect_to_recipe'}),
        name='recipe_detail'
    ),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
