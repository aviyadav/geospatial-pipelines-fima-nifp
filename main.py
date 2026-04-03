import time

import duckdb
import geopandas as gpd
import pandas as pd
import polars as pl


def pandas_play():

    start = time.time()

    # 1. Read files into RAM

    con = duckdb.connect()

    claims_df = con.execute("""
        SELECT countyCode, netBuildingPaymentAmount
        FROM read_parquet('data/FimaNfipClaimsV2.parquet')
    """).df()

    policies_df = con.execute("""
        SELECT countyCode, policyCount, totalBuildingInsuranceCoverage
        FROM read_parquet('data/FimaNfipPoliciesV2.parquet')
    """).df()

    con.close()

    # 2. Aggregate millions of rows (Single-threaded)
    claims_agg = (
        claims_df.dropna(subset=["countyCode"])
        .groupby("countyCode")
        .agg(avg_claim_amt=("netBuildingPaymentAmount", "sum"))
        .reset_index()
    )

    policies_agg = (
        policies_df.dropna(subset=["countyCode"])
        .groupby("countyCode")
        .agg(
            total_policies=("policyCount", "sum"),
            avg_coverage=("totalBuildingInsuranceCoverage", "sum"),
        )
        .reset_index()
    )

    # 3. Clean and join
    agg_df = pd.merge(claims_agg, policies_agg, on="countyCode", how="outer")
    agg_df = agg_df.rename(columns={"countyCode": "GEOID"})
    agg_df["GEOID"] = agg_df["GEOID"].astype(str).str.zfill(5)

    # 4. Spatial Merge
    counties = gpd.read_file("data/tl_2025_us_county/tl_2025_us_county.shp")
    counties = counties[["GEOID", "STATEFP", "geometry"]]
    merged_gdf = counties.merge(agg_df, on="GEOID", how="left")

    end = time.time()

    print(merged_gdf.head())
    print(f"Time taken: {end - start:.2f} seconds")


def polars_play():
    start = time.time()

    # polars implementation

    # 1. Read files into RAM

    con = duckdb.connect()

    claims_df = con.execute("""
        SELECT countyCode, netBuildingPaymentAmount
        FROM read_parquet('data/FimaNfipClaimsV2.parquet')
    """).pl()

    policies_df = con.execute("""
        SELECT countyCode, policyCount, totalBuildingInsuranceCoverage
        FROM read_parquet('data/FimaNfipPoliciesV2.parquet')
    """).pl()

    con.close()

    # 2. Aggregate millions of rows (multi-threaded via Polars)
    claims_agg = (
        claims_df.drop_nulls(subset=["countyCode"])
        .group_by("countyCode")
        .agg(pl.col("netBuildingPaymentAmount").sum().alias("avg_claim_amt"))
    )

    policies_agg = (
        policies_df.drop_nulls(subset=["countyCode"])
        .group_by("countyCode")
        .agg(
            pl.col("policyCount").sum().alias("total_policies"),
            pl.col("totalBuildingInsuranceCoverage").sum().alias("avg_coverage"),
        )
    )

    # 3. Clean and join
    agg_df = claims_agg.join(policies_agg, on="countyCode", how="full", coalesce=True)
    agg_df = agg_df.rename({"countyCode": "GEOID"})
    agg_df = agg_df.with_columns(pl.col("GEOID").cast(pl.String).str.zfill(5))

    # 4. Spatial Merge (GeoPandas requires pandas)
    counties = gpd.read_file("data/tl_2025_us_county/tl_2025_us_county.shp")
    counties = counties[["GEOID", "STATEFP", "geometry"]]
    merged_gdf = counties.merge(agg_df.to_pandas(), on="GEOID", how="left")

    end = time.time()

    print(merged_gdf.head())
    print(f"Time taken: {end - start:.2f} seconds")


def duckdb_play():
    start = time.time()

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")

    # Unified SQL query for aggregation and spatial join
    query = """
    WITH aggregated_claims AS (
        SELECT
            lpad(cast(countyCode AS VARCHAR), 5, '0') AS GEOID,
            sum(netBuildingPaymentAmount)             AS avg_claim_amt
        FROM read_parquet('data/FimaNfipClaimsV2.parquet')
        WHERE countyCode IS NOT NULL
        GROUP BY 1
    ),
    aggregated_policies AS (
        SELECT
            lpad(cast(countyCode AS VARCHAR), 5, '0') AS GEOID,
            sum(policyCount)                          AS total_policies,
            sum(totalBuildingInsuranceCoverage)       AS avg_coverage
        FROM read_parquet('data/FimaNfipPoliciesV2.parquet')
        WHERE countyCode IS NOT NULL
        GROUP BY 1
    ),
    counties_shapefile AS (
        SELECT
            GEOID,
            STATEFP,
            ST_AsWKB(geom) AS geometry
        FROM ST_Read('data/tl_2025_us_county/tl_2025_us_county.shp')
    )
    SELECT
        s.GEOID, s.STATEFP, p.total_policies,
        p.avg_coverage, c.avg_claim_amt, s.geometry
    FROM counties_shapefile s
    LEFT JOIN aggregated_policies p ON s.GEOID = p.GEOID
    LEFT JOIN aggregated_claims c   ON s.GEOID = c.GEOID
    """

    df = con.execute(query).df()
    con.close()

    end = time.time()
    print(f"Time taken: {end - start:.2f} seconds")

    # Cast bytearray to strict bytes for Shapely compatibility
    df["geometry"] = df["geometry"].apply(bytes)

    # Final Handoff to GeoPandas
    df["geometry"] = gpd.GeoSeries.from_wkb(df["geometry"])
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4269")

    # result_lf = con.execute(query).pl().lazy()
    # con.close()

    # end = time.time()
    # print(f"Time taken: {end - start:.2f} seconds")

    # # Cast bytearray to strict bytes for Shapely compatibility, then collect
    # result_df = result_lf.with_columns(
    #     pl.col("geometry").map_elements(bytes, return_dtype=pl.Binary)
    # ).collect()

    # # Final Handoff to GeoPandas
    # result_pd = result_df.to_pandas()
    # result_pd["geometry"] = gpd.GeoSeries.from_wkb(result_pd["geometry"])
    # return gpd.GeoDataFrame(result_pd, geometry="geometry", crs="EPSG:4269")


def main():
    # pandas_play() # Time taken: 87.18 seconds
    # polars_play()  # Time taken: 27.19 seconds
    duckdb_play()  # Time taken: 2.09 seconds


if __name__ == "__main__":
    main()
