import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ingredients.models import Ingredient


class Command(BaseCommand):
    help = "Load ingredients from JSON file"

    def handle(self, *args, **options):
        data_dir = Path(settings.BASE_DIR).parent / "data"
        json_file = data_dir / "ingredients.json"

        if not json_file.exists():
            self.stdout.write(self.style.ERROR(f"File {json_file} not found"))
            return

        with open(json_file, "r", encoding="utf-8") as f:
            ingredients_data = json.load(f)

        for ingredient_data in ingredients_data:
            Ingredient.objects.get_or_create(
                name=ingredient_data["name"],
                measurement_unit=ingredient_data["measurement_unit"],
            )

        self.stdout.write(
            self.style.SUCCESS("Successfully loaded ingredients")
        )
