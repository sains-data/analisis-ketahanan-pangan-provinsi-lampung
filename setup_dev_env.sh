#!/bin/bash

# Lampung Food Security Development Environment Setup Script
# Simplified setup focusing only on virtual environment and dependency installation

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

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${RED}Error: Python 3.8+ is required. Found: ${PYTHON_VERSION}${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
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

# Upgrade pip and install uv for faster package management
echo -e "${BLUE}Upgrading pip and installing uv...${NC}"
.venv/bin/pip install --upgrade pip setuptools wheel
.venv/bin/pip install uv

# Install project dependencies
echo -e "${BLUE}Installing project dependencies...${NC}"
.venv/bin/uv pip install -e ".[dev,airflow,database,jupyter,monitoring]"

# Install type stubs (skip pyspark-stubs for Python 3.13 compatibility)
echo -e "${BLUE}Installing type stubs...${NC}"
.venv/bin/uv pip install types-requests types-PyYAML || echo -e "${YELLOW}Some type stubs may not be available${NC}"

# Set up Python path in virtual environment
echo -e "${BLUE}Configuring Python path...${NC}"
echo "export PYTHONPATH=\"$(pwd)/src:\$PYTHONPATH\"" >> .venv/bin/activate

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

echo -e "${GREEN}"
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Copy .env.example to .env and update with your settings"
echo "3. Run code formatting: ./scripts/format_code.sh"
echo "4. Run type checking: ./scripts/type_check.sh"
echo "5. Run tests: ./scripts/run_tests.sh"
echo -e "${NC}"