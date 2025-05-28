### P0: Critical Issues (Immediate Attention)

* **[HIGH] Resolve Duplicate `hive-site.xml`:**
* [x] Delete the `hive-site.xml` file at the project root.
* [x] Ensure `configs/hive/hive-site.xml` is the single source of truth.
* [x] Verify and update `docker-compose.yml` (services: `hive-metastore`, `hiveserver2`, `spark-master`, `spark-worker1`, `spark-worker2` ) to use only `configs/hive/hive-site.xml`.
* [x] Check all shell scripts and Spark job submission commands for correct `hive-site.xml` references.
* **[HIGH] Implement Missing Silver Layer ETL Scripts**:
    * [x] Create `clean_harga.py` in `src/etl/silver/` for `harga_pangan.csv`[cite: 144, 428, 894].
        * [x] Handle missing values (`-`) and parse quoted numbers (e.g., `"12,000"`)[cite: 894].
        * [x] Align with schema in `settings.py` (map `harga pangan` to `harga_produsen` and/or `harga_konsumen` or revise schema)[cite: 632, 633, 634].
    * [x] Create `clean_cuaca.py` in `src/etl/silver/` for `cuaca.csv`[cite: 144, 428].
        * [x] Handle missing values (`-`) and placeholders (`8888`)[cite: 563].
        * [x] Address schema mismatch: `cuaca.csv` has `TANGGAL;suhu;curah_hujan`[cite: 563], while `settings.py` expects `kabupaten_kota`, `curah_hujan`, `suhu_rata_rata`, `kelembaban`, `tahun`[cite: 635, 636, 637]. *Resolution: Added `kabupaten_kota` as "Lampung" (province-wide data), mapped `suhu` to `suhu_rata_rata`, set `kelembaban` as null, extracted `tahun` from date.*
    * [x] Create `clean_sosial_ekonomi.py` in `src/etl/silver/` for `sosial_ekonomi.csv`[cite: 428, 463].
        * [x] Handle empty records (lines with only `;;;;`)[cite: 466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489].
        * [x] Ensure column names match `settings.py` (`Kabupaten/Kota` vs `kabupaten_kota`, etc.)[cite: 638, 463].
    * [x] Create `clean_konsumsi_pangan.py` in `src/etl/silver/` for `konsumsi_pangan.csv`[cite: 428, 7].
        * [x] Handle decimal comma (e.g., `125,89`)[cite: 7].
        * [x] Standardize `kabupaten_kota` names[cite: 7].
    * [x] Create `clean_ikp.py` in `src/etl/silver/` for `ikp.csv`[cite: 144, 428, 138].
        * [x] Handle quoted CSV fields and ensure consistent parsing[cite: 138].
        * [x] Handle `#N/A` values for `PERINGKAT KAB/KOTA`[cite: 141].
        * [x] Rename `Nama Kabupaten` to `kabupaten_kota` and `Kode Kab/Kota` if used as part of the cleaning process.
    * [x] Update `run_silver.sh` to execute all new silver layer cleaning scripts[cite: 2041]. (All silver ETL scripts implemented: clean_harga.py, clean_cuaca.py, clean_sosial_ekonomi.py, clean_konsumsi_pangan.py, clean_ikp.py)
* **[HIGH] Address Critical Schema Mismatches**:
    * [x] **Cuaca Data**: Resolved - treated as Lampung province-wide daily weather data. Added `kabupaten_kota` as "Lampung", extracted `tahun` from date column, mapped available columns to expected schema.
    * [x] **Harga Pangan**: Resolved - mapped `harga pangan` to both `harga_produsen` and `harga_konsumen` columns as interim solution until business clarification[cite: 633, 634, 894].

### P1: Missing Implementations & Gaps

* **[MEDIUM] Robust Error Handling in Gold Layer Scripts**:
    * [x] Modify `calc_gold_enriched.py` to handle missing silver tables more gracefully than just returning `None` from `safe_load_table`[cite: 428]. Either enforce dependencies (fail Airflow DAG if a table is missing) or implement logic to correctly proceed with available data, clearly logging what's missing and its impact.
        * [x] Implemented `load_table_with_dependency_check()` with proper error handling and dependency enforcement
        * [x] Added graceful degradation for optional tables with detailed logging of pipeline capabilities
        * [x] Applied "Fail Fast, Fail Loud" principle for required tables (produksi_pangan)
        * [x] Enhanced validation and final dataset verification before completion
        * [x] Fixed SparkSessionManager null reference errors and improved session lifecycle management
        * [x] Applied same robust error handling pattern to `calc_indikator.py`
