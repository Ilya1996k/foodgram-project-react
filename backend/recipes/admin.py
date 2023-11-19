from django.contrib import admin
from django.contrib.admin import display

from .models import (Carts, CountIngredient, Favourites, Ingredients, Recipes,
                     Tags)


@admin.register(Tags)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "slug",)


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit",)
    search_fields = ("name",)


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("author", "name", "count_favorites")
    list_filter = ("author", "tags")
    search_fields = ("name",)

    @display(description="Количество в избранных")
    def count_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Carts)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe",)


@admin.register(Favourites)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe",)


@admin.register(CountIngredient)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount",)
