"""
Data quality validation utilities for Lampung Food Security Big Data System
"""

import logging
from typing import Any, Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql.functions import abs as spark_abs
from pyspark.sql.functions import avg, col, countDistinct, isnan
from pyspark.sql.functions import max as spark_max
from pyspark.sql.functions import min as spark_min
from pyspark.sql.functions import percentile_approx, regexp_replace, stddev, trim, when

from config.settings import DATA_SCHEMAS, QUALITY_CONFIG

# Type imports removed as they're unused in this module


logger = logging.getLogger(__name__)


class DataQualityValidator:
    """Comprehensive data quality validation for ETL pipelines"""

    def __init__(self, df: DataFrame, dataset_name: str):
        self.df = df
        self.dataset_name = dataset_name
        self.validation_results: Dict[str, Any] = {}

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all data quality validations"""
        logger.info(f"Starting data quality validation for {self.dataset_name}")

        self.validation_results = {
            "dataset": self.dataset_name,
            "row_count": self.df.count(),
            "column_count": len(self.df.columns),
            "schema_validation": self.validate_schema(),
            "completeness": self.check_completeness(),
            "uniqueness": self.check_uniqueness(),
            "validity": self.check_validity(),
            "consistency": self.check_consistency(),
            "outliers": self.detect_outliers(),
            "data_profiling": self.profile_data(),
        }

        logger.info(f"Data quality validation completed for {self.dataset_name}")
        return self.validation_results

    def validate_schema(self) -> Dict[str, Any]:
        """Validate schema against expected structure"""
        expected_columns = DATA_SCHEMAS.get("bronze", {}).get(self.dataset_name, [])
        actual_columns = self.df.columns

        missing_columns = set(expected_columns) - set(actual_columns)
        extra_columns = set(actual_columns) - set(expected_columns)

        return {
            "expected_columns": expected_columns,
            "actual_columns": actual_columns,
            "missing_columns": list(missing_columns),
            "extra_columns": list(extra_columns),
            "schema_valid": len(missing_columns) == 0,
        }

    def check_completeness(self) -> Dict[str, Any]:
        """Check data completeness (missing values)"""
        total_rows = self.df.count()
        completeness_stats = {}

        for column in self.df.columns:
            null_count = self.df.filter(
                col(column).isNull() | isnan(col(column))
            ).count()
            completeness_stats[column] = {
                "null_count": null_count,
                "null_percentage": (
                    (null_count / total_rows) * 100 if total_rows > 0 else 0
                ),
                "completeness_score": (
                    ((total_rows - null_count) / total_rows) * 100
                    if total_rows > 0
                    else 0
                ),
            }

        overall_completeness = sum(
            stats["completeness_score"] for stats in completeness_stats.values()
        ) / len(completeness_stats)

        return {
            "column_stats": completeness_stats,
            "overall_completeness": overall_completeness,
            "completeness_threshold_met": overall_completeness >= 90,
        }

    def check_uniqueness(self) -> Dict[str, Any]:
        """Check data uniqueness and identify duplicates"""
        total_rows = self.df.count()
        unique_rows = self.df.dropDuplicates().count()
        duplicate_count = total_rows - unique_rows

        # Check uniqueness for key columns
        key_columns = ["kabupaten_kota", "tahun"]
        if self.dataset_name in ["produksi_pangan", "harga_pangan", "konsumsi_pangan"]:
            key_columns.append("komoditas")

        existing_key_columns = [col for col in key_columns if col in self.df.columns]
        key_duplicates = 0
        if existing_key_columns:
            unique_key_rows = self.df.dropDuplicates(existing_key_columns).count()
            key_duplicates = total_rows - unique_key_rows

        return {
            "total_rows": total_rows,
            "unique_rows": unique_rows,
            "duplicate_count": duplicate_count,
            "duplicate_percentage": (
                (duplicate_count / total_rows) * 100 if total_rows > 0 else 0
            ),
            "key_columns": existing_key_columns,
            "key_duplicates": key_duplicates,
            "uniqueness_score": (
                (unique_rows / total_rows) * 100 if total_rows > 0 else 0
            ),
        }

    def check_validity(self) -> Dict[str, Any]:
        """Check data validity (format, range, constraints)"""
        validity_stats: Dict[str, Any] = {}
        invalid_markers = QUALITY_CONFIG["invalid_markers"]

        for column in self.df.columns:
            column_type = dict(self.df.dtypes)[column]
            validity_stats[column] = {
                "data_type": column_type,
                "invalid_values": 0,
                "format_issues": [],
            }

            # Check for invalid markers
            for marker in invalid_markers:
                if marker:  # Skip empty strings
                    invalid_count = self.df.filter(col(column) == marker).count()
                    validity_stats[column]["invalid_values"] = (
                        validity_stats[column]["invalid_values"] + invalid_count
                    )
                    if invalid_count > 0:
                        validity_stats[column]["format_issues"].append(
                            f"Found {invalid_count} instances of '{marker}'"
                        )

            # Type-specific validations
            if "int" in column_type.lower() or "double" in column_type.lower():
                # Check for negative values where they shouldn't exist
                if column in [
                    "produksi",
                    "luas_panen",
                    "harga_produsen",
                    "harga_konsumen",
                    "jumlah_penduduk",
                ]:
                    negative_count = self.df.filter(col(column) < 0).count()
                    if negative_count > 0:
                        validity_stats[column]["format_issues"].append(
                            f"Found {negative_count} negative values"
                        )
                        validity_stats[column]["invalid_values"] = (
                            validity_stats[column]["invalid_values"] + negative_count
                        )

            # Year validation
            if column == "tahun":
                invalid_years = self.df.filter(
                    (col(column) < 2000) | (col(column) > 2030)
                ).count()
                if invalid_years > 0:
                    validity_stats[column]["format_issues"].append(
                        f"Found {invalid_years} invalid year values"
                    )
                    validity_stats[column]["invalid_values"] = (
                        validity_stats[column]["invalid_values"] + invalid_years
                    )

        total_cells = self.df.count() * len(self.df.columns)
        total_invalid = sum(
            stats["invalid_values"] for stats in validity_stats.values()
        )

        return {
            "column_stats": validity_stats,
            "total_invalid_values": total_invalid,
            "validity_score": (
                ((total_cells - total_invalid) / total_cells) * 100
                if total_cells > 0
                else 0
            ),
            "validity_threshold_met": (
                total_invalid / total_cells < 0.05 if total_cells > 0 else True
            ),
        }

    def check_consistency(self) -> Dict[str, Any]:
        """Check data consistency across columns and records"""
        consistency_issues = []

        # Check kabupaten_kota consistency (standardized naming)
        if "kabupaten_kota" in self.df.columns:
            inconsistent_naming = (
                self.df.groupBy("kabupaten_kota")
                .count()
                .filter(col("count") < 5)
                .count()
            )
            if inconsistent_naming > 0:
                consistency_issues.append(
                    f"Found {inconsistent_naming} kabupaten_kota values with "
                    f"low frequency (possible naming inconsistencies)"
                )

        # Check year consistency
        if "tahun" in self.df.columns:
            year_range = self.df.agg(
                spark_min("tahun").alias("min_year"),
                spark_max("tahun").alias("max_year"),
            ).collect()[0]
            year_gap = year_range["max_year"] - year_range["min_year"]
            if year_gap > 15:
                consistency_issues.append(
                    f"Large year range detected: {year_range['min_year']} to "
                    f"{year_range['max_year']}"
                )

        # Check production vs area consistency
        if all(
            col in self.df.columns
            for col in ["produksi", "luas_panen", "produktivitas"]
        ):
            inconsistent_prod = self.df.filter(
                (col("produksi") > 0)
                & (col("luas_panen") > 0)
                & (
                    spark_abs(
                        col("produktivitas") - (col("produksi") / col("luas_panen"))
                    )
                    > 0.1
                )
            ).count()
            if inconsistent_prod > 0:
                consistency_issues.append(
                    f"Found {inconsistent_prod} records with inconsistent "
                    f"production calculations"
                )

        return {
            "consistency_issues": consistency_issues,
            "consistency_score": 100 - len(consistency_issues) * 10,  # Rough
            "consistency_threshold_met": len(consistency_issues) <= 2,
        }

    def detect_outliers(self) -> Dict[str, Any]:
        """Detect statistical outliers in numeric columns"""
        outlier_stats = {}

        numeric_columns = [
            col_name
            for col_name, col_type in self.df.dtypes
            if "int" in col_type.lower() or "double" in col_type.lower()
        ]

        for column in numeric_columns:
            if column == "tahun":  # Skip year column
                continue

            stats = self.df.select(
                avg(col(column)).alias("mean"),
                stddev(col(column)).alias("stddev"),
                percentile_approx(col(column), 0.25).alias("q1"),
                percentile_approx(col(column), 0.75).alias("q3"),
            ).collect()[0]

            if stats["stddev"] is not None:
                # IQR method
                iqr = stats["q3"] - stats["q1"]
                lower_bound = stats["q1"] - 1.5 * iqr
                upper_bound = stats["q3"] + 1.5 * iqr

                outlier_count = self.df.filter(
                    (col(column) < lower_bound) | (col(column) > upper_bound)
                ).count()

                # Z-score method (|z| > 3)
                z_score_outliers = self.df.filter(
                    ((col(column) - stats["mean"]) / stats["stddev"]) > 3
                ).count()

                outlier_stats[column] = {
                    "iqr_outliers": outlier_count,
                    "z_score_outliers": z_score_outliers,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "outlier_percentage": (
                        (outlier_count / self.df.count()) * 100
                        if self.df.count() > 0
                        else 0
                    ),
                }

        return outlier_stats

    def profile_data(self) -> Dict[str, Any]:
        """Generate comprehensive data profile"""
        profile: Dict[str, Any] = {
            "basic_stats": {},
            "categorical_stats": {},
            "numerical_stats": {},
        }

        for column in self.df.columns:
            col_type = dict(self.df.dtypes)[column]

            # Basic stats for all columns
            profile["basic_stats"][column] = {
                "data_type": col_type,
                "distinct_count": self.df.select(countDistinct(col(column))).collect()[
                    0
                ][0],
                "null_count": self.df.filter(col(column).isNull()).count(),
            }

            # Categorical stats
            if "string" in col_type.lower():
                top_values = (
                    self.df.groupBy(column)
                    .count()
                    .orderBy(col("count"))
                    .limit(5)
                    .collect()
                )
                profile["categorical_stats"][column] = {
                    "top_values": [(row[column], row["count"]) for row in top_values],
                    "cardinality": len(top_values),
                }

            # Numerical stats
            elif "int" in col_type.lower() or "double" in col_type.lower():
                num_stats = self.df.select(
                    spark_min(col(column)).alias("min"),
                    spark_max(col(column)).alias("max"),
                    avg(col(column)).alias("mean"),
                    stddev(col(column)).alias("stddev"),
                ).collect()[0]

                profile["numerical_stats"][column] = {
                    "min": num_stats["min"],
                    "max": num_stats["max"],
                    "mean": num_stats["mean"],
                    "stddev": num_stats["stddev"],
                }

        return profile


def validate_bronze_data(df: DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Validate bronze layer data"""
    validator = DataQualityValidator(df, dataset_name)
    return validator.run_all_validations()