* **[MEDIUM] Unused `src/cli:main`**:
    * [x] The `pyproject.toml` defines a script `lampung-foodsec = "src.cli:main"`[cite: 857]. However, no `src/cli.py` is provided in the file listing.
    * [x] **Decision**: Removed the script definition from `pyproject.toml` following "Dead Code Gets Buried" principle.

### P2: File System & Structure Cleanup

* **[LOW] Relocate Gold Layer Python Scripts**:
    * [x] Move `calc_indikator.py` from `scripts/` to `src/etl/gold/`[cite: 142, 3].
    * [x] Move `calc_gold_enriched.py` from `scripts/` to `src/etl/gold/`[cite: 425, 3].
    * [x] Update `run_gold.sh` to reflect these new paths (e.g., `docker exec spark-master /spark/bin/spark-submit ... /src/etl/gold/calc_indikator.py`)[cite: 732].
* **[LOW] Review Developer Utility Scripts**:
    * [x] Assess if `scripts/format_code.sh` and `scripts/type_check.sh` are still needed if pre-commit hooks or IDE integrations are adopted project-wide[cite: 594, 596]. *Kept for CI - these provide useful development workflows. Updated paths to exclude moved scripts.*
    * [x] Delete `scripts/cleanup_imports.sh` due to its risky use of `sed` for code modification[cite: 198]. *Removed - relying on `isort` and `flake8`/`pyright` for import management.*
* **[LOW] Ensure `docs/DEVELOPMENT.md` is Version Controlled**:
    * [x] Verify that `docs/DEVELOPMENT.md` (created by `setup_dev_env.sh`) is added to Git[cite: 611]. *Created static `docs/DEVELOPMENT.md` file in repository - no longer generated by setup script.*

### P3: Configuration Management Simplification

* **[MEDIUM] Streamline `settings.py` DATA_SCHEMAS**:
    * [ ] Review and correct all schemas in `src/config/settings.py DATA_SCHEMAS` to accurately reflect the *cleaned silver layer data structure*, not the raw bronze structure[cite: 628]. This includes column names and data types.
    * [ ] For `cuaca` schema in `settings.py`[cite: 635, 636, 637], decide its final structure after addressing the raw data gap.
* **[LOW] Consistency between `.env`, `docker-compose.yml`, and XML configs**:
    * [ ] Minimize direct Hadoop/Hive config overrides in `docker-compose.yml` environment sections if they can be fully managed by the mounted XML files[cite: 665, 669, 678, 693].
    * [ ] Ensure `validate-env.sh` checks all critical environment variables used by `docker-compose.yml`[cite: 168].

### P4: ETL Pipeline Refinements

* **[MEDIUM] Standardize Column Naming and Cleaning**:
    * [ ] Apply `std_kabupaten_kota` (or a similar utility for standardization) within each respective *silver layer* cleaning script, not in the gold layer scripts[cite: 430]. Gold layer should consume already standardized data.
    * [ ] Ensure consistent handling of decimal commas (e.g., in `konsumsi_pangan.csv` [cite: 7]) and other data type conversions in silver scripts.
* **[MEDIUM] Data Validation Points**:
    * [ ] Use the `DataQualityValidator` (or the chosen standardized DQ tool/method) at the end of each silver script to validate output data before writing.
    * [ ] Log quality scores and reports from these validation steps.
* **[LOW] Airflow DAG Improvements**:
    * [ ] Consider making Airflow DAG tasks more granular if specific dataset cleaning fails (e.g., separate tasks for each silver table generation).
    * [ ] For datasets deemed optional for certain gold outputs, reflect this logic in the DAG's branching or task dependencies.
    * [ ] The DAG's `validate_gold_task` currently only checks `gold.ketahanan_pangan_kab`[cite: 461]. Add checks for `gold.ketahanan_pangan_enriched` too.

### P5: Dependency Management

* **[HIGH] Consolidate on `pyproject.toml`**:
    * [x] Make `pyproject.toml` the single source of truth for Python dependencies[cite: 843].
    * [x] Removed `requirements.txt` - no longer needed as `pyproject.toml` is the single source.
