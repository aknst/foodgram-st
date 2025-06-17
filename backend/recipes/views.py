from django.shortcuts import get_object_or_404, redirect
from rest_framework.exceptions import ValidationError

from recipes.models import Recipe


def redirect_short_link(request, recipe_id):
    try:
        get_object_or_404(Recipe, id=recipe_id)
        return redirect(f"/recipes/{recipe_id}")
    except ValueError:
        raise ValidationError("Некорректный ID рецепта.")
