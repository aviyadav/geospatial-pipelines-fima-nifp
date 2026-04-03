# Geospatial Pipelines for FIMA NFIP Data

This project demonstrates efficient geospatial data processing pipelines for aggregating and analyzing Federal Insurance and Mitigation Administration (FIMA) National Flood Insurance Program (NFIP) claims and policies data at the county level in the United States.

## Overview

The pipeline performs the following operations:
1. Loads NFIP claims and policies data from Parquet files.
2. Aggregates data by county (GEOID).
3. Merges aggregated data with US county shapefiles for spatial analysis.
4. Compares performance across different data processing libraries: pandas, Polars, and DuckDB.

The project highlights the performance benefits of using optimized libraries like DuckDB for large-scale geospatial data processing.

## Data Sources

- **NFIP Claims**: `FimaNfipClaimsV2.parquet` from [FEMA OpenFEMA API](https://www.fema.gov/about/reports-and-data/openfema/v2/FimaNfipClaimsV2.parquet)
- **NFIP Policies**: `FimaNfipPoliciesV2.parquet` from [FEMA OpenFEMA API](https://www.fema.gov/about/reports-and-data/openfema/v2/FimaNfipPoliciesV2.parquet)
- **US Counties Shapefile**: `tl_2025_us_county` from [US Census Bureau TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)

## Dependencies

- Python >= 3.14
- duckdb >= 1.5.1
- geopandas >= 1.1.3
- pandas >= 3.0.2
- polars >= 1.39.3
- pyarrow >= 23.0.1

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd geospatial-pipelines-fima-nifp
   ```

2. Install dependencies using uv (or pip):
   ```bash
   uv sync
   # or
   pip install -r requirements.txt
   ```

3. Ensure data files are in the `data/` directory:
   - `FimaNfipClaimsV2.parquet`
   - `FimaNfipPoliciesV2.parquet`
   - `tl_2025_us_county/` (shapefile directory)

## Usage

Run the main script to execute the pipelines:

```bash
python main.py
```

The script includes three implementations:
- `pandas_play()`: Uses pandas for data processing (single-threaded).
- `polars_play()`: Uses Polars for data processing (multi-threaded).
- `duckdb_play()`: Uses DuckDB with spatial extensions for unified SQL-based processing.

By default, `duckdb_play()` is executed, which is the most efficient.

## Performance Comparison

Based on sample runs:
- Pandas: ~87 seconds
- Polars: ~27 seconds
- DuckDB: ~2 seconds

DuckDB's columnar storage and vectorized execution make it particularly suited for large geospatial datasets.

## Project Structure

- `main.py`: Main script with pipeline implementations.
- `data/`: Directory containing input data files.
- `pyproject.toml`: Project configuration and dependencies.
- `README.md`: This file.

## Contributing

Contributions are welcome. Please ensure code follows best practices and includes appropriate tests.

## License

[Specify license if applicable]