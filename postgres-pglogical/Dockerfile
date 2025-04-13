FROM postgres:14

# Install pglogical
RUN apt-get update && \
    apt-get install -y postgresql-14-pglogical && \
    rm -rf /var/lib/apt/lists/*
