#!/bin/sh

ALEMBIC=/usr/local/bin/alembic

echo "INFO  Checking if database is at current migration: $($ALEMBIC heads)."

if ! $ALEMBIC current | grep -q '(head)'; then
    echo "DATABASE MIGRATION IS NOT UP TO DATE"
    echo "RUNNING MIGRATION"
    $ALEMBIC --raiseerr upgrade head
else
    echo "INFO  Database is at right migration."
fi

echo "INFO  Starting application..."

echo "INFO Executing $@"

exec $@
