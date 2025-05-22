import os
import django
import sys
import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import necessary Django components
from django.db import connection

def fix_migrations():
    # Get current time in ISO format
    current_time = datetime.datetime.now().isoformat()
    
    # Execute raw SQL to add the users migration to the migration history
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, %s)",
            ['users', '0001_initial', current_time]
        )
    
    print("Successfully added users migration to migration history.")
    print("Now you can run 'python manage.py migrate' to apply remaining migrations.")

if __name__ == "__main__":
    fix_migrations() 