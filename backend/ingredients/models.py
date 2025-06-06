from django.db import models


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200, verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=200, verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"
