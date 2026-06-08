/* 	S3.01 Cristina Fornaguera Torner  */
/* Nivel 1 Exercici 1 */

/*
He credo el proyecto ‘sprint3-analytics-cristina-f-t’
Usando el código siguiente en la consola:
gcloud projects create sprint3-analytics-cristina-f-t --name="sprint3-analytics-cristina-f-t"

      -	He vinculado la sesión al proyecto a través de la consola:
gcloud config set project sprint3-analytics-cristina-f-t
*/

-- Uso el código siguiente para crear el dataset Silver:
CREATE SCHEMA `sprint3_silver`
OPTIONS(
  location = 'eu'
);

/*
Creo el dataset Gold a través de la shell con el siguiente código:
bq mk --location=EU sprint3_gold 

*/

/* Nivell 1 Exercici 2:  */

-- Código para crear la tabla ‘transactions_raw’:
CREATE OR REPLACE EXTERNAL TABLE `sprint3_bronze.transactions_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/ERP/transactions.csv'],
  field_delimiter = ';'
);

/*Como no sabemos la estructura de la segunda tabla ‘companies_raw’, 
la cargaremos de forma temporal en una tabla ‘test’ para ver su estructura y contenido, 
y después crearemos la tabla ‘companies_raw’ ya con su propio y adecuado formato: */

CREATE OR REPLACE EXTERNAL TABLE `sprint3_bronze.test_companies_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/ERP/companies.csv']
);

--  Hacemos un select para ver los 5 primeros registros:
SELECT * FROM `sprint3_bronze.test_companies_raw` LIMIT 5;

/* Con estos datos tenemos suficiente para saber los tipos de datos y los nombres de columnas, 
creamos la tabla ‘companies_raw’: */

CREATE OR REPLACE EXTERNAL TABLE `sprint3_bronze.companies_raw`
(
  company_id STRING,
  company_name STRING,
  phone STRING,
  email STRING,
  country STRING,
  website STRING
)
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/ERP/companies.csv'],
  skip_leading_rows = 1
);

-- Creamos el resto de tablas importando los .csv:
CREATE OR REPLACE EXTERNAL TABLE `sprint3_bronze.american_users_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/CRM/american_users.csv']
);

CREATE OR REPLACE EXTERNAL TABLE `sprint3_bronze.european_users_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/CRM/european_users.csv']
);

CREATE OR REPLACE EXTERNAL TABLE `sprint3_bronze.credit_cards_raw`
OPTIONS (
  format = 'CSV',
  uris = ['gs://bootcamp-data-analytics-public/CRM/credit_cards.csv']
);


/* Nivell 1 Exercici 4:  */
-- B
SELECT id
FROM `sprint3_bronze.transactions_raw`;

SELECT id
FROM `sprint3_bronze.transactions_raw_native`;

-- C

SELECT *
FROM `sprint3_bronze.transactions_raw`
LIMIT 10;

SELECT *
FROM `sprint3_bronze.transactions_raw_native`
LIMIT 10;

SELECT *
FROM `sprint3_bronze.transactions_raw_native`;

/* Nivell 1 Exercici 5:  */

-- Consulta esquema tabla ‘transactions_raw_native’

SELECT
  column_name,
  data_type
FROM
  `sprint3_bronze.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE
  table_name = 'transactions_raw_native';

-- Consulta :

SELECT 
  DATE(timestamp) AS data_dia,
  ROUND(SUM(amount),2) AS ingressos_totals
FROM 
  `sprint3_bronze.transactions_raw_native`
WHERE 
  EXTRACT(YEAR FROM timestamp) = 2021
GROUP BY 
  data_dia
ORDER BY 
  ingressos_totals DESC
LIMIT 5;

/* Nivell 1 Exercici 6:  */

-- Consulta esquema tabla ‘companies_raw’:

SELECT
  column_name,
  data_type
FROM
  `sprint3_bronze.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE
  table_name = 'companies_raw';

--  Consulta:
SELECT
  c.company_name AS nom_empresa,
  c.country AS pais,
  DATE(t.timestamp) AS data_transaccio,
  ROUND(t.amount,2) AS import
FROM
  `sprint3_bronze.transactions_raw_native` AS t
JOIN
  `sprint3_bronze.companies_raw` AS c
  ON t.business_id = c.company_id
WHERE
  t.amount BETWEEN 100 AND 200
  AND (
    DATE(t.timestamp) = '2015-04-29'
    OR DATE(t.timestamp) = '2018-07-20'
    OR DATE(t.timestamp) = '2024-03-13'
  )
ORDER BY
  data_transaccio ASC;


/* Nivell 2 Exercici 1:  */

-- Consulta esquema tabla ‘products_raw’ 

SELECT 
  column_name, 
  data_type 
