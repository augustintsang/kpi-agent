-- Create the ecommerce_transactions table with default values
CREATE TABLE ecommerce_transactions (
    transaction_id INTEGER PRIMARY KEY,
    user_name VARCHAR(100) DEFAULT 'Unknown',
    age INTEGER DEFAULT 0,
    country VARCHAR(50) DEFAULT 'Unknown',
    product_category VARCHAR(50) DEFAULT 'Unknown',
    purchase_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_method VARCHAR(50) DEFAULT 'Unknown',
    transaction_date DATE DEFAULT CURRENT_DATE
);

-- Create a temporary table for raw data import
CREATE TEMP TABLE temp_transactions (
    transaction_id INTEGER,
    user_name VARCHAR(100),
    age INTEGER,
    country VARCHAR(50),
    product_category VARCHAR(50),
    purchase_amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    transaction_date DATE
);

-- Import data into temporary table
\copy temp_transactions(transaction_id, user_name, age, country, product_category, purchase_amount, payment_method, transaction_date) FROM 'ecommerce_transactions.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', NULL '', QUOTE '"', ESCAPE '"');

-- Insert data from temporary table to main table with NULL handling
INSERT INTO ecommerce_transactions (
    transaction_id, user_name, age, country, product_category, 
    purchase_amount, payment_method, transaction_date
)
SELECT 
    transaction_id,
    COALESCE(user_name, 'Unknown'),
    COALESCE(age, 0),
    COALESCE(country, 'Unknown'),
    COALESCE(product_category, 'Unknown'),
    COALESCE(purchase_amount, 0.00),
    COALESCE(payment_method, 'Unknown'),
    COALESCE(transaction_date, CURRENT_DATE)
FROM temp_transactions;

-- Drop temporary table
DROP TABLE temp_transactions; 