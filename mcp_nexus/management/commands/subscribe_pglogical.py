import os
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Creates a pglogical subscription to a remote node.'

    def handle(self, *args, **options):
        remote_node_name = os.environ.get('PGLOGICAL_REMOTE_NODE_NAME')
        remote_dsn = os.environ.get('PGLOGICAL_REMOTE_DSN')

        if not remote_node_name or not remote_dsn:
            self.stderr.write(self.style.ERROR('PGLOGICAL_REMOTE_NODE_NAME and PGLOGICAL_REMOTE_DSN are required.'))
            return

        subscription_name = f"sub_from_{remote_node_name}"

        with connection.cursor() as cursor:
            self.stdout.write(self.style.NOTICE(f'Attempting subscription to remote node: {remote_node_name}'))
            try:
                command = """
                    SELECT pglogical.create_subscription(
                        subscription_name := \'{}\',
                        provider_dsn := \'{}\',
                        replication_sets := ARRAY['default']
                    );
                """.format(subscription_name, remote_dsn)
                print("Variables: ", subscription_name, remote_dsn)
                print ("Command being executed: ", command)
                cursor.execute(command, [subscription_name, remote_dsn])
                # cursor.execute("""
                #     SELECT pglogical.create_subscription(
                #         subscription_name := %s,
                #         provider_dsn := %s,
                #         replication_sets := ARRAY['default']
                #     );
                # """, [subscription_name, remote_dsn])
                self.stdout.write(self.style.SUCCESS(f'Subscription to {remote_node_name} created.'))
            except Exception as e:
                if "already exists" in str(e):
                    self.stdout.write(self.style.WARNING(f'Subscription to {remote_node_name} already exists. Skipping.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Failed to create subscription to {remote_node_name}. Skipping.\n{e}'))

        self.stdout.write(self.style.SUCCESS('pglogical subscription setup completed.'))