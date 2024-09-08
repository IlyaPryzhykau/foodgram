import base64

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from .models import (Recipe, Subscription, Tag, Ingredient,
                     RecipeIngredient, Favorite, ShoppingCart)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'avatar', 'is_subscribed',
            'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def get_recipes(self, obj):
        if self.get_is_subscribed(obj):
            recipes = Recipe.objects.filter(author=obj)
            return RecipeSerializer(recipes, many=True,
                                    context=self.context).data
        return None

    def get_recipes_count(self, obj):
        if self.get_is_subscribed(obj):
            return Recipe.objects.filter(author=obj).count()
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Удаляем поля, если пользователь не подписан
        if not self.get_is_subscribed(instance):
            representation.pop('recipes', None)
            representation.pop('recipes_count', None)

        return representation


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), source='ingredient')
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')



class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)  # Оставляем только идентификаторы
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'tags', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj).select_related('ingredient')
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            }
            for ri in recipe_ingredients
        ]

    def create(self, validated_data):
        ingredients_data = self.context['request'].data.get('ingredients', [])
        tags_data = validated_data.pop('tags', [])

        # Создаем объект Recipe
        recipe = Recipe.objects.create(**validated_data)

        # Устанавливаем теги для рецепта
        recipe.tags.set(tags_data)

        # Создаем связи для ингредиентов рецепта
        ingredient_objects = {ingredient_data['id']: Ingredient.objects.get(id=ingredient_data['id']) for ingredient_data in ingredients_data}
        for ingredient_data in ingredients_data:
            ingredient = ingredient_objects[ingredient_data['id']]
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

        return recipe

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Обрабатываем развернутое представление тегов
        representation['tags'] = TagSerializer(instance.tags.all(), many=True).data
        return representation




class SubscriptionSerializer(serializers.ModelSerializer):
    author = UserSerializer()

    class Meta:
        model = Subscription
        fields = ('user', 'author', 'created_at')
