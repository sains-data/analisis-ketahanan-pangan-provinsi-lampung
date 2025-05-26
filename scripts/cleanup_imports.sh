#!/bin/bash

# Cleanup unused imports based on pyright warnings
# This script removes specific unused imports identified by pyright

set -e

echo "🧹 Cleaning up unused imports..."

# Create backup directory
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Function to backup and clean a file
cleanup_file() {
    local file="$1"
    local imports_to_remove="$2"

    if [ ! -f "$file" ]; then
        echo "⚠️  File not found: $file"
        return
    fi

    echo "📝 Processing: $file"

    # Create backup
    cp "$file" "$BACKUP_DIR/$(basename $file)"

    # Remove unused imports
    for import in $imports_to_remove; do
        # Remove import from comma-separated list
        sed -i "s/, $import//g" "$file"
        sed -i "s/$import, //g" "$file"
        sed -i "s/$import//g" "$file"
    done

    # Clean up any remaining empty import lines or trailing commas
    sed -i '/^from .* import[[:space:]]*$/d' "$file"
    sed -i 's/,[[:space:]]*)/)/g' "$file"
    sed -i 's/([[:space:]]*,/(/g' "$file"
}

# Clean specific files based on pyright warnings
cleanup_file "scripts/calc_gold_enriched.py" "mean DoubleType"
cleanup_file "scripts/calc_indikator.py" "Window"
cleanup_file "scripts/clean_cuaca.py" "to_date year"
cleanup_file "scripts/clean_harga.py" "IntegerType StringType"
cleanup_file "scripts/clean_produksi.py" "when isnan isnull DoubleType StringType"

# Fix DAG unused expression
if [ -f "dags/lampung_foodsec_dag.py" ]; then
    echo "📝 Processing: dags/lampung_foodsec_dag.py"
    cp "dags/lampung_foodsec_dag.py" "$BACKUP_DIR/lampung_foodsec_dag.py"

    # Fix the unused expression by adding a comment or variable assignment
    sed -i 's/bronze_task >> silver_task >> gold_task >> validate_gold_task/# Task dependencies\n_ = bronze_task >> silver_task >> gold_task >> validate_gold_task/' "dags/lampung_foodsec_dag.py"
fi

# Run isort to clean up import organization
if command -v isort &> /dev/null; then
    echo "🔧 Running isort to organize imports..."
    isort scripts/ dags/ src/ --profile black 2>/dev/null || true
fi

# Run black to format the files
if command -v black &> /dev/null; then
    echo "🎨 Running black to format code..."
    black scripts/ dags/ src/ --quiet 2>/dev/null || true
fi

echo "✅ Cleanup complete!"
echo "📦 Backups saved in: $BACKUP_DIR"
echo ""
echo "🔍 Run 'pyright' to verify improvements"
echo "🗑️  Remove backup directory when satisfied: rm -rf $BACKUP_DIR"
