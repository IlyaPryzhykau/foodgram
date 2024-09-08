import os
import json

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='The path to the JSON file containing ingredients'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'{file_path} not found'))
            return

        try:
            if os.path.exists(file_path):
                self.load_ingredients(file_path)
            else:
                self.stdout.write(self.style.WARNING(
                    f'{file_path} not found'
                ))

            self.stdout.write(self.style.SUCCESS('Data imported successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {e}'))
            transaction.set_rollback(True)

    def load_ingredients(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            for item in data:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
