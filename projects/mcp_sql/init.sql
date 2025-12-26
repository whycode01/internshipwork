-- Drop existing tables if they exist (from previous setup)
DROP TABLE IF EXISTS deliverables;
DROP TABLE IF EXISTS work_orders;
DROP TABLE IF EXISTS sales_orders;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS addresses;
DROP TABLE IF EXISTS customers;

-- Use the company_db database
USE company_db;

-- Table 1: Customers
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Addresses (bill_to or ship_to)
CREATE TABLE IF NOT EXISTS addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    address_type ENUM('bill_to', 'ship_to') NOT NULL,
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    pincode VARCHAR(10),
    country VARCHAR(50) DEFAULT 'India',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Table 3: Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    creation_date DATE NOT NULL,
    customer_id INT NOT NULL,
    total_amount DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'INR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Table 4: Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    po_id INT NOT NULL,
    contact_person VARCHAR(100),
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    invoice_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE
);

-- Table 5: Sales Orders
CREATE TABLE IF NOT EXISTS sales_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    so_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    contracting_parties TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Table 6: Work Orders
CREATE TABLE IF NOT EXISTS work_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    so_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    authorized_signatory VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (so_id) REFERENCES sales_orders(id) ON DELETE CASCADE
);

-- Table 7: Deliverables
CREATE TABLE IF NOT EXISTS deliverables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    so_id INT NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (so_id) REFERENCES sales_orders(id) ON DELETE CASCADE
);

-- Insert Sample Data: Customers
INSERT INTO customers (customer_name, contact_person) VALUES
('Tech Innovations Pvt Ltd', 'Amit Kumar'),
('Global Solutions Inc', 'Priya Patel'),
('Digital Corp', 'Rahul Sharma'),
('Business Analytics Ltd', 'Sneha Reddy'),
('Enterprise Systems', 'Vijay Singh');

-- Insert Sample Data: Addresses (Bill-to and Ship-to)
INSERT INTO addresses (customer_id, address_type, address_line1, city, state, pincode) VALUES
-- Customer 1: Tech Innovations
(1, 'bill_to', '123 Tech Park Road', 'Bangalore', 'Karnataka', '560001'),
(1, 'ship_to', '456 Industrial Area', 'Bangalore', 'Karnataka', '560002'),
-- Customer 2: Global Solutions
(2, 'bill_to', '789 Marine Drive', 'Mumbai', 'Maharashtra', '400001'),
(2, 'ship_to', '101 Navi Mumbai Zone', 'Navi Mumbai', 'Maharashtra', '400703'),
-- Customer 3: Digital Corp
(3, 'bill_to', '321 Nehru Place', 'Delhi', 'Delhi', '110019'),
(3, 'ship_to', '654 Gurgaon Sector 18', 'Gurgaon', 'Haryana', '122015'),
-- Customer 4: Business Analytics
(4, 'bill_to', '987 Koregaon Park', 'Pune', 'Maharashtra', '411001'),
(4, 'ship_to', '222 Hinjewadi IT Park', 'Pune', 'Maharashtra', '411057'),
-- Customer 5: Enterprise Systems
(5, 'bill_to', '555 MG Road', 'Bangalore', 'Karnataka', '560052'),
(5, 'ship_to', '777 Whitefield', 'Bangalore', 'Karnataka', '560066');

-- Insert Sample Data: Purchase Orders
INSERT INTO purchase_orders (po_number, creation_date, customer_id, total_amount, currency) VALUES
('PO-001', '2025-01-15', 1, 150000.00, 'INR'),
('PO-002', '2025-02-20', 2, 250000.00, 'INR'),
('PO-003', '2025-03-10', 3, 180000.00, 'USD'),
('PO-004', '2025-04-05', 4, 120000.00, 'INR'),
('PO-005', '2025-05-12', 5, 300000.00, 'INR');

-- Insert Sample Data: Invoices
INSERT INTO invoices (invoice_number, po_id, contact_person, amount, currency, invoice_date) VALUES
('INV-001', 1, 'Amit Kumar', 150000.00, 'INR', '2025-02-01'),
('INV-002', 2, 'Priya Patel', 250000.00, 'INR', '2025-03-15'),
('INV-003', 3, 'Rahul Sharma', 180000.00, 'USD', '2025-04-01'),
('INV-004', 4, 'Sneha Reddy', 120000.00, 'INR', '2025-05-10'),
('INV-005', 5, 'Vijay Singh', 300000.00, 'INR', '2025-06-05');

-- Insert Sample Data: Sales Orders
INSERT INTO sales_orders (so_number, customer_id, contracting_parties) VALUES
('SO-001', 1, 'Tech Innovations Pvt Ltd and Company XYZ'),
('SO-002', 2, 'Global Solutions Inc and Partner ABC'),
('SO-003', 3, 'Digital Corp and Client DEF'),
('SO-004', 4, 'Business Analytics Ltd and Vendor GHI'),
('SO-005', 5, 'Enterprise Systems and Contractor JKL');

-- Insert Sample Data: Work Orders
INSERT INTO work_orders (so_id, start_date, end_date, authorized_signatory) VALUES
(1, '2025-02-01', '2025-05-01', 'John Doe - Manager'),
(2, '2025-03-15', '2025-06-15', 'Jane Smith - Director'),
(3, '2025-04-01', '2025-07-01', 'Mike Johnson - VP'),
(4, '2025-05-10', '2025-08-10', 'Sarah Wilson - Lead'),
(5, '2025-06-05', '2025-09-05', 'David Brown - Executive');

-- Insert Sample Data: Deliverables
INSERT INTO deliverables (so_id, description, status) VALUES
(1, 'Software Development and Testing', 'Completed'),
(1, 'Documentation and Training', 'Pending'),
(2, 'System Integration Services', 'In Progress'),
(2, 'Data Migration', 'Completed'),
(3, 'Cloud Setup and Configuration', 'Pending'),
(4, 'Analytics Dashboard Development', 'In Progress'),
(5, 'Hardware Procurement and Installation', 'Completed');
