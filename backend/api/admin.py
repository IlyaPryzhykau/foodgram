from django.contrib import admin
from .models import Recipe, Tag, Ingredient, RecipeIngredient

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    fields = ('ingredient', 'amount')

class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'cooking_time')
    inlines = [RecipeIngredientInline]
    filter_horizontal = ('tags',)  # Поле ManyToMany без промежуточной модели

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(RecipeIngredient)