FROM postgres:14

# Install pglogical
RUN apt-get update && \
    apt-get install -y postgresql-14-pglogical && \
    rm -rf /var/lib/apt/lists/*

COPY ./postgresql.conf /etc/postgresql/postgresql.conf
COPY ./pg_hba.conf /etc/postgresql/pg_hba.conf
