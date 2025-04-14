#!/usr/bin/env python
import time
import subprocess
import sys

# Wait for database to be ready
max_retries = 10
retry_count = 0
while retry_count < max_retries:
    try:
        print("Checking if database is ready...")
        subprocess.check_call(["python", "manage.py", "check", "--database", "default"])
        print("Database is ready!")
        break
    except subprocess.CalledProcessError:
        retry_count += 1
        print(f"Database not ready yet (attempt {retry_count}/{max_retries}), waiting...")
        time.sleep(5)

if retry_count == max_retries:
    print("Could not connect to database after maximum retries. Exiting.")
    sys.exit(1)

# Run migrations
print("Running migrations...")
subprocess.check_call(["python", "manage.py", "migrate", "--noinput"])

# Create superuser if needed
print("Ensuring superuser exists...")
subprocess.check_call(["python", "manage.py", "ensure_superuser"])

# Setup pglogical
print("Setting up pglogical...")
subprocess.check_call(["python", "manage.py", "setup_pglogical"])

# Create repuser
print("Creating replication user...")
subprocess.check_call(["python", "manage.py", "create_repuser"])

# Subscribe to pglogical
print("Subscribing to pglogical...")
subprocess.check_call(["python", "manage.py", "subscribe_pglogical"])

# Collect static files
print("Collecting static files...")
subprocess.check_call(["python", "manage.py", "collectstatic", "--noinput"])

print("All migration and static collection tasks completed successfully!")
