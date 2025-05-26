#!/bin/bash

# Lampung Food Security Development Environment Setup Script
# This script sets up the development environment with proper dependencies and type checking

set -e  # Exit on any error

echo "🚀 Setting up Lampung Food Security Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3.8+ is available
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo -e "${RED}Error: Python 3.8+ is required. Found: ${PYTHON_VERSION}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip (use venv's pip explicitly)
echo -e "${BLUE}Upgrading pip...${NC}"
.venv/bin/pip install --upgrade pip setuptools wheel

# Install uv for faster package management
echo -e "${BLUE}Installing uv package manager...${NC}"
.venv/bin/pip install uv

# Install project dependencies
echo -e "${BLUE}Installing project dependencies...${NC}"
if [ -f "pyproject.toml" ]; then
    .venv/bin/uv pip install -e ".[dev,airflow,database,jupyter,monitoring]"
else
    # Fallback to requirements.txt
    if [ -f "requirements.txt" ]; then
        .venv/bin/uv pip install -r requirements.txt
        .venv/bin/uv pip install pytest pytest-cov black isort mypy pyright flake8
    else
        echo -e "${YELLOW}No pyproject.toml or requirements.txt found, installing basic dependencies...${NC}"
        .venv/bin/uv pip install pyspark pandas numpy pyarrow python-dotenv pyyaml
        .venv/bin/uv pip install pytest black isort mypy pyright flake8
    fi
fi

# Install type stubs (skip pyspark-stubs for Python 3.13 compatibility)
echo -e "${BLUE}Installing type stubs...${NC}"
.venv/bin/uv pip install types-requests types-PyYAML || echo -e "${YELLOW}Some type stubs may not be available${NC}"

# Create .env file from template
echo -e "${BLUE}Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file from template${NC}"
        echo -e "${YELLOW}Please review and update .env file with your specific settings${NC}"
    else
        echo -e "${YELLOW}No .env.example found, creating basic .env file...${NC}"
        cat > .env << EOF
# Lampung Food Security Environment Configuration
ENVIRONMENT=development
DEBUG=true
PYTHONPATH=$(pwd)/src
LOG_LEVEL=INFO

# Hadoop & Spark (Docker containers)
HDFS_NAMENODE_HOST=namenode
HDFS_NAMENODE_PORT=9000
SPARK_MASTER_URL=spark://spark-master:7077
HIVE_HOST=hiveserver2
HIVE_PORT=10000
EOF
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Set up Python path
echo -e "${BLUE}Configuring Python path...${NC}"
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
echo "export PYTHONPATH=\"$(pwd)/src:\$PYTHONPATH\"" >> .venv/bin/activate

# Create pyrightconfig.json for better type checking
echo -e "${BLUE}Setting up Pyright configuration...${NC}"
cat > pyrightconfig.json << EOF
{
    "include": [
        "src",
        "scripts",
        "dags"
    ],
    "exclude": [
        "**/__pycache__",
        "**/node_modules",
        "**/.venv",
        "**/venv",
        ".git",
        "logs",
        "data",
        "output.txt"
    ],
    "venvPath": ".",
    "venv": ".venv",
    "pythonVersion": "3.13",
    "pythonPlatform": "Linux",
    "typeCheckingMode": "basic",
    "useLibraryCodeForTypes": true,
    "reportMissingImports": "warning",
    "reportMissingTypeStubs": "none",
    "reportMissingParameterType": "none",
    "reportUnknownParameterType": "none",
    "reportUnknownVariableType": "none",
    "reportUnknownMemberType": "none",
    "reportUnknownArgumentType": "none",
    "reportPrivateUsage": "warning",
    "reportUnusedImport": "warning",
    "reportUnusedVariable": "warning",
    "stubPath": "typings"
}
EOF

# Code quality tools are available via scripts/
echo -e "${GREEN}✓ Code quality tools configured${NC}"

# Ensure we're using the virtual environment
if [[ "$VIRTUAL_ENV" != *".venv"* ]]; then
    echo -e "${YELLOW}Re-activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Create development scripts
echo -e "${BLUE}Creating development utility scripts...${NC}"

# Create format script
cat > scripts/format_code.sh << 'EOF'
#!/bin/bash
echo "Formatting code with black..."
black src/ scripts/ dags/ --line-length 88

echo "Sorting imports with isort..."
isort src/ scripts/ dags/ --profile black

echo "Running flake8 checks..."
flake8 src/ scripts/ dags/ --max-line-length=88 --extend-ignore=E203,W503

