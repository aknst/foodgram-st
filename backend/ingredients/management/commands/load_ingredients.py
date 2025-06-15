import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ingredients.models import Ingredient


class Command(BaseCommand):
    help = "Load ingredients from JSON file"

    def handle(self, *args, **options):
        try:
            data_dir = Path(settings.BASE_DIR).parent / "data"
            json_file = data_dir / "ingredients.json"

            with open(json_file, "r", encoding="utf-8") as f:
                ingredients_data = json.load(f)

            existing = set(
                Ingredient.objects.values_list("name", "measurement_unit")
            )

            new_objs = [
                Ingredient(
                    name=item["name"],
                    measurement_unit=item["measurement_unit"],
                )
                for item in ingredients_data
                if (item["name"], item["measurement_unit"]) not in existing
            ]

            created = Ingredient.objects.bulk_create(new_objs)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully loaded {len(created)} new ingredients"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error loading ingredients: {e}")
            )
