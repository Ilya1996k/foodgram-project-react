from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class Tags(models.Model):
    """Модель тегов."""
    name = models.CharField('Название', max_length=50)
    color = models.CharField('Цвет', max_length=20)
    slug = models.CharField("Слаг тега", max_length=100)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ("name",)

    def __str__(self):
        return f'Название тега: {self.name}'


class Ingredients(models.Model):
    """Модель ингредиентов."""
    name = models.CharField('Название', max_length=50)
    measurement_unit = models.CharField('Единица измерения', max_length=20)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'Название ингредиента: {self.name}'


class Recipes(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=50)
    image = models.ImageField('Картинка',
                              blank=True,
                              null=True,
                              upload_to="recipes/")
    # image = models.ImageField('Картинка', upload_to="recipes/")
    text = models.CharField('Текстовое описание', max_length=1000)
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name='Ингредиенты',
        # through='CountIngredient'
    )
    tags = models.ManyToManyField(
        Tags,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField('Время приготовления')
    date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-date',)

    def __str__(self):
        return f'Название: {self.name}\n Автор: {self.author.username}'


class Carts(models.Model):
    """Модель для корзины покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return (f'Рецепт {self.recipe.name} добавлен в корзину' +
                f' пользователя {self.user.username}')


class Favourites(models.Model):
    """Модель для избранных рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранное'

    def __str__(self):
        return (f'Рецепт {self.recipe.name} добавлен в избранное' +
                f'  пользователя {self.user.username}')


class CountIngredient(models.Model):
    """ Модель для количества ингредиентов в рецепте """

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='ingredients_for_recipe',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингредиенты',
        related_name='ingredients_in_recipes'
    )
    amount = models.PositiveSmallIntegerField('Количество')

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.ingredient.name}: {self.amount}'
