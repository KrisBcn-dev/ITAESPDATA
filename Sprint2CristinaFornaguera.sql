/*
Nivell 1
Exercici 1
A partir dels documents adjunts (estructura_dades i dades_introduir), importa les dues taules. Mostra les característiques principals de l'esquema creat i explica les diferents taules i variables que existeixen. Assegura't d'incloure un diagrama que il·lustri la relació entre les diferents taules i variables.
*/
-- Primer executem el fitxer que crearà la base de dades i les taules
-- N1-Ex.1__ estructura dades.sql
USE transactions;
-- A continuació, executem el fitxer que introduirà les dades a les taules
-- N1-Ex.1__dades_introduir.sql
/*
Exercici 2
Utilitzant JOIN realitzaràs les següents consultes:
*/
-- Llistat dels països que estan generant vendes.
SELECT DISTINCT c.country FROM company c
INNER JOIN transaction t ON t.company_id = c.id
WHERE t.declined=0;

-- Des de quants països es generen les vendes.
SELECT COUNT(DISTINCT c.country) FROM company c
INNER JOIN transaction t ON t.company_id = c.id
WHERE t.declined=0;

-- Identifica la companyia amb la mitjana més gran de vendes.
SELECT  c.company_name, AVG(t.amount) as mitjana
FROM company c
INNER JOIN transaction t ON t.company_id = c.id
WHERE t.declined=0
GROUP BY c.company_name
ORDER BY mitjana DESC
LIMIT 1;

/*
Exercici 3
Utilitzant només subconsultes (sense utilitzar JOIN):
*/
-- Mostra totes les transaccions realitzades per empreses d'Alemanya.
SELECT t.* FROM transaction t
WHERE EXISTS (
    SELECT 1 
    FROM company c
    WHERE c.id = t.company_id 
      AND c.country = 'Germany'
);

-- Llista les empreses que han realitzat transaccions per un amount superior a la mitjana de totes les transaccions.
SELECT c.* 
FROM company c
WHERE EXISTS (
    SELECT 1 
    FROM transaction t
    WHERE t.company_id = c.id 
      AND t.amount > (SELECT AVG(tr.amount) FROM transaction tr)
);

-- Eliminaran del sistema les empreses que no tenen transaccions registrades, entrega el llistat d'aquestes empreses.
SELECT c.* FROM company c
WHERE NOT EXISTS (
    SELECT 1 
    FROM transaction t
    WHERE t.company_id = c.id
);

/*
Exercici 4
La teva tasca és dissenyar i crear una taula anomenada "credit_card" que emmagatzemi detalls crucials sobre les targetes de crèdit. La nova taula ha de ser capaç d'identificar de manera única cada targeta i establir una relació adequada amb les altres dues taules ("transaction" i "company"). Després de crear la taula serà necessari que ingressis la informació del document denominat "dades_introduir_credit". Recorda mostrar el diagrama i realitzar una breu descripció d'aquest.
*/
CREATE TABLE credit_card (
	id VARCHAR(15) PRIMARY KEY,
    iban VARCHAR(50),
    pan VARCHAR(50),
    pin VARCHAR(4),
    cvv VARCHAR(3),
    expiring_date VARCHAR(8)
);

ALTER TABLE transaction
ADD CONSTRAINT fk_credit_card
FOREIGN KEY (credit_card_id) 
REFERENCES credit_card(id);	

-- Carreguem les dades a la taula credit_card executant el fitxer següent:
-- N1-Ex.4__ datos_introducir_credit.sql

/*
Exercici 5
El departament de Recursos Humans ha identificat un error en el número de compte associat a la targeta de crèdit amb ID CcU-2938. La informació que ha de mostrar-se per a aquest registre és: TR323456312213576817699999. Recorda mostrar que el canvi es va realitzar.
*/
-- trobem el nº de targeta afectat
SELECT iban FROM credit_card 
WHERE id = 'CcU-2938';

-- Actualitzem el nº de targeta afectat
UPDATE credit_card 
SET iban = 'TR323456312213576817699999'
WHERE id = 'CcU-2938';