FROM 
  `sprint3_bronze.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE 
  table_name = 'products_raw';

--  Consulta:

CREATE OR REPLACE TABLE `sprint3_silver.products_clean` AS
SELECT
  id AS product_id,
  product_name AS name,
  CAST(REPLACE(warehouse_id, 'WH-', '') AS INT64) AS warehouse_id,
  price,
  weight,
  colour,
  category,
  brand,
  cost,
  launch_date
FROM
  `sprint3_bronze.products_raw`;

/* Nivell 2 Exercici 2:  */

-- Consulta creación tabla ‘sprint3_silver.transactions_clean’:

CREATE OR REPLACE TABLE `sprint3_silver.transactions_clean` AS
SELECT
  id AS transaction_id,
  card_id,
  business_id,
  user_id,
  timestamp,
  IFNULL(SAFE_CAST(amount AS FLOAT64), 0) AS amount,
  declined,
  lat,
  longitude,
  ARRAY(
    SELECT CAST(TRIM(id_prod) AS INT64)
    FROM UNNEST(SPLIT(product_ids, ',')) AS id_prod
  ) AS product_ids
FROM
  `sprint3_bronze.transactions_raw_native`;

/* Nivell 2 Exercici 3:  */

--  Consulta esquema tablas ‘american_users_raw' y 'european_users_raw' :

SELECT
  table_name,
  column_name,
  data_type
FROM
  `sprint3_bronze.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE
  table_name IN ('american_users_raw', 'european_users_raw')
ORDER BY
  column_name, table_name;

--Creación tabla ‘sprint3_silver.users_combined’:

CREATE OR REPLACE TABLE `sprint3_silver.users_combined` AS
SELECT
  id AS user_id,
  name,
  surname,
  email,
  phone,
  birth_date,
  address,
  city,
  postal_code,
  country,
  'USA' AS origin
FROM
  `sprint3_bronze.american_users_raw`

UNION ALL

SELECT
  id AS user_id,
  name,
  surname,
  email,
  phone,
  birth_date,
  address,
  city,
  postal_code,
  country,
  'Europe' AS origin
FROM
  `sprint3_bronze.european_users_raw`;

/* Nivell 2 Exercici 4:  */

/* 1 */

--  Creamos la tabla ‘companies_clean’ a Silver:

CREATE OR REPLACE TABLE `sprint3_silver.companies_clean` AS
SELECT
  company_id,
  company_name,
  phone,
  email,
  country,
  website
FROM
  `sprint3_bronze.companies_raw`;

 /* 2 */

-- Averiguamos el esquema de la tabla ‘credit_cards_raw’:

SELECT
  column_name,
  data_type
FROM
  `sprint3_bronze.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE
  table_name = 'credit_cards_raw';


-- Creación tabla ‘sprint3_silver.credit_cards_clean’: 

CREATE OR REPLACE TABLE `sprint3_silver.credit_cards_clean` AS
SELECT
  id AS card_id,
  user_id,
  iban,
  pan,
  pin,
  cvv,
  track1,
  track2,
  expiring_date
FROM
  `sprint3_bronze.credit_cards_raw`;

/* Nivell 3 Exercici 1:  */

-- Creamos la Vista siguiendo las instrucciones de transformación:

CREATE OR REPLACE VIEW `sprint3_gold.v_marketing_kpis` AS
SELECT
  c.company_name,
  c.phone,
  c.country,
  ROUND(AVG(t.amount), 2) AS avg_purchase,
  IF(AVG(t.amount) > 260, 'Premium', 'Standard') AS client_tier
FROM
  `sprint3_silver.companies_clean` AS c
JOIN
  `sprint3_silver.transactions_clean` AS t
  ON c.company_id = t.business_id
GROUP BY
  c.company_name,
  c.phone,
  c.country;


-- Creamos la consulta a la vista siguiendo las instrucciones:
SELECT * FROM `sprint3_gold.v_marketing_kpis`
ORDER BY
  client_tier ASC,
  avg_purchase DESC;


/* Nivell 3 Exercici 2:  */

-- Creamos la consulta para la creación de la nueva tabla ‘product_sales_ranking’ en Gold, siguiendo las instrucciones:

CREATE OR REPLACE TABLE `sprint3_gold.product_sales_ranking` AS
SELECT
  p.product_id,
  p.name,
  p.price,
  p.colour,
  COUNT(t_flat.single_prod_id) AS total_sold
FROM
  `sprint3_silver.products_clean` AS p
LEFT JOIN (
  SELECT
    id_p AS single_prod_id
  FROM
    `sprint3_silver.transactions_clean`,
    UNNEST(product_ids) AS id_p
) AS t_flat
  ON p.product_id = t_flat.single_prod_id
GROUP BY
  p.product_id,
  p.name,
  p.price,
  p.colour
ORDER BY
  total_sold DESC;
