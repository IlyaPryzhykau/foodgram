from django.contrib import admin
from .models import Recipe, Tag, Ingredient, RecipeIngredient

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    fields = ('id', 'ingredient', 'amount')

class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'cooking_time')
    inlines = [RecipeIngredientInline]
    filter_horizontal = ('tags',)  # Поле ManyToMany без промежуточной модели

class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(RecipeIngredient)
