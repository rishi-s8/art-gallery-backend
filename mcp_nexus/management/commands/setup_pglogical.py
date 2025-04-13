import os
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Sets up pglogical node and (optional) subscription to remote node.'

    def handle(self, *args, **options):
        node_name = os.environ.get('PGLOGICAL_NODE_NAME')
        local_dsn = os.environ.get('PGLOGICAL_LOCAL_DSN')  # optional
        remote_node_name = os.environ.get('PGLOGICAL_REMOTE_NODE_NAME')
        remote_dsn = os.environ.get('PGLOGICAL_REMOTE_DSN')

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
                """, [node_name, local_dsn or ''])
            except Exception as e:
                if "already exists" in str(e) or "duplicate key value" in str(e):
                    self.stdout.write(self.style.WARNING('Node already exists. Skipping.'))
                else:
                    raise

            self.stdout.write(self.style.NOTICE('Adding all tables in public schema to default replication set...'))
            cursor.execute("""
                SELECT pglogical.replication_set_add_all_tables('default', ARRAY['public'], true);
            """)

            if remote_node_name and remote_dsn:
                self.stdout.write(self.style.NOTICE(f'Attempting subscription to remote node: {remote_node_name}'))
                try:
                    cursor.execute("""
                        SELECT pglogical.create_subscription(
                            subscription_name := %s,
                            provider_dsn := %s,
                            replication_sets := ARRAY['default']
                        );
                    """, [f"sub_from_{remote_node_name}", remote_dsn])
                    self.stdout.write(self.style.SUCCESS(f'Subscription to {remote_node_name} created.'))
                except Exception as e:
                    if "already exists" in str(e):
                        self.stdout.write(self.style.WARNING(f'Subscription to {remote_node_name} already exists. Skipping.'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Failed to create subscription to {remote_node_name}. Skipping.\n{e}'))
            else:
                self.stdout.write(self.style.WARNING('No remote node info provided. Skipping subscription setup.'))

            self.stdout.write(self.style.SUCCESS('pglogical setup completed.'))
