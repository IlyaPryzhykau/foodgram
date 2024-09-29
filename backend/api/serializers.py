import base64

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.exceptions import ValidationError

from .models import Recipe, RecipeIngredient, Subscription, Tag, Ingredient

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
            return user.follower.filter(author=obj).exists()
        return False

    def get_recipes(self, obj):
        if self.get_is_subscribed(obj):
            recipes = obj.recipes.all()
            return RecipeSerializer(recipes, many=True,
                                    context=self.context).data

    def get_recipes_count(self, obj):
        if self.get_is_subscribed(obj):
            return obj.recipes.count()

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
    amount = serializers.IntegerField(
        min_value=settings.MIN_AMOUNT,
        max_value=settings.MAX_AMOUNT
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


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
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=settings.MIN_COOKING_TIME,
        max_value=settings.MAX_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')

    def get_author(self, obj):
        user = obj.author
        request = self.context.get('request')
        context = {'request': request}

        serializer = UserSerializer(user, context=context)
        data = serializer.data

        data.pop('recipes', None)
        data.pop('recipes_count', None)

        return data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and user.favorites.filter(recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and user.shopping_cart.filter(recipe=obj).exists())

    def validate(self, data):
        ingredients = data.get('recipe_ingredients', [])
        tags = data.get('tags', [])

        if not ingredients:
            raise ValidationError(
                {'recipe_ingredients': 'Это поле не может быть пустым.'})

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if not Ingredient.objects.filter(id__in=ingredient_ids).count() == len(
                ingredient_ids):
            raise ValidationError(
                {'recipe_ingredients': 'Некоторые ингредиенты не существуют.'})

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError(
                {'recipe_ingredients': 'Ингредиенты не должны повторяться.'})

        if not tags:
            raise ValidationError({'tags': 'Это поле не может быть пустым.'})

        if len(tags) != len(set(tags)):
            raise ValidationError({'tags': 'Теги не должны повторяться.'})

        return data

    def create_recipe_ingredients(self, recipe, ingredients_data):
        """Создает ингредиенты для рецепта с использованием bulk_create."""
        recipe_ingredients = [
            RecipeIngredient(recipe=recipe, **ingredient_data)
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        self.create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', [])
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)

        instance.recipe_ingredients.all().delete()

        self.create_recipe_ingredients(instance, ingredients_data)
        instance.tags.set(tags_data)

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation['ingredients'] = RecipeIngredientDetailSerializer(
            instance.recipe_ingredients.all(),
            many=True
        ).data

        representation['tags'] = TagSerializer(
            instance.tags.all(),
            many=True
        ).data

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

    def validate(self, data):
        user = self.context['request'].user
        author = data.get('author')

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя.')

        return data

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and user.follower.filter(author=obj.author).exists())

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None
        recipes_limit_value = recipes_limit or settings.DEFAULT_PAGE_SIZE
        recipes = obj.author.recipes.all()[:recipes_limit_value]

        return RecipeShortSerializer(recipes, many=True,
                                     context=self.context).data
