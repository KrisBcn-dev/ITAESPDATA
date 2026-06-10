-- Sprint 4 Cristina Fornaguera
-- NIVELL 1: ENTORN I INGESTA HÍBRIDA (CODE-FIRST)
-- Exercici 1: Consulta sobre Taula no Optimitzada (Diagnòstic)

SELECT 
  t.transaction_id,
  t.timestamp,
  t.amount,
  t.declined,
  c.company_name,
  c.country
FROM 
  `sprint3_silver.transactions_clean` AS t
JOIN 
  `sprint3_silver.companies_clean` AS c 
  ON t.business_id = c.company_id
WHERE 
  DATE(t.timestamp) = '2022-03-12'
  AND c.country = 'Germany';

-- Exercici 2: Re-arquitectura i Optimització de l'Emmagatzematge (Partition & Cluster)
-- Pas 1: Generació de Dades Recents (Mocking Data)

CREATE OR REPLACE TABLE `sprint3_silver.transactions_recent` AS
SELECT
  * EXCEPT(timestamp),
  TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL CAST(RAND() * 50 AS INT64) DAY) AS timestamp
FROM
  `sprint3_silver.transactions_clean`;


-- Pas 2: Creació de la Taula Optimitzada (Partitioning & Clustering) 

CREATE OR REPLACE TABLE `sprint3_gold.fact_transactions_optimized`
PARTITION BY DATE(timestamp)
CLUSTER BY business_id AS
SELECT
  transaction_id,
  card_id,
  business_id,
  user_id,
  amount,
  declined,
  lat,
  longitude,
  product_ids,
  timestamp
FROM
  `sprint3_silver.transactions_recent`;

-- Exercici 3: La Prova del Cotó (Benchmark)
-- Pas 1:  Taula no optimitzada

SELECT
  *
FROM
  `sprint3_silver.transactions_recent`
WHERE
  DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

-- Pas 2: Taula optimitzada

SELECT
  *
FROM
  `sprint3_gold.fact_transactions_optimized`
WHERE
  DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);

-- Exercici 4: Smart Caching (Vistes Materialitzades)
-- Pas 1: creación de la Vista Materializada 

CREATE OR REPLACE MATERIALIZED VIEW `sprint3_gold.mv_daily_sales` AS
SELECT 
  DATE(timestamp) AS sales_date,
  SUM(amount) AS total_sales
FROM 
  `sprint3_gold.fact_transactions_optimized`
GROUP BY 
  sales_date;
  
-- Pas 2: consulta a la nueva vista

SELECT 
  sales_date, 
  ROUND(total_sales,2) AS total_sales
FROM 
  `sprint3_gold.mv_daily_sales`;


-- NIVELL 2: SQL Analític Avançat
-- Exercici 1: Perfilat de Clients VIP (Mètriques Agregades amb CTEs)

WITH VIP_Stats AS (
  SELECT 
    user_id,
    COUNT(transaction_id) AS num_compres,
    ROUND(AVG(amount), 2) AS tiquet_mig,
    ROUND(MAX(amount), 2) AS max_compra,
    ROUND(SUM(amount), 2) AS total_gastat
  FROM 
    `sprint3_gold.fact_transactions_optimized`
  WHERE 
    declined = 0
  GROUP BY 
    user_id
  HAVING 
    SUM(amount) > 500
)
SELECT 
  v.user_id,
  CONCAT(u.name, ' ', u.surname) AS nom_complet,
  u.email,
  v.num_compres,
  v.tiquet_mig,
  v.max_compra,
  v.total_gastat
FROM 
  VIP_Stats AS v
JOIN 
  `sprint3_silver.users_combined` AS u 
  USING (user_id)
ORDER BY 
  v.total_gastat DESC;


-- Exercici 2: Anàlisi de Tendències (Window Functions sobre Vistes)

SELECT
  sales_date AS Data,
  ROUND(total_sales, 2) AS Vendes_Avui,
  ROUND(LAG(total_sales) OVER (ORDER BY sales_date ASC), 2) AS Vendes_Ahir,
  ROUND(
    SAFE_DIVIDE(
      total_sales - LAG(total_sales) OVER (ORDER BY sales_date ASC),
      LAG(total_sales) OVER (ORDER BY sales_date ASC)
    ) * 100,
    2
  ) AS Diff_Percentual