-- Comprovem el nº de targeta afectat
SELECT iban FROM credit_card 
WHERE id = 'CcU-2938';

/*
Exercici 6
En la taula "transaction" ingressa una nova transacció amb la següent informació:

Id - 108B1D1D-5B23-A76C-55EF-C568E49A99DD 
credit_card_id - CcU-9999 
company_id  - b-9999 
user_id - 9999 
lat - 829.999 
longitude - -117.999 
amount - 111.11 
declined - 0 
*/
USE transactions;
INSERT INTO transaction (id, credit_card_id, company_id, user_id, lat, longitude, amount, declined) 
VALUES ('108B1D1D-5B23-A76C-55EF-C568E49A99DD', 'CcU-9999', 'b-9999', 9999, 829.999, -117.999, 111.11, 0);
-- Aquest Insert ha donat error perquè no existeix la companyia b-9999, ho comprovem:
SELECT c.id FROM company c
WHERE UPPER(c.id) = 'B-9999';

/*   
Exercici 7
Des de recursos humans et sol·liciten eliminar la columna "pan" de la taula credit_card. Recorda mostrar el canvi realitzat.
*/
-- Comprovem que la columna a eliminar existeix:
DESCRIBE credit_card;

-- eliminem la columna 'pan'
ALTER TABLE credit_card 
DROP COLUMN pan;

-- Comprovem que s'ha eliminat la columna 'pan'
DESCRIBE credit_card;

/*
Exercici 8
Descarrega els arxius CSV que trobaràs a l'apartat de recursos:
    american_users.csv
    european_users.csv
    companies.csv
    credit_cards.csv
    transactions.csv
Estudia'ls i dissenya una base de dades amb un esquema d'estrella que contingui, almenys 4 taules de les quals puguis realitzar les següents consultes:
La taula de products.csv l'utilitzarem més endavant.
*/
CREATE DATABASE sales;
USE sales;
-- DROP table users;
-- creació taula users
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    surname VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(50),
    birth_date VARCHAR(50),
    country VARCHAR(50),
    city VARCHAR(50),
    postal_code VARCHAR(10),
    address VARCHAR(50),
    signup_date DATE,
    user_segment VARCHAR(50),
    income_band VARCHAR(50)
);
-- Carreguem el primer csv d'usuaris a la taula users
LOAD DATA 
INFILE 'N1-Ex.8__american_users.csv' 
INTO TABLE users 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

-- Carreguem el segon csv d'usuaris a la taula users
LOAD DATA 
INFILE 'N1-Ex.8__european_users.csv' 
INTO TABLE users 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

-- DROP TABLE companies;

-- creació taula companies
CREATE TABLE companies (
    company_id VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(50),
    phone VARCHAR(50),
    email VARCHAR(50),
    country VARCHAR(50),
    website VARCHAR(100),
    merchant_category VARCHAR(50),
    merchant_price_position VARCHAR(50)
);

-- Carreguem el csv de companies a la taula companies
LOAD DATA 
INFILE 'N1-Ex.8__companies.csv' 
INTO TABLE companies 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