def clean_invalid_markers(
    df: DataFrame, columns: Optional[List[str]] = None
) -> DataFrame:
    """Remove or replace invalid data markers"""
    invalid_markers = QUALITY_CONFIG["invalid_markers"]
    target_columns = columns if columns is not None else df.columns

    cleaned_df = df
    for column in target_columns:
        if column in df.columns:
            for marker in invalid_markers:
                if marker:  # Skip empty strings
                    cleaned_df = cleaned_df.withColumn(
                        column, when(col(column) == marker, None).otherwise(col(column))
                    )

    return cleaned_df


def standardize_region_names(
    df: DataFrame, region_column: str = "kabupaten_kota"
) -> DataFrame:
    """Standardize region name formatting"""
    if region_column not in df.columns:
        return df

    return df.withColumn(
        region_column,
        trim(
            regexp_replace(
                regexp_replace(col(region_column), r"[^a-zA-Z0-9\s]", ""), r"\s+", " "
            )
        ),
    )


def calculate_data_quality_score(validation_results: Dict[str, Any]) -> float:
    """Calculate overall data quality score"""
    weights = {
        "completeness": 0.25,
        "validity": 0.25,
        "uniqueness": 0.20,
        "consistency": 0.20,
        "schema": 0.10,
    }

    scores = {
        "completeness": validation_results.get("completeness", {}).get(
            "overall_completeness", 0
        ),
        "validity": validation_results.get("validity", {}).get("validity_score", 0),
        "uniqueness": validation_results.get("uniqueness", {}).get(
            "uniqueness_score", 0
        ),
        "consistency": validation_results.get("consistency", {}).get(
            "consistency_score", 0
        ),
        "schema": (
            100
            if validation_results.get("schema_validation", {}).get(
                "schema_valid", False
            )
            else 0
        ),
    }

    weighted_score = sum(
        float(scores[metric]) * weights[metric] for metric in weights.keys()
    )
    return round(weighted_score, 2)


