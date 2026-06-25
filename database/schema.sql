-- Database Schema for E-Commerce Analytics
-- This schema represents standard transaction and behavior tables.

PRAGMA foreign_keys = ON;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    signup_date TIMESTAMP NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    age INTEGER,
    state TEXT,
    acquisition_channel TEXT CHECK(acquisition_channel IN ('Organic Search', 'Paid Search', 'Social Media', 'Email Marketing', 'Referral', 'Direct'))
);

-- 2. Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('Electronics', 'Fashion', 'Home & Kitchen', 'Books', 'Beauty & Personal Care', 'Sports & Outdoors')),
    price REAL NOT NULL CHECK(price > 0),
    cost REAL NOT NULL CHECK(cost > 0),
    stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0)
);

-- 3. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Completed', 'Processing', 'Shipped', 'Cancelled', 'Returned')),
    payment_method TEXT CHECK(payment_method IN ('Credit Card', 'PayPal', 'Debit Card', 'Bank Transfer', 'Apple Pay')),
    shipping_cost REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 4. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price > 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 5. Web Events Table (Clickstream data for Customer Behavior Analysis)
CREATE TABLE IF NOT EXISTS web_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id INTEGER,
    event_time TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN ('page_view', 'product_view', 'add_to_cart', 'purchase')),
    product_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL
);

-- Indexes for performance optimization on common query columns
CREATE INDEX IF NOT EXISTS idx_users_signup ON users(signup_date);
CREATE INDEX IF NOT EXISTS idx_users_state ON users(state);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_web_events_session ON web_events(session_id);
CREATE INDEX IF NOT EXISTS idx_web_events_user ON web_events(user_id);
CREATE INDEX IF NOT EXISTS idx_web_events_time ON web_events(event_time);
CREATE INDEX IF NOT EXISTS idx_web_events_type ON web_events(event_type);
