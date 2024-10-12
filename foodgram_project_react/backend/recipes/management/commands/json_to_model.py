import json

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

from django.db import connection

DATA_FOLDER = f"{settings.BASE_DIR}/../data"
DB_ENGINE = settings.DATABASES.get("default").get("ENGINE")

class Command(BaseCommand):
    help = 'Load csv files to models'

    def handle(self, *args, **kwargs):

        with connection.cursor() as cursor:
            
            cursor.execute(f"DELETE FROM {Ingredient._meta.db_table}")

            if DB_ENGINE == "django.db.backends.postgresql":
                cursor.execute(f"ALTER SEQUENCE {Ingredient._meta.db_table}_id_seq RESTART WITH 1")

            if DB_ENGINE == "django.db.backends.sqlite3":
                cursor.execute(f"DELETE FROM SQLite_sequence WHERE name='{Ingredient._meta.db_table}'")

        cursor.close()

        with open(
            f"{DATA_FOLDER}/ingredients.json",
            'r',
            encoding='utf-8'
            ) as json_file:
            json_data = json.load(json_file)
            for json_element in json_data:
                Ingredient.objects.create(**json_element)
