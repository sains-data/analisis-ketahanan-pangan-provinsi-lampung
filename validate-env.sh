#!/bin/bash

# Validate environment configuration for Lampung Food Security Big Data System

echo "🔍 Validating environment configuration..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy .env.example to .env and update the values:"
    echo "   cp .env.example .env"
    exit 1
fi

echo "✅ .env file found"

# Required environment variables
REQUIRED_VARS=(
    "METASTORE_DB_PASSWORD"
    "AIRFLOW_DB_PASSWORD"
    "AIRFLOW_FERNET_KEY"
    "AIRFLOW_SECRET_KEY"
    "AIRFLOW_ADMIN_USER"
    "AIRFLOW_ADMIN_PASSWORD"
    "SUPERSET_ADMIN_USER"
    "SUPERSET_ADMIN_PASSWORD"
    "SUPERSET_SECRET_KEY"
)

# Load .env file
set -a
source .env
set +a

echo "🔐 Checking required security variables..."

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "📝 Please update your .env file with these variables."
    exit 1
fi

echo "✅ All required environment variables are set"

# Security warnings
echo "🔒 Security checks..."

if [ "$AIRFLOW_ADMIN_PASSWORD" = "admin" ]; then
    echo "⚠️  WARNING: Using default Airflow admin password"
fi

if [ "$SUPERSET_ADMIN_PASSWORD" = "admin123" ]; then
    echo "⚠️  WARNING: Using default Superset admin password"
fi

if [ "$METASTORE_DB_PASSWORD" = "hive123" ]; then
    echo "⚠️  WARNING: Using default metastore database password"
fi

if [ "$AIRFLOW_DB_PASSWORD" = "airflow123" ]; then
    echo "⚠️  WARNING: Using default Airflow database password"
fi

if [[ "$SUPERSET_SECRET_KEY" == *"your-"* ]]; then
    echo "⚠️  WARNING: Using example Superset secret key"
fi

echo ""
echo "✅ Environment validation complete!"
echo "🚀 You can now start the system with: ./start-system.sh"
