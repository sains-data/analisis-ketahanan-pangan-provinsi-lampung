#!/bin/bash
echo "Formatting code with black..."
black src/ dags/ --line-length 88

echo "Sorting imports with isort..."
isort src/ dags/ --profile black

echo "Running flake8 checks..."
flake8 src/ dags/ --max-line-length=88 --extend-ignore=E203,W503

echo "Code formatting complete!"