-- creació taula credit_cards
-- al contenir la columna user_id, la relacionarem ja em el id d'usuari de la taula 'users'
CREATE TABLE credit_cards (
    id VARCHAR(10) PRIMARY KEY,
    user_id INT,
    iban VARCHAR(50),
    pan VARCHAR(50),
    pin INT,
    cvv INT,
    track1 VARCHAR(70),
    track2 VARCHAR(70),
    expiring_date VARCHAR(50),
    card_type VARCHAR(30),
    card_renewal_flag TINYINT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Carreguem el csv de credit_cards a la taula credit_cards
LOAD DATA 
INFILE 'N1-Ex.8__credit_cards.csv' 
INTO TABLE credit_cards 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

-- DROP TABLE transactions;
-- creació taula transactions
-- **Alerta, aqui canvia el separador de , a ;
-- al contenir la columna user_id, la relacionarem ja em el id d'usuari de la taula 'users'
-- al contenir la columna card_id, la relacionarem ja em el id de targeta de la taula 'credit_cards'
-- al contenir la columna business_id, la relacionarem ja em el id de targeta de la taula 'companies'
-- tot i tenir la columna products, els camps d'aquesta columna contenen un o més ids de productes, 
-- cosa que no facilita cap relació directa amb la taula 'products' que encara no tenim.
CREATE TABLE transactions (
    id VARCHAR(50) PRIMARY KEY,
    card_id VARCHAR(10),
    business_id VARCHAR(10),
    timestamp DATETIME,
    amount FLOAT,
    declined TINYINT,
    product_ids VARCHAR(70),
    user_id INT,
    lat VARCHAR(70),
    longitude VARCHAR(70),
    discount_amount FLOAT,
    tax_amount FLOAT,
    shipping_amount FLOAT,
    channel VARCHAR(50),
    campaign_id VARCHAR(50),
    device_type VARCHAR(50),
    is_international TINYINT,
    decline_reason VARCHAR(70),
    distance_km  FLOAT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (card_id) REFERENCES credit_cards(id),
    FOREIGN KEY (business_id) REFERENCES companies(company_id)
);

-- Carreguem el csv de transactions a la taula transactions
LOAD DATA 
INFILE 'N1-Ex.8__transactions.csv' 
INTO TABLE transactions 
FIELDS TERMINATED BY ';' -- Important!
ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

/*
Exercici 9
Realitza una subconsulta que mostri tots els usuaris amb més de 80 transaccions utilitzant almenys 2 taules.
*/
USE sales;
SELECT u.name, u.surname
FROM users u
WHERE EXISTS (
    SELECT 1 
    FROM transactions t 
    WHERE t.user_id = u.id 
    GROUP BY t.user_id
    HAVING COUNT(t.id) > 80
);
/* Exercici 10
Mostra la mitjana d'amount per IBAN de les targetes de crèdit a la companyia Donec Ltd, utilitza almenys 2 taules.
*/
SELECT ROUND(AVG(t.amount),2) AS amount_average, cc.iban, c.company_name
FROM transactions t
INNER JOIN companies c ON c.company_id = t.business_id
INNER JOIN credit_cards cc ON cc.id = t.card_id
WHERE UPPER(c.company_name) = UPPER("Donec Ltd")
AND UPPER(cc.card_type) = 'CREDIT'  
GROUP BY cc.iban, c.company_name;

/* Nivell 2 Exercici 1
Identifica els cinc dies que es va generar la quantitat més gran d'ingressos a l'empresa per vendes. Mostra la data de cada transacció juntament amb el total de les vendes.
*/
SELECT DATE(t.timestamp) AS dia, ROUND(SUM(t.amount),2) AS quantitat
FROM transactions t
WHERE t.declined = 0
GROUP BY DATE(t.timestamp)
ORDER BY SUM(t.amount) DESC
LIMIT 5;

/* Exercici 2
Presenta el nom, telèfon, país, data i amount, d'aquelles empreses que van realitzar transaccions amb un valor comprès entre 350 i 400 euros i en alguna d'aquestes dates: 29 d'abril del 2015, 20 de juliol del 2018 i 13 de març del 2024. Ordena els resultats de major a menor quantitat.
*/
SELECT c.company_name, c.phone, c.country, DATE(t.timestamp) AS date, t.amount
FROM companies c
INNER JOIN transactions t ON t.business_id = c.company_id
WHERE t.amount BETWEEN 350 AND 400 
AND (DATE(t.timestamp) = '2015-04-29' 
     OR DATE(t.timestamp) = '2018-07-20' 
     OR DATE(t.timestamp) = '2024-03-13')
ORDER BY t.amount DESC;

/* Exercici 3
Necessitem optimitzar l'assignació dels recursos i dependrà de la capacitat operativa que es requereixi, per la qual cosa et demanen la informació sobre la quantitat de transaccions que realitzen les empreses, però el departament de recursos humans és exigent i vol un llistat de les empreses on especifiquis si tenen igual o més de 400 transaccions o menys.
*/
SELECT c.company_name, COUNT(t.id) AS total_transactions, IF(COUNT(t.id) >= 400, '+=', '-') AS '400TR'
FROM companies c
INNER JOIN transactions t ON t.business_id = c.company_id
GROUP BY c.company_id;

/* Exercici 4
Elimina de la taula transaction el registre amb ID 000447FE-B650-4DCF-85DE-C7ED0EE1CAAD de la base de dades.
*/
DELETE FROM transactions
WHERE id='000447FE-B650-4DCF-85DE-C7ED0EE1CAAD';

/* Exercici 5
La secció de màrqueting desitja tenir accés a informació específica per a realitzar anàlisi i estratègies efectives. S'ha sol·licitat crear una vista que proporcioni detalls clau sobre les companyies i les seves transaccions. Serà necessària que creïs una vista anomenada VistaMarketing que contingui la següent informació: Nom de la companyia. Telèfon de contacte. País de residència. Mitjana de compra realitzat per cada companyia. Presenta la vista creada, ordenant les dades de major a menor mitjana de compra.
*/
CREATE VIEW VistaMarketing AS
SELECT c.company_name AS company, c.phone AS phone, c.country AS country, AVG(t.amount) AS sales_average
FROM companies c
INNER JOIN transactions t ON t.business_id = c.company_id
GROUP BY c.company_id
ORDER BY AVG(t.amount) DESC

/* Nivell 3
Exercici 1
Crea una nova taula que reflecteixi l'estat de les targetes de crèdit basat en si les tres últimes transaccions han estat declinades aleshores és inactiu, si almenys una no és rebutjada aleshores és actiu. Partint d’aquesta taula respon:

👉 Quantes targetes estan actives? 5000
*/
CREATE TABLE credit_card_status AS
SELECT 
    card_id,
    CASE 
        WHEN SUM(declined) < 3 THEN 'Active'
        ELSE 'Inactive'
    END AS status
FROM (
    SELECT 
        card_id,
        declined,
        ROW_NUMBER() OVER (PARTITION BY card_id ORDER BY timestamp DESC) AS position
    FROM transactions
) AS transaccions_ordenades
WHERE position <= 3
GROUP BY card_id;

SELECT COUNT(card_id) as targetes_actives
FROM credit_card_status
WHERE status = 'Active';

/* Exercici 2
Crea una taula amb la qual puguem unir les dades de l'arxiu de products.csv amb la base de dades creada (ja que fins ara no podíem fer-ho), tenint en compte que des de transaction tens product_ids. Genera la següent consulta:
👉 Necessitem conèixer el nombre de vegades que s'ha venut cada producte.
*/
-- Primer crearem la taula 'products' i hi carregarem les dades del fitxer .csv
-- Creació taula products
CREATE TABLE products (
    id VARCHAR(10) PRIMARY KEY,
    product_name VARCHAR(50),
    price VARCHAR(50),
    colour VARCHAR(10),
    weight FLOAT,
    warehouse_id VARCHAR(10),
    category VARCHAR(50),
    brand VARCHAR(50),
    cost VARCHAR(50),
    launch_date DATE
);

-- Carreguem el csv de products a la taula products
LOAD DATA 
INFILE 'N1-Ex.8__products.csv' 
INTO TABLE products 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 ROWS;

-- Creem la taula 'transaction_products' que relacionarà les transaccions amb els productes venuts en cada transacció, tenint en compte que la columna 'product_ids' de la taula 'transactions' pot contenir un o més ids de productes separats per comes.
CREATE TABLE transaction_products AS
SELECT t.id AS transaction_id, p.id AS product_id
FROM products p
INNER JOIN transactions t 
ON FIND_IN_SET(p.id, REPLACE(t.product_ids, ' ', ''))
GROUP BY t.id, p.id
HAVING product_id IS NOT NULL AND product_id != '';

-- consulta : nombre de vegades que s'ha venut cada producte.
SELECT 
    p.id AS product_id,
    p.product_name,
    p.category,
    COUNT(tp.transaction_id) AS times_sold
FROM products p
LEFT JOIN transaction_products tp ON p.id = tp.product_id
GROUP BY p.id, p.product_name, p.category
ORDER BY times_sold DESC;
