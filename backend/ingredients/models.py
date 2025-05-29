from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=200, verbose_name='Ingredient name')
    measurement_unit = models.CharField(max_length=200, verbose_name='Measurement unit')

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'
