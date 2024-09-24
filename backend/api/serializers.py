import base64

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError

from .models import (Recipe, Subscription, Tag, Ingredient,
                     RecipeIngredient, Favorite, ShoppingCart)
from foodgram.settings import DEFAULT_PAGE_SIZE

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для обработки изображений в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""
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

    def get_recipes_count(self, obj):
        if self.get_is_subscribed(obj):
            return Recipe.objects.filter(author=obj).count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not self.get_is_subscribed(instance):
            representation.pop('recipes', None)
            representation.pop('recipes_count', None)

        return representation


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    author = serializers.SerializerMethodField()
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipe_ingredients')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_author(self, obj):
        user = obj.author
        request = self.context.get('request')
        is_subscribed = False

        if request and request.user.is_authenticated:
            is_subscribed = Subscription.objects.filter(user=request.user,
                                                        author=user).exists()

        return {
            'email': user.email,
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_subscribed': is_subscribed,
            'avatar': user.avatar.url if user.avatar else None
        }

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated and
                Favorite.objects.filter(user=user, recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated and
                ShoppingCart.objects.filter(user=user, recipe=obj).exists())

    def validate(self, data):
        ingredients = data.get('recipe_ingredients', [])
        tags = data.get('tags', [])

        if not ingredients:
            raise ValidationError(
                {'recipe_ingredients': 'Это поле не может быть пустым.'})

        ingredient_ids = [item.get('ingredient').id for item in ingredients]
        if not Ingredient.objects.filter(id__in=ingredient_ids).count() == len(
                ingredient_ids):
            raise ValidationError(
                {'recipe_ingredients': 'Некоторые ингредиенты не существуют.'})

        for ingredient in ingredients:
            if ingredient.get('amount', 0) <= 0:
                raise ValidationError(
                    {'recipe_ingredients': 'Количество '
                                           'ингредиента должно быть больше 0.'}
                )

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError(
                {'recipe_ingredients': 'Ингредиенты не должны повторяться.'})

        if not tags:
            raise ValidationError({'tags': 'Это поле не может быть пустым.'})

        if len(tags) != len(set(tags)):
            raise ValidationError({'tags': 'Теги не должны повторяться.'})

        if not data.get('text'):
            raise ValidationError({'text': 'Это поле не может быть пустым.'})

        if data.get('cooking_time', 0) <= 0:
            raise ValidationError(
                {'cooking_time': 'Время приготовления должно быть больше 0.'})

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)

        instance.recipe_ingredients.all().delete()
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=instance, **ingredient_data)

        instance.tags.set(tags_data)

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        ingredients = instance.recipe_ingredients.all()
        representation['ingredients'] = [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            } for ri in ingredients
        ]

        representation['tags'] = TagSerializer(instance.tags.all(), many=True).data

        return representation


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецептов."""
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    email = serializers.CharField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name',
                                       read_only=True)
    last_name = serializers.CharField(source='author.last_name',
                                      read_only=True)
    avatar = Base64ImageField(source='author.avatar', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated and
                Subscription.objects.filter(user=user,
                                            author=obj.author).exists())

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None
        recipes = Recipe.objects.filter(
            author=obj.author)[:recipes_limit or DEFAULT_PAGE_SIZE]

        return RecipeShortSerializer(recipes, many=True,
                                     context=self.context).data