from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientsFilter, RecipesFilter
from api.paginators import LimitPagination
from api.permissions import AdminOrReadOnly, AuthorOrAdminOrReadOnly
from api.serializers import (IngredientSerializer, RecipeCreateSerializer,
                             RecipeReadSerializer, RecipeShortSerializer,
                             SubscribeSerializer, TagSerializer,
                             UserSerializer)
from recipes.models import (Carts, CountIngredient, Favourites, Ingredients,
                            Recipes, Tags)
from users.models import Subscribers, Users

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Класс для тегов рецептов."""
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Класс для ингредиентов рецептов."""
    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = IngredientsFilter


class UserViewSet(DjoserUserViewSet):
    """Класс для пользователей."""
    permission_classes = (AdminOrReadOnly,)
    pagination_class = LimitPagination
    queryset = Users.objects.all()
    serializer_class = UserSerializer

    @action(detail=False,
            methods=["GET"],
            permission_classes=(IsAuthenticated, ))
    def subscriptions(self, request):
        """Cписок подписок."""
        pages = self.paginate_queryset(
            User.objects.filter(subscribers__user=request.user)
        )
        serializer = SubscribeSerializer(pages,
                                         many=True,
                                         context={"request": request}
                                         )
        return self.get_paginated_response(serializer.data)
        # return Response(serializer.data)

    @action(detail=True, methods=["POST", "DELETE"],
            url_path="subscribe", permission_classes=(IsAuthenticated, ))
    def subscribe(self, request):
        author = self.get_object()
        if request.method == "POST":
            serializer = SubscribeSerializer(author,
                                             data=request.data,
                                             context={"request": request})
            serializer.is_valid(raise_exception=True)
            Subscribers.objects.create(
                user=request.user,
                author=author
            )
            return Response(serializer.data, status=HTTP_201_CREATED)
        subscription = Subscribers.objects.get(
            user=request.user,
            author=author
        )
        subscription.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    queryset = Recipes.objects.all()
    pagination_class = LimitPagination
    permission_classes = (AuthorOrAdminOrReadOnly, )
    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RecipeCreateSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=["DELETE", "POST"])
    def shopping_cart(self, request, pk):
        queryset = Carts.objects.filter(user=request.user, recipe__id=pk)
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == "POST":
            if queryset.exists():
                return Response({"errors": "Рецепт уже добавлен!"},
                                status=HTTP_400_BAD_REQUEST)
            Carts.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=HTTP_201_CREATED)

        else:
            in_cart = get_object_or_404(Carts,
                                        user=request.user,
                                        recipe=recipe
                                        )
            in_cart.delete()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["DELETE", "POST"])
    def favorite(self, request, pk):
        queryset = Favourites.objects.filter(user=request.user, recipe__id=pk)
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == "POST":
            if queryset.exists():
                return Response({"errors": "Рецепт уже добавлен!"},
                                status=HTTP_400_BAD_REQUEST)
            Favourites.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=HTTP_201_CREATED)

        else:
            in_favorites = get_object_or_404(Favourites,
                                             user=request.user,
                                             recipe=recipe)
            in_favorites.delete()
            return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=["GET"],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = CountIngredient.objects.filter(
            recipe__cart__user=request.user
        ).values(
            "ingredient__name",
            "ingredient__measurement_unit"
        ).annotate(
            sum=Sum("amount")
        )
        shopping_list = ["Список покупок \n"]
        for i, ingredient in enumerate(ingredients):
            line = "".join([f"Ингредиент №{i+1}: ",
                            f"{ingredient['ingredient__name']}  ",
                            f"{ingredient['sum']}",
                            f"{ingredient['ingredient__measurement_unit']}.\n"
                            ])
            shopping_list.append(line)
        response = HttpResponse(
            shopping_list, content_type="text.txt; charset=utf-8")
        response["Content-Disposition"] = "attachment; filename='shopping.txt'"
        return response
