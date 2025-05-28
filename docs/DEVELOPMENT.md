# Development Guide

## Quick Setup

1. **Clone and Setup Environment**:
   ```bash
   git clone <repository-url>
   cd lampung-food-security
   ./setup_dev_env.sh
   ```

2. **Activate Virtual Environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your specific settings
   ```

## Development Workflow

### Code Quality Tools

1. **Format Code**:
   ```bash
   ./scripts/format_code.sh
   ```

2. **Type Checking**:
   ```bash
   ./scripts/type_check.sh
   ```

3. **Run Tests**:
   ```bash
   ./scripts/run_tests.sh
   ```

4. **Complete Quality Check**:
   ```bash
   ./scripts/format_code.sh && ./scripts/type_check.sh && ./scripts/run_tests.sh
   ```

### System Operations

1. **Start System**:
   ```bash
   ./start-system.sh
   ```

2. **Run ETL Pipelines**:
   ```bash
   ./run_bronze.sh    # Load raw data
   ./run_silver.sh    # Clean and standardize
   ./run_gold.sh      # Calculate indicators
   ```

3. **Validate Environment**:
   ```bash
   ./validate-env.sh
   ```

## Project Structure

```
lampung-food-security/
├── src/
│   ├── config/          # Configuration management
│   ├── utils/           # Common utilities
│   └── etl/
│       ├── silver/      # Data cleaning scripts
│       └── gold/        # Analytics and indicators
├── scripts/             # Utility scripts
├── dags/               # Airflow DAGs
├── tests/              # Test files
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test data
├── configs/            # Hadoop/Hive/Spark configs
├── data/               # Local data storage
└── docs/               # Documentation
```

## Development Standards

### Python Standards
- **Black** for code formatting (88 characters)
- **isort** for import sorting
- **Pyright** for type checking
- **pytest** for testing with 80% coverage minimum

### Architecture Layers
1. **Bronze**: Raw data ingestion (CSV → HDFS)
2. **Silver**: Cleaned, standardized data (Parquet)
3. **Gold**: Business metrics and indicators

### Data Quality Rules
- All silver scripts must validate output data
- Required columns must be present
- Business rules enforced in gold layer
- Custom validation in `src/utils/data_quality.py`

## IDE Setup

### VS Code
Install extensions:
- Python
- Pylance
- Black Formatter
- isort

### PyCharm
Configure:
- Python interpreter: `.venv/bin/python`
- Code style: Black
- Import sorting: isort

## Testing

### Test Categories
- **Unit tests**: `pytest tests/unit/`
- **Integration tests**: `pytest tests/integration/`
- **Specific markers**: `pytest -m "not slow"`

### Test Data
- Use small fixtures in `tests/fixtures/`
- Mock external services for unit tests
- Integration tests use Docker services

## System Dependencies

### Required Services (Docker)
- Hadoop (HDFS, YARN)
- Hive (Metastore, HiveServer2)
- Spark (Master, Workers)
- Airflow (Scheduler, Webserver)

### Local Development
- Python 3.8+
- Docker & Docker Compose
- uv (for fast package management)

## Common Tasks

### Adding New Data Source
1. Create silver cleaning script in `src/etl/silver/`
2. Add schema to `src/config/settings.py`
3. Update `run_silver.sh`
4. Add tests and validation

### Debugging ETL Issues
1. Check HDFS: `docker exec namenode hdfs dfs -ls /data/`
2. Check Hive tables: `docker exec hiveserver2 beeline -u jdbc:hive2://hiveserver2:10000 -e "SHOW TABLES;"`
3. Review logs: `docker logs <container-name>`

### Performance Optimization
1. Monitor Spark UI: http://localhost:8080
2. Check resource usage: `docker stats`
3. Profile with memory-profiler if needed

## Troubleshooting

### Common Issues
- **Permission errors**: Check `start-system.sh` for proper ownership
- **Import errors**: Verify PYTHONPATH in `.venv/bin/activate`
- **Type checking**: Install type stubs with `uv pip install types-*`

### Environment Problems
- Run `./validate-env.sh` to check configuration
- Ensure all services are healthy: `docker ps`
- Check port conflicts (8080, 9000, 10000, etc.)

## Contributing

1. Follow the project rules in the codebase
2. Write tests for new functionality
3. Update documentation for API changes
4. Run full quality checks before committing
5. Keep commits focused and well-described