FROM
  `sprint3_gold.mv_daily_sales`
ORDER BY
  Data ASC;

-- Exercici 3: Totals Acumulats (Running Totals sobre Vistes)

SELECT 
  sales_date AS Data,
  ROUND(total_sales, 2) AS Vendes_del_Dia,
  ROUND(
    SUM(total_sales) OVER (
      PARTITION BY EXTRACT(YEAR FROM sales_date)
      ORDER BY sales_date ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 
    2
  ) AS Vendes_Acumulades_YTD
FROM 
  `sprint3_gold.mv_daily_sales`
ORDER BY 
  Data ASC;

  -- Exercici 4: Fidelització i Valor del Client (Filtratge Avançat)

  WITH Third_Purchase_Analytics AS (
  SELECT
    user_id,
    transaction_id,
    DATE(timestamp) AS data_tercera_compra,
    amount AS import_tercera_compra,
    AVG(amount) OVER(
      PARTITION BY user_id
      ORDER BY timestamp ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS mitjana_tres_primeres,
    ROW_NUMBER() OVER(
      PARTITION BY user_id
      ORDER BY timestamp ASC
    ) AS ordre_compra
  FROM
    `sprint3_gold.fact_transactions_optimized`
  WHERE
    declined = 0
  QUALIFY
    ordre_compra = 3
)

SELECT
  t.user_id,
  CONCAT(u.name, ' ', u.surname) AS nom_complet,
  u.email,
  t.data_tercera_compra,
  ROUND(t.import_tercera_compra, 2) AS import_tercera_compra,
  ROUND(t.mitjana_tres_primeres, 2) AS mitjana_3_primeres
FROM
  Third_Purchase_Analytics AS t
JOIN
  `sprint3_silver.users_combined` AS u
  USING (user_id)
ORDER BY
  mitjana_3_primeres DESC;

-- NIVELL 3: Analytics Engineering (Arrays & Automatització)
-- Exercici 1: Desaniuament i Aplanament de Dades (Unnesting)

CREATE OR REPLACE TABLE `sprint3_gold.dim_transactions_flat` AS
SELECT
  t.transaction_id,
  t.timestamp,
  ROUND(t.amount, 2) AS total_ticket,
  p.product_id AS product_sku,
  p.name AS product_name,
  ROUND(p.price, 2) AS product_price
FROM
  `sprint3_gold.fact_transactions_optimized` AS t
CROSS JOIN
  UNNEST(t.product_ids) AS single_product_id
INNER JOIN
  `sprint3_silver.products_clean` AS p
  ON SAFE_CAST(single_product_id AS INT64) = p.product_id
WHERE
  t.declined = 0;

-- Exercici 2: El Rànquing de Vendes (Agregació Simple)

SELECT
  product_name,
  COUNT(transaction_id) AS unitats_venudes
FROM
  `sprint3_gold.dim_transactions_flat`
GROUP BY
  product_name
ORDER BY
  unitats_venudes DESC
LIMIT 5;

-- Exercici 3.1: UDF

CREATE OR REPLACE FUNCTION `sprint3_gold.calculate_tax`(amount FLOAT64)
RETURNS FLOAT64 AS (
  amount * 1.21
);

-- Exercici 3.2: Aplicar UDF a la creación de la tabla dim_transactions_flat

CREATE OR REPLACE TABLE `sprint3_gold.dim_transactions_flat` AS
SELECT
  t.transaction_id,
  t.timestamp,
  ROUND(t.amount, 2) AS total_ticket,
  p.product_id AS product_sku,
  p.name AS product_name,
  ROUND(p.price, 2) AS product_price,
  ROUND(`sprint3_gold.calculate_tax`(p.price), 2) AS product_price_tax_inc
FROM
  `sprint3_gold.fact_transactions_optimized` AS t
CROSS JOIN
  UNNEST(t.product_ids) AS single_product_id
JOIN
  `sprint3_silver.products_clean` AS p
  ON SAFE_CAST(single_product_id AS INT64) = p.product_id
WHERE
  t.declined = 0;
