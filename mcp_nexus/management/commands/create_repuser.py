from django.core.management.base import BaseCommand
from django.db import connection
from psycopg2 import sql
import os

class Command(BaseCommand):
    help = 'Creates a read-only pglogical replication user'

    def handle(self, *args, **options):
        username = os.environ.get('REPLICATION_USER', 'repuser')
        password = os.environ.get('REPLICATION_PASSWORD', 'repuser')

        with connection.cursor() as cursor:
            # Check if the role exists
            cursor.execute(
                sql.SQL("SELECT 1 FROM pg_roles WHERE rolname = %s"),
                [username]
            )
            if not cursor.fetchone():
                # Create the role with LOGIN privilege
                cursor.execute(
                    sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s").format(
                        sql.Identifier(username)
                    ),
                    [password]
                )

            # Grant necessary privileges
            cursor.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(connection.settings_dict['NAME']),
                    sql.Identifier(username)
                )
            )
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )
            cursor.execute(
                sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )
            cursor.execute(
                sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {}").format(
                    sql.Identifier(username)
                )
            )

        self.stdout.write(self.style.SUCCESS(f'Replication user {username} created with read-only access.'))