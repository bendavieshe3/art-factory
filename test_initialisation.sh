#!/bin/bash

# Define original and temporary names for the SQLite database and default warehouse
ORIGINAL_DB="web/db.sqlite3"
TEMP_DB="web/db_temp.sqlite3"
ORIGINAL_WAREHOUSE="./default_warehouse"
TEMP_WAREHOUSE="./default_warehouse_temp"

# Step 1: Rename the SQLite database and default warehouse (if they exist)
if [ -f "$ORIGINAL_DB" ]; then
    mv "$ORIGINAL_DB" "$TEMP_DB"
    echo "Renamed $ORIGINAL_DB to $TEMP_DB"
fi

if [ -d "$ORIGINAL_WAREHOUSE" ]; then
    mv "$ORIGINAL_WAREHOUSE" "$TEMP_WAREHOUSE"
    echo "Renamed $ORIGINAL_WAREHOUSE to $TEMP_WAREHOUSE"
fi

# Step 2: Run database migrations
echo "Running database migrations..."
./web/manage.py makemigrations
./web/manage.py migrate

# Step 3: Trigger initialization with an innocuous art-factory command
echo "Triggering initialization..."
./art-factory.py warehouse

# Step 4: Rename the SQLite database and default warehouse back to their original names
if [ -f "$TEMP_DB" ]; then
    mv "$TEMP_DB" "$ORIGINAL_DB"
    echo "Renamed $TEMP_DB back to $ORIGINAL_DB"
fi

if [ -d "$TEMP_WAREHOUSE" ]; then
    rm -rf "$ORIGINAL_WAREHOUSE"
    mv "$TEMP_WAREHOUSE" "$ORIGINAL_WAREHOUSE"
    echo "Renamed $TEMP_WAREHOUSE back to $ORIGINAL_WAREHOUSE"
fi

echo "Initialization test completed."
