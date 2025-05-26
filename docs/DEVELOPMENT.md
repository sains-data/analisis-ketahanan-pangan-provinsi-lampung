# Panduan Pengembangan

## Setup

Jalankan script setup:
```bash
./setup_dev_env.sh
```

Aktifkan virtual environment:
```bash
source .venv/bin/activate
```

## Workflow Pengembangan

1. **Format Kode**:
   ```bash
   ./scripts/format_code.sh
   ```

2. **Type Checking**:
   ```bash
   ./scripts/type_check.sh
   ```

3. **Menjalankan Tests**:
   ```bash
   ./scripts/run_tests.sh
   ```

4. **Quality Checks Manual**:
   Jalankan quality tools sesuai kebutuhan:
   ```bash
   ./scripts/format_code.sh && ./scripts/type_check.sh
   ```

## Setup IDE

### VS Code
Pasang ekstensi berikut:
- Python
- Pylance
- Black Formatter
- isort

### PyCharm
Konfigurasi:
- Python interpreter: `.venv/bin/python`
- Code style: Black
- Import sorting: isort

## Struktur Proyek

```
src/
├── config/          # Manajemen konfigurasi
├── utils/           # Utilitas umum
└── etl/            # Kode pipeline ETL

scripts/            # Script operasional
dags/              # Airflow DAGs
tests/             # File test
docs/              # Dokumentasi
```

## Type Checking

Proyek menggunakan Pyright untuk type checking. Type stubs disediakan di `typings/` untuk kompatibilitas PySpark.

## Testing

Test diorganisir menjadi:
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/fixtures/` - Data test dan fixtures

Jalankan kategori test tertentu:
```bash
pytest tests/unit/          # Unit tests saja
pytest tests/integration/   # Integration tests saja
pytest -m "not slow"       # Lewati slow tests
```