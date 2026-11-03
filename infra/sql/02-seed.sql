
-- AI-A01 Synthetic Enterprise Data
-- Fictional customers, suppliers and orders
-- Fixed dates make tests reproducible.

BEGIN;

INSERT INTO customers (customer_id, customer_name, priority) VALUES
(1, 'Nordic Manufacturing', 'critical'),
(2, 'Baltic Logistics', 'high'),
(3, 'Central Retail Group', 'standard'),
(4, 'Atlantic Industries', 'high'),
(5, 'Scandinavian Healthcare', 'critical')
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO suppliers (supplier_id, supplier_name, reliability_score) VALUES
(1, 'Alpha Components', 96.50),
(2, 'Beta Industrial Supply', 72.00),
(3, 'Gamma Distribution', 88.00),
(4, 'Delta Manufacturing', 65.50)
ON CONFLICT (supplier_id) DO NOTHING;

INSERT INTO orders
(order_id, customer_id, supplier_id, order_value,
 promised_date, expected_date, status)
VALUES
(1001, 1, 2, 125000, '2026-11-05', '2026-11-10', 'processing'),
(1002, 2, 1, 48000, '2026-11-08', '2026-11-08', 'processing'),
(1003, 3, 3, 15000, '2026-11-06', '2026-11-09', 'pending'),
(1004, 4, 4, 89000, '2026-11-04', '2026-11-12', 'processing'),
(1005, 5, 1, 210000, '2026-11-07', '2026-11-07', 'shipped'),
(1006, 1, 4, 75000, '2026-11-09', '2026-11-15', 'pending')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO knowledge_documents (document_id, title, content)
VALUES
(1, 'Supplier Delay Policy',
 'Orders expected more than two days after the promised date must be escalated. Critical customers require immediate account-manager notification.'),
(2, 'Customer Priority Policy',
 'Critical customers receive first priority for recovery planning. High-priority customers receive proactive updates for material delays.'),
(3, 'Supply Chain Recovery Guidelines',
 'Recovery options include expedited shipping, alternative suppliers, partial deliveries and revised production schedules.')
ON CONFLICT (document_id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('customers','customer_id'),
              (SELECT MAX(customer_id) FROM customers));
SELECT setval(pg_get_serial_sequence('suppliers','supplier_id'),
              (SELECT MAX(supplier_id) FROM suppliers));
SELECT setval(pg_get_serial_sequence('orders','order_id'),
              (SELECT MAX(order_id) FROM orders));
SELECT setval(pg_get_serial_sequence('knowledge_documents','document_id'),
              (SELECT MAX(document_id) FROM knowledge_documents));

COMMIT;
