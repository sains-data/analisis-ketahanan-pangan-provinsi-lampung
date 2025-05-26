# Panduan Type Checking untuk Proyek Big Data

## Gambaran Umum

Type checking dalam proyek big data menghadirkan tantangan unik karena environment yang dikontainerisasi, dependensi eksternal seperti PySpark dan Airflow, dan sifat dinamis dari framework komputasi terdistribusi. Panduan ini menyediakan strategi praktis untuk type checking yang efektif dalam proyek Ketahanan Pangan Lampung.

## Tantangan dalam Type Checking Big Data

### 1. Dependensi yang Dikontainerisasi
- **PySpark** dan **Airflow** berjalan di dalam container Docker
- Environment pengembangan lokal mungkin tidak memiliki package ini terinstall
- Type checker tidak dapat resolve import yang hanya ada di container

### 2. Perilaku Framework yang Dinamis
- Spark DataFrame memiliki schema yang dinamis
- Operasi kolom di-resolve saat runtime
- Informasi type seringkali tidak lengkap

### 3. Integrasi JVM
- PySpark berinterface dengan library Java/Scala
- Informasi type mungkin hilang di batas bahasa
- Beberapa operasi mengembalikan tipe `Any` generik

## Strategi Konfigurasi

### Konfigurasi Pyright (`pyrightconfig.json`)

```json
{
    "typeCheckingMode": "basic",
    "reportMissingImports": "warning",
    "reportMissingTypeStubs": "none",
    "reportUnknownParameterType": "none",
    "reportUnknownVariableType": "none",
    "reportUnknownMemberType": "none",
    "stubPath": "typings"
}
```

### Konfigurasi MyPy (`pyproject.toml`)

```toml
[tool.mypy]
ignore_missing_imports = true
check_untyped_defs = true
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = ["pyspark.*", "airflow.*"]
ignore_missing_imports = true
```

## Best Practices Type Annotation

### 1. Gunakan String Literals untuk Forward References

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import DataFrame

def process_data(df: "DataFrame") -> "DataFrame":
    return df.filter(df.col > 0)
```

### 2. Buat Type Stubs untuk Komponen Kritis

```python
# typings/pyspark/sql/__init__.pyi
class DataFrame:
    def filter(self, condition: Union[str, Column]) -> DataFrame: ...
    def select(self, *cols: Union[str, Column]) -> DataFrame: ...
```

### 3. Gunakan Union Types untuk Konfigurasi

```python
from typing import Union, Dict, Any

ConfigValue = Union[str, int, bool, float]
Config = Dict[str, ConfigValue]
```

### 4. Anotasi Return Types untuk Fungsi Kompleks

```python
def read_csv_from_hdfs(
    spark: SparkSession,
    file_path: str,
    **kwargs: Any
) -> "DataFrame":
    """Baca CSV dengan type annotation yang proper"""
    return spark.read.csv(file_path, **kwargs)
```

## Menangani Jenis Warning Umum

### 1. Missing Import Warnings

**Status**: Diharapkan - ini hanya warning
```python
# Ini akan menunjukkan warning tapi dapat diterima
from pyspark.sql import SparkSession  # warning: Import "pyspark.sql" could not be resolved
```

**Solusi**: Konfigurasi sebagai warning di `pyrightconfig.json`

### 2. Unknown Attribute Access

**Masalah**:
```python
df.filter(col("name") == "value")  # Error: Cannot access attribute "filter"
```

**Solusi**: Gunakan string literals atau suppress
```python
df: "DataFrame" = spark.table("my_table")
df.filter(col("name") == "value")  # Sekarang properly typed
```

### 3. Configuration Type Issues

**Masalah**:
```python
config_value = CONFIG["key"]  # Type is unknown
some_function(config_value)   # Type mismatch
```

**Solusi**: Explicit casting
```python
config_value = str(CONFIG["key"])
some_function(config_value)
```

## Workflow Pengembangan

### 1. Manual Type Checking

```bash
# Jalankan sebelum commit
pyright
mypy src/ --ignore-missing-imports
```

### 2. Level Warning yang Dapat Diterima

**Green Zone** (Dapat Diterima):
- `reportMissingImports` untuk PySpark/Airflow
- `reportMissingTypeStubs` untuk library eksternal
- `reportUnknownMemberType` untuk operasi dinamis

**Yellow Zone** (Review):
- `reportUnusedVariable` dalam script ETL
- `reportUnusedImport` untuk debugging imports

**Red Zone** (Harus Diperbaiki):
- `reportUndefinedVariable`
- `reportCallIssue` dengan tipe argumen yang salah
- `reportAttributeAccessIssue` pada tipe yang diketahui

### 3. Menekan Warning Spesifik

```python
# Type: ignore untuk baris tertentu
result = some_dynamic_operation()  # type: ignore[reportUnknownMemberType]

