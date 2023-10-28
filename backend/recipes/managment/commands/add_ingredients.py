import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredients


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        Ingredients.objects.all().delete()
        with open('data/ingredients.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                Ingredients.objects.create(name=row[0],
                                           measurement_unit=row[1])
