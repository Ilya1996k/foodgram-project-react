from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import IntegerField, SerializerMethodField
from recipes.models import Ingredients, Recipes, Tags, CountIngredient
from users.models import Subscribers
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework.exceptions import ValidationError
from rest_framework import status

User = get_user_model()


class UserSerializer(ModelSerializer):
    """Работа с пользователями."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователей."""
        user = self.context.get("request").user

        if user.is_anonymous or (user == obj):
            return False

        return user.subscriptions.filter(author=obj).exists()

class RecipeInfoSerializer(ModelSerializer):
    """Информация о рецепте."""

    class Meta:
        model = Recipes
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("__all__",)


class SubscribeSerializer(UserSerializer):
    """Вывод подписок пользователя."""
    recipes_count = SerializerMethodField()
    recipes = RecipeInfoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "recipes_count", 
            "recipes",
            "is_subscribed",
        )
        read_only_fields = ("__all__",)

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if Subscribers.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='На этого пользователя Вы уже подписаны!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data
 
    def get_recipes_count(self, obj):
        """Количество рецептов каждго автора."""
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователей."""
        user = self.context.get("request").user

        if user.is_anonymous or (user == obj):
            return False

        return user.subscriptions.filter(author=obj).exists()
    


class IngredientSerializer(ModelSerializer):
    """Вывод ингридиентов."""

    class Meta:
        model = Ingredients
        fields = '__all__'


class TagSerializer(ModelSerializer):
    """Вывод тегов."""

    class Meta:
        model = Tags
        fields = '__all__'


class RecipeReadSerializer(ModelSerializer):
    """Вывод рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()


    class Meta:
        model = Recipes
        fields = (
            'id',
            'tags', 'ingredients',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
            'image', 'text', 
            'name', 'cooking_time'
        )

    def get_ingredients(self, recipe):
        """Получить все ингредиенты для данного рецецпта."""
        ingredients = CountIngredient.objects.filter(recipe=recipe)
        return ingredients.values(
            'amount',
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit'),
            
        )
    
    def get_is_favorited(self, recipe):
        """Проверить наличие рецепта в избранном"""
        user = self.context.get("view").request.user

        if user.is_anonymous:
            return False

        return user.favorites.filter(recipe=recipe).exists()
    
    def get_is_in_shopping_cart(self, recipe):
        """проверить наличие рецепта в корзине"""
        user = self.context.get("view").request.user

        if user.is_anonymous:
            return False

        return user.cart.filter(recipe=recipe).exists()


class RecipeShortSerializer(ModelSerializer):
    class Meta:
        model = Recipes
        fields = ('id', 'image', 'name', 'cooking_time')


class RecipeCreateSerializer(ModelSerializer):
    """Создание и обновление рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all()
        )
    ingredients = SerializerMethodField()
    image = Base64ImageField()


    class Meta:
        model = Recipes
        fields = (
            'tags', 'ingredients',
            'image', 'text', 
            'name', 'cooking_time'
        )

    def get_ingredients(self, recipe):
        """Получить все ингредиенты для данного рецецпта."""
        ingredients = CountIngredient.objects.filter(recipe=recipe)
        return ingredients.values(
            'ingredient_id',
            'ingredient__name',
            'ingredient__measurement_unit',
            'amount'
        )

    def validate_tags(self, tags):
        if len(tags)==0:
            raise ValidationError(
                detail='Дожен быть хотя бы один тег!',
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(set(tags)) != len(tags):
            raise ValidationError(
                detail='Все теги должны быть уникальными!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return tags

    def validate(self, data):
        """Валидация исходных данных."""
        ingredients = self.initial_data.get("ingredients")
        ingredients = self.validate_ingredients(ingredients)

        data.update(
            {
                "ingredients": ingredients
            }
        )
        return data
    
    def validate_ingredients(self, ingredients):
        if len(ingredients)==0:
            raise ValidationError(
                detail='Дожен быть хотя бы один ингредиент!',
                status=status.HTTP_400_BAD_REQUEST
            )
        id_ingredients_list = [item['id'] for item in ingredients]
        if len(set(id_ingredients_list)) != len(id_ingredients_list):
            raise ValidationError(
                detail='Ингредиенты не должны повторяться!',
                status=status.HTTP_400_BAD_REQUEST
            )
        if len([item['amount'] for item in ingredients if int(item['amount']) <= 0]) > 0:
            raise ValidationError(
                detail='Должно быть хотя бы какое-то количество ингредиента!',
                status=status.HTTP_400_BAD_REQUEST
            )
        return ingredients

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(
            author=self.context.get('request').user,
            **validated_data
        )
        recipe.tags.set(tags)
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            CountIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                amount=amount
            )
        return recipe
  
    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        if tags:
            instance.tags.clear()
            instance.tags.set(tags)
        if ingredients:
            instance.ingredients.clear()
            for ingredient, amount in ingredients.values():
                CountIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=amount
                )
        instance.save()
        return instance










    