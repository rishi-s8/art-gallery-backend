import os
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Sets up pglogical node and adds tables to the default replication set.'

    def handle(self, *args, **options):
        node_name = os.environ.get('PGLOGICAL_NODE_NAME')
        local_dsn = os.environ.get('PGLOGICAL_LOCAL_DSN', '')

        if not node_name:
            self.stderr.write(self.style.ERROR('PGLOGICAL_NODE_NAME is required.'))
            return

        with connection.cursor() as cursor:
            self.stdout.write(self.style.NOTICE('Creating pglogical extension (if not exists)...'))
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pglogical;")

            self.stdout.write(self.style.NOTICE(f'Creating pglogical node: {node_name}'))
            try:
                cursor.execute("""
                    SELECT pglogical.create_node(
                        node_name := %s,
                        dsn := %s
                    );
                """, [node_name, local_dsn])
            except Exception as e:
                if any(msg in str(e) for msg in [
                    "already configured as pglogical node",
                    "already exists",
                    "duplicate key value"
                ]):
                    self.stdout.write(self.style.WARNING('Node already exists. Skipping.'))
                else:
                    raise

            self.stdout.write(self.style.NOTICE('Adding all tables in public schema to default replication set...'))
            cursor.execute("""
                SELECT pglogical.replication_set_add_all_tables('default', ARRAY['public'], true);
            """)

        self.stdout.write(self.style.SUCCESS('pglogical node setup completed.'))