# Disable untuk seluruh file
# pyright: reportMissingImports=false
```

## Pola Spesifik Proyek

### 1. Manajemen Spark Session

```python
class SparkSessionManager:
    _instance: Optional[SparkSession] = None

    @classmethod
    def get_session(cls, app_name: str) -> SparkSession:
        if cls._instance is None:
            cls._instance = SparkSession.builder.appName(app_name).getOrCreate()
        return cls._instance
```

### 2. Type Safety Konfigurasi

```python
from typing import TypedDict

class SparkConfig(TypedDict):
    app_name: str
    master: str
    warehouse_dir: str

SPARK_CONFIG: SparkConfig = {
    "app_name": "LampungFoodSecurity",
    "master": "spark://spark-master:7077",
    "warehouse_dir": "hdfs://namenode:9000/user/hive/warehouse"
}
```

### 3. Operasi DataFrame dengan Type Hints

```python
def clean_production_data(df: "DataFrame") -> "DataFrame":
    """Bersihkan data produksi dengan type safety"""
    return (df
        .filter(col("produksi") > 0)
        .withColumn("produktivitas_per_ha", col("produksi") / col("luas_panen"))
        .dropDuplicates()
    )
```

## Testing Type Annotations

### 1. Runtime Type Checking

```python
import pytest
from typing import get_type_hints

def test_function_annotations():
    """Verifikasi fungsi memiliki type annotation yang proper"""
    hints = get_type_hints(clean_production_data)
    assert 'return' in hints
```

### 2. Mock Objects untuk Testing

```python
from unittest.mock import Mock, MagicMock

@pytest.fixture
def mock_spark_session():
    """Mock Spark session untuk test type checking"""
    session = Mock(spec=SparkSession)
    session.read.csv.return_value = Mock(spec=DataFrame)
    return session
```

## Konfigurasi IDE

### Settings VS Code

```json
{
    "python.linting.pyrightEnabled": true,
    "python.linting.mypyEnabled": false,
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true
}
```

### Settings PyCharm

1. Pergi ke Settings → Editor → Inspections → Python
2. Aktifkan inspeksi "Type checker"
3. Konfigurasi level severity untuk berbagai jenis warning
4. Setup external tools untuk pyright

## Pertimbangan Performa

### 1. Kecepatan Type Checking

- Gunakan `typeCheckingMode: "basic"` untuk check yang lebih cepat
- Eksklusi direktori data besar dari type checking
- Cache hasil type checking di CI/CD

### 2. Penggunaan Memory

```python
# Hindari dalam type annotations - dapat menyebabkan masalah memory
from typing import List
huge_list: List[DataFrame] = []  # Hindari ini

# Pendekatan yang lebih baik
from typing import Sequence
data_sequence: Sequence["DataFrame"] = []
```

## Continuous Integration

### Contoh GitHub Actions

```yaml
- name: Type Check
  run: |
    source .venv/bin/activate
    pyright --outputjson > type-check-results.json || true
    python scripts/parse-type-results.py
```

### Quality Gates

- **Block merge** pada error red-zone
- **Warn on** masalah yellow-zone
- **Allow** warning green-zone

## Troubleshooting

### Masalah dan Solusi Umum

1. **"Cannot resolve import"**
   - Periksa apakah module ada di virtual environment
   - Tambahkan ke `pyrightconfig.json` excludes jika dikontainerisasi

2. **"Unknown attribute"**
   - Buat type stub di direktori `typings/`
   - Gunakan string literal type annotations

3. **"Type mismatch in configuration"**
   - Tambahkan explicit type casting
   - Gunakan TypedDict untuk struktur konfigurasi

4. **"Too many warnings"**
   - Sesuaikan `typeCheckingMode` dari "strict" ke "basic"
   - Konfigurasi level warning spesifik

### Debug Commands

```bash
# Periksa konfigurasi pyright
pyright --version
pyright --help

# Verbose type checking
pyright --verbose

# Periksa file spesifik
pyright src/utils/spark_utils.py

# Generate type stub
pyright --createstub pyspark
```

## Ringkasan Best Practices

1. **Terima warning import PySpark** - ini diharapkan dalam environment yang dikontainerisasi
2. **Gunakan string literals** untuk DataFrame dan anotasi tipe kompleks
3. **Buat type stubs** untuk library eksternal yang sering digunakan
4. **Konfigurasi level warning yang tepat** - ketat untuk kode Anda, longgar untuk dependensi eksternal
5. **Fokus pada tipe logic business** daripada internal framework
6. **Gunakan explicit casting** untuk nilai konfigurasi
7. **Test type annotations** dengan runtime checks jika memungkinkan
8. **Dokumentasikan keputusan type checking** dalam komentar kode

Tujuannya adalah menangkap error nyata sambil mempertahankan velocity pengembangan, bukan mencapai 100% type coverage dalam environment big data.