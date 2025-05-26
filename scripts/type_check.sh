#!/bin/bash
echo "Running type checks with pyright..."
pyright

echo "Running mypy checks..."
mypy src/ --ignore-missing-imports

echo "Type checking complete!"
