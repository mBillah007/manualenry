from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings
import MySQLdb

class Command(BaseCommand):
    help = 'Create database if it does not exist'

    def handle(self, *args, **options):
        db_settings = settings.DATABASES['default']
        db_name = db_settings['NAME']

        try:
            conn = MySQLdb.connect(
                host=db_settings['HOST'],
                user=db_settings['USER'],
                passwd=db_settings['PASSWORD'],
                port=int(db_settings['PORT'])
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
            self.stdout.write(self.style.SUCCESS(f"Database '{db_name}' ensured."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating database: {e}"))
