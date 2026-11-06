# Mapping DuckDB logic to SQL Server (T-SQL) — interview cheat sheet

The pipeline uses **DuckDB** because it is free and fast for a portfolio. Employers often ask for **SQL Server** / **SSMS**. The **ideas** are the same: CTEs, window functions, Parquet/CSV staging.

## CPIH YoY % (conceptual T-SQL)

Assume a staging table `stg.CpihMonthly(obs_date date, index_level decimal(18,4))` loaded from `cpih_yoy.csv` or raw monthly rows.

```sql
WITH ordered AS (
  SELECT
    obs_date,
    index_level,
    AVG(index_level) OVER (
      ORDER BY obs_date
      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS cpih_3m_avg
  FROM stg.CpihMonthly
  WHERE obs_date IS NOT NULL AND index_level IS NOT NULL
),
yoy AS (
  SELECT
    obs_date,
    index_level,
    cpih_3m_avg,
    LAG(index_level, 12) OVER (ORDER BY obs_date) AS index_12m_ago,
    CASE
      WHEN LAG(index_level, 12) OVER (ORDER BY obs_date) IS NULL
        OR LAG(index_level, 12) OVER (ORDER BY obs_date) = 0
      THEN NULL
      ELSE 100.0 * (index_level - LAG(index_level, 12) OVER (ORDER BY obs_date))
        / NULLIF(LAG(index_level, 12) OVER (ORDER BY obs_date), 0)
    END AS yoy_pct
  FROM ordered
)
SELECT * FROM yoy ORDER BY obs_date;
```

Use `NULLIF` in T-SQL to avoid divide-by-zero warnings.

## Monthly PSNB aggregate

```sql
SELECT
  obs_date,
  SUM(net_borrowing_gbp_m) AS total_net_borrowing_gbp_m,
  COUNT(*) AS row_count
FROM stg.PsnbMonthly
WHERE obs_date IS NOT NULL AND net_borrowing_gbp_m IS NOT NULL
GROUP BY obs_date
ORDER BY obs_date;
```

## Loading CSV in SSMS (free Express / Developer)

1. Right-click database → **Tasks** → **Import Flat File** (or `BULK INSERT` from a filepath you control).
2. Map columns to match export CSV headers from `data/exports/*.csv`.

This file is documentation only; it is not executed in CI.
