from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from recipes.models import CountIngredient, Ingredients, Recipes, Tags
from users.models import Subscribers

User = get_user_model()


class UserSerializer(ModelSerializer):
    """Работа с пользователями."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
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
    # recipes = RecipeInfoSerializer(many=True, read_only=True)
    recipes = SerializerMethodField()

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
        user = self.context.get("request").user
        if user == author:
            raise ValidationError(
                detail="Нельзя подписаться на самого себя!",
                code=status.HTTP_400_BAD_REQUEST
            )
        if Subscribers.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail="На этого пользователя Вы уже подписаны!",
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_recipes_count(self, obj):
        """Количество рецептов каждого автора."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        params = self.context.get("request").query_params
        limit = params.get("recipes_limit")
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]

        serializer = RecipeInfoSerializer(recipes, many=True)
        return serializer.data

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
        fields = "__all__"


class TagSerializer(ModelSerializer):
    """Вывод тегов."""

    class Meta:
        model = Tags
        fields = "__all__"


class RecipeReadSerializer(ModelSerializer):
    """Вывод рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = SerializerMethodField()
    # image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = (
            "id",
            "tags", "ingredients",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
            "image", "text",
            "name", "cooking_time"
        )

    def get_image(self, recipe):
        if recipe.image:
            return recipe.image.url
        return None

    def get_ingredients(self, recipe):
        """Получить все ингредиенты для данного рецецпта."""
        ingredients = Ingredients.objects.filter(
            ingredients_in_recipes__recipe=recipe
        )
        return ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=F("ingredients_in_recipes__amount")
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
    image = Base64ImageField()

    class Meta:
        model = Recipes
        fields = ("id", "image", "name", "cooking_time")


class RecipeCreateSerializer(RecipeReadSerializer):
    """Создание и обновление рецептов."""
    # tags = serializers.PrimaryKeyRelatedField(
    #     many=True,
    #     queryset=Tags.objects.all()
    # )
    tags = TagSerializer(many=True, read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            "id",
            "tags", "ingredients",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
            "image", "text",
            "name", "cooking_time"
        )

    def get_ingredients(self, recipe):
        """Получить все ингредиенты для данного рецецпта."""
        ingredients = Ingredients.objects.filter(
            ingredients_in_recipes__recipe=recipe
        )
        return ingredients.values(
            "id",
            "name",
            "measurement_unit",
            amount=F("ingredients_in_recipes__amount")
        )

    def validate_tags(self, tags):
        if len(tags) == 0:
            raise ValidationError(
                detail="Дожен быть хотя бы один тег!"
            )
        tags_obj = Tags.objects.filter(id__in=tags)

        if len(tags) != len(tags_obj):
            raise ValidationError("Указан несуществующий тег.")

        return list(tags_obj)

    def validate_cooking_time(self, cooking_time):
        if cooking_time < 1:
            raise ValidationError(
                detail="Время не менее 1 минуты!"
            )
        if cooking_time > 300:
            raise ValidationError(
                detail="Слишком долго!"
            )
        return cooking_time

    def validate(self, data):
        """Валидация исходных данных."""
        ingredients = self.initial_data.get("ingredients")
        tags = self.initial_data.get("tags")
        image = self.initial_data.get("image")
        if not ingredients:
            raise ValidationError(
                detail="Отсутствуют ингредиенты!"
            )
        if not tags:
            raise ValidationError(
                detail="Отсутствуют tags!"
            )
        if not image:
            raise ValidationError(
                detail="Отсутствуют image!"
            )
        ingredients = self.validate_ingredients(ingredients)
        tags = self.validate_tags(tags)

        data.update(
            {
                "ingredients": ingredients,
                "tags": tags
            }
        )
        return data

    def validate_ingredients(self, ingredients):
        if len(ingredients) == 0:
            raise ValidationError(
                detail="Дожен быть хотя бы один ингредиент!"
            )
        id_ingredients_list = [item["id"] for item in ingredients]
        if len(set(id_ingredients_list)) != len(id_ingredients_list):
            raise ValidationError(
                detail="Ингредиенты не должны повторяться!"
            )
        for item in ingredients:
            if int(item["amount"]) <= 0:
                raise ValidationError(
                    detail="Должен быть хотя бы 1 ингредиент!"
                )

        for ingredient in ingredients:
            try:
                Ingredients.objects.get(id=ingredient['id'])
            except Ingredients.DoesNotExist:
                raise ValidationError(detail="Ингредиентов нет ")

        return ingredients

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipes.objects.create(
            author=self.context.get("request").user,
            **validated_data
        )
        recipe.tags.set(tags)
        recipe.tags.set(tags)
        recipe.tags.set(tags)

        CountIngredient.objects.bulk_create(
            [CountIngredient(
                ingredient=Ingredients.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.tags.clear()
        instance.tags.set(tags)
        CountIngredient.objects.filter(recipe=instance).delete()
        CountIngredient.objects.bulk_create(
            [CountIngredient(
                ingredient=Ingredients.objects.get(id=ingredient['id']),
                recipe=instance,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        instance.save()
        return instance