def generate_quality_report(validation_results: Dict[str, Any]) -> str:
    """Generate human-readable data quality report"""
    dataset = validation_results.get("dataset", "Unknown")
    overall_score = calculate_data_quality_score(validation_results)

    # Get validation details
    schema_valid = validation_results.get("schema_validation", {}).get(
        "schema_valid", False
    )
    missing_cols = validation_results.get("schema_validation", {}).get(
        "missing_columns", []
    )
    completeness = validation_results.get("completeness", {}).get(
        "overall_completeness", 0
    )
    validity = validation_results.get("validity", {}).get("validity_score", 0)
    uniqueness = validation_results.get("uniqueness", {}).get("uniqueness_score", 0)
    consistency = validation_results.get("consistency", {}).get("consistency_score", 0)
    duplicates = validation_results.get("uniqueness", {}).get("duplicate_count", 0)
    invalid_values = validation_results.get("validity", {}).get(
        "total_invalid_values", 0
    )
    consistency_issues = len(
        validation_results.get("consistency", {}).get("consistency_issues", [])
    )

    # Determine quality status
    if overall_score >= 80:
        status = "PASS"
    elif overall_score >= 60:
        status = "REVIEW REQUIRED"
    else:
        status = "FAIL"

    report = f"""
    DATA QUALITY REPORT - {dataset.upper()}
    {'='*50}

    Overall Quality Score: {overall_score}/100

    Dataset Overview:
    - Rows: {validation_results.get('row_count', 0):,}
    - Columns: {validation_results.get('column_count', 0)}

    Schema Validation:
    - Valid: {schema_valid}
    - Missing columns: {missing_cols}

    Data Completeness: {completeness:.1f}%
    Data Validity: {validity:.1f}%
    Data Uniqueness: {uniqueness:.1f}%
    Data Consistency: {consistency:.1f}%

    Issues Found:
    - Duplicates: {duplicates}
    - Invalid values: {invalid_values}
    - Consistency issues: {consistency_issues}

    Quality Status: {status}
    """

    return report