echo "Code formatting complete!"
EOF

# Create type check script
cat > scripts/type_check.sh << 'EOF'
#!/bin/bash
echo "Running type checks with pyright..."
pyright

echo "Running mypy checks..."
mypy src/ --ignore-missing-imports

echo "Type checking complete!"
EOF

# Create test script
cat > scripts/run_tests.sh << 'EOF'
#!/bin/bash
echo "Running tests with pytest..."
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

echo "Tests complete! Coverage report available in htmlcov/"
EOF

# Make scripts executable
chmod +x scripts/*.sh

# Create basic test structure
echo -e "${BLUE}Setting up test structure...${NC}"
mkdir -p tests/unit tests/integration tests/fixtures
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py

# Create a basic test file
cat > tests/unit/test_config.py << 'EOF'
"""
Unit tests for configuration module
"""
import pytest
from src.config.settings import SPARK_CONFIG, HDFS_CONFIG, HIVE_CONFIG


def test_spark_config_exists():
    """Test that Spark configuration is properly defined"""
    assert SPARK_CONFIG is not None
    assert "app_name" in SPARK_CONFIG
    assert "master" in SPARK_CONFIG


def test_hdfs_config_exists():
    """Test that HDFS configuration is properly defined"""
    assert HDFS_CONFIG is not None
    assert "namenode_host" in HDFS_CONFIG
    assert "base_url" in HDFS_CONFIG


def test_hive_config_exists():
    """Test that Hive configuration is properly defined"""
    assert HIVE_CONFIG is not None
    assert "host" in HIVE_CONFIG
    assert "port" in HIVE_CONFIG
EOF

# Create basic conftest.py for pytest
cat > tests/conftest.py << 'EOF'
"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def spark_session():
    """Create a Spark session for testing (if available)"""
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder \
            .appName("TestSession") \
            .master("local[2]") \
            .getOrCreate()
        yield spark
        spark.stop()
    except ImportError:
        pytest.skip("PySpark not available for testing")
EOF

# Verify installation
echo -e "${BLUE}Verifying installation...${NC}"
.venv/bin/python -c "
try:
    import sys
    print(f'✓ Python {sys.version.split()[0]}')

    import pyspark
    print(f'✓ PySpark {pyspark.__version__}')

    import pandas
    print(f'✓ Pandas {pandas.__version__}')

    import numpy
    print(f'✓ NumPy {numpy.__version__}')

    # Test our modules
    sys.path.insert(0, 'src')
    from config.settings import SPARK_CONFIG
    print('✓ Project configuration loaded')

    print('✓ All core dependencies verified')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"

# Create development documentation
echo -e "${BLUE}Creating development documentation...${NC}"
cat > docs/DEVELOPMENT.md << 'EOF'
# Development Guide

## Setup

Run the setup script:
```bash
./setup_dev_env.sh
```

Activate the virtual environment:
```bash
source .venv/bin/activate
```

## Development Workflow

1. **Code Formatting**:
   ```bash
   ./scripts/format_code.sh
   ```

2. **Type Checking**:
   ```bash
   ./scripts/type_check.sh
   ```

3. **Running Tests**:
   ```bash
   ./scripts/run_tests.sh
   ```

4. **Quality Checks**:
   Run formatting and type checking as needed:
   ```bash
   ./scripts/format_code.sh && ./scripts/type_check.sh
   ```

## IDE Setup

### VS Code
Install these extensions:
- Python
- Pylance
- Black Formatter
- isort

### PyCharm
Configure:
- Python interpreter: `.venv/bin/python`
- Code style: Black
- Import sorting: isort

## Project Structure

```
src/
├── config/          # Configuration management
├── utils/           # Common utilities
└── etl/            # ETL pipeline code

scripts/            # Operational scripts
dags/              # Airflow DAGs
tests/             # Test files
docs/              # Documentation
```

## Type Checking

The project uses Pyright for type checking. Type stubs are provided in `typings/` for PySpark compatibility.

## Testing

Tests are organized into:
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/fixtures/` - Test data and fixtures

Run specific test categories:
```bash
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest -m "not slow"       # Skip slow tests
```
EOF

echo -e "${GREEN}"
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Review and update .env file with your settings"
echo "3. Run type checking: ./scripts/type_check.sh"
echo "4. Run tests: ./scripts/run_tests.sh"
echo "5. Format code: ./scripts/format_code.sh"
echo ""
echo "For development workflow, see: docs/DEVELOPMENT.md"
echo -e "${NC}"
