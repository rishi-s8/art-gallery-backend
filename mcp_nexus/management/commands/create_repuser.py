from django.core.management.base import BaseCommand
from django.db import connection
from psycopg2 import sql
import os

class Command(BaseCommand):
    help = 'Creates a dedicated pglogical replication user with necessary privileges'

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
                # Create the role with LOGIN and REPLICATION privileges
                cursor.execute(
                    sql.SQL("CREATE ROLE {} WITH LOGIN REPLICATION PASSWORD %s").format(
                        sql.Identifier(username)
                    ),
                    [password]
                )

            # Grant CONNECT privilege on the current database
            cursor.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(connection.settings_dict['NAME']),
                    sql.Identifier(username)
                )
            )

            # Grant USAGE on the public schema
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )

            # Grant SELECT on all existing tables in the public schema
            cursor.execute(
                sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )

            # Ensure future tables in the public schema have SELECT granted to the replication user
            cursor.execute(
                sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {}").format(
                    sql.Identifier(username)
                )
            )

            # Grant USAGE on the pglogical schema
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA pglogical TO {}").format(
                    sql.Identifier(username)
                )
            )

            # Grant SELECT on all tables in the pglogical schema
            cursor.execute(
                sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA pglogical TO {}").format(
                    sql.Identifier(username)
                )
            )

            # Grant EXECUTE on all functions in the pglogical schema
            cursor.execute(
                sql.SQL("GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pglogical TO {}").format(
                    sql.Identifier(username)
                )
            )

        self.stdout.write(self.style.SUCCESS(f'Replication user "{username}" created with necessary privileges.'))