#!/bin/bash
echo "Running tests with pytest..."
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

echo "Tests complete! Coverage report available in htmlcov/"
