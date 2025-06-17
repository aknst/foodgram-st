import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка ингредиентов из JSON файла"

    def handle(self, *args, **options):
        data_dir = Path(settings.BASE_DIR).parent / "data"
        json_file = data_dir / "ingredients.json"

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                ingredients_data = json.load(f)

            new_objs = [Ingredient(**item) for item in ingredients_data]

            created = Ingredient.objects.bulk_create(
                new_objs,
                ignore_conflicts=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Успешно загружено {len(created)} ингредиентов"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Ошибка загрузки ингредиентов из файла "
                    f"{json_file.name}: {e}"
                )
            )
