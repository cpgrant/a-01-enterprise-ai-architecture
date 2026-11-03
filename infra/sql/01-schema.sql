
-- AI-A01 Enterprise Operations Database
-- Synthetic data only

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    priority VARCHAR(20) NOT NULL
        CHECK (priority IN ('standard', 'high', 'critical'))
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(120) NOT NULL,
    reliability_score NUMERIC(5,2)
        CHECK (reliability_score BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    order_value NUMERIC(12,2) NOT NULL,
    promised_date DATE NOT NULL,
    expected_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL
        CHECK (status IN ('pending', 'processing', 'shipped', 'delivered')),
    CHECK (order_value >= 0)
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    document_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768)
);