* **[MEDIUM] Audit and Prune Dependencies**:
    * [x] Remove `pathlib2` from `pyproject.toml` and `requirements.txt`; use standard `pathlib`[cite: 753, 851].
    * [x] Investigate and remove `pymysql` if no MySQL database is used[cite: 753, 855]. *Removed from main dependencies, kept in optional database group for PostgreSQL only.*
    * [x] Evaluate the necessity of both `great-expectations` and `pandera`[cite: 753, 850]. *Removed both - using custom data validation in `src/utils/data_quality.py` instead.*
    * [x] Remove `configparser` if not actively used for INI files[cite: 753, 850]. *Removed - Python's built-in configparser is sufficient if needed.*
* **[LOW] Review Type Stub Installations**:
    * [ ] `setup_dev_env.sh` mentions skipping `pyspark-stubs` for Python 3.13 compatibility[cite: 579]. Ensure this is still relevant and that type checking for PySpark is adequate with `pyspark`'s own type hints or other stubs if necessary.

### P6: Code Quality & Simplification

* **[MEDIUM] Refactor `setup_dev_env.sh`**:
    * [x] Drastically simplify this script. Its responsibilities for creating venv and installing dependencies via `uv pip install -e ".[dev]"` (or relevant groups) are sufficient[cite: 567, 574]. *Simplified to focus only on venv creation and dependency installation.*
    * [x] Remove code generation parts (e.g., creating `pyrightconfig.json`, `tests/unit/test_config.py`, `tests/conftest.py`, `docs/DEVELOPMENT.md`). These should be static files in the repository. *Code generation removed - created static `docs/DEVELOPMENT.md` as proper documentation.*
    * [x] Guide users via `README.md` for manual steps like copying `.env.example` and running linters/formatters. *Setup script now guides users to copy .env.example manually and use existing utility scripts.*
* **[MEDIUM] Consolidate Data Quality Utilities**:
    * [ ] Merge functionality of `spark_utils.validate_data_quality` into the `DataQualityValidator` class in `data_quality.py` to avoid duplication[cite: 180, 215, 390].
* **[LOW] Logging Consistency**:
    * [ ] Ensure all Python scripts and shell scripts use consistent and informative logging. `src/config/settings.py` defines `LOGGING_CONFIG`[cite: 650]; ensure Python scripts utilize this (e.g., via `logging.config.dictConfig`).

### P7: Testing Enhancements

* **[MEDIUM] Expand Test Coverage**:
    * [ ] Write unit tests for all crucial utility functions in `src/utils/` (especially data cleaning and transformation logic).
    * [ ] Write unit tests for the logic within each ETL script (`clean_*.py`, `calc_*.py`).
    * [ ] Develop integration tests for the silver and gold layer generation processes, verifying data integrity and transformations across stages. Use small, representative test datasets.
    * [ ] Ensure `tests/conftest.py` provides necessary fixtures (like the Spark session) for all tests[cite: 6, 127].
* **[LOW] Test Data Management**:
    * [ ] Store small, sanitized test CSV files in `tests/fixtures/` for reproducible testing of ETL scripts.

### P8: Documentation Updates

* **[MEDIUM] Update `README.md` and `docs/DEVELOPMENT.md`**:
    * Reflect changes made from this TODO list (e.g., simplified setup, corrected paths, consolidated configs).
    * Clearly document the (to-be-completed) data flow for *all* datasets through Bronze, Silver, and Gold layers.
    * Document the final data schemas for each layer.
    * Add troubleshooting steps for common issues.
* **[LOW] Add Docstrings**:
    * Ensure all Python functions, classes, and modules have clear, concise docstrings explaining their purpose, arguments, and return values, as seen in many of the utility functions already[cite: 212, 1946].

### P9: Shell Script Refinements

* **[MEDIUM] ETL Script Execution Paths**:
    * Modify `run_gold.sh` to execute Python scripts from their new location in `src/etl/gold/`[cite: 732].
    * Modify `run_silver.sh` to correctly call all (newly created) silver ETL scripts from `src/etl/silver/`[cite: 2041].
* **[LOW] Review `start-system.sh` Permissions**:
    * The script uses `chmod -R 777` and then `sudo chown` for `data/yarn/local`[cite: 189]. While this might be a workaround for container user permission issues, investigate if more specific permissions can be set or if user mapping in Docker Compose can solve this more cleanly.
    * `sudo chown -R 50000:0 logs dags` is also present[cite: 189, 190]. Ensure this UID/GID is consistent and correctly matches the Airflow container's user requirements.
