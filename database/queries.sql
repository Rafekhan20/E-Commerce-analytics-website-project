-- SQL Queries for E-Commerce Analytics Dashboard
-- This file contains analytical queries that compute KPIs, trends, and behavioral segments.

-- ==========================================
-- 1. REVENUE ANALYSIS
-- ==========================================

-- Query: Overall Sales KPIs
-- Computes total revenue, total cost, gross profit, gross profit margin, total orders, and Average Order Value (AOV)
SELECT 
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
    ROUND(SUM(oi.quantity * p.cost), 2) AS total_cost,
    ROUND(SUM(oi.quantity * (oi.unit_price - p.cost)), 2) AS gross_profit,
    ROUND((SUM(oi.quantity * (oi.unit_price - p.cost)) / SUM(oi.quantity * oi.unit_price)) * 100, 2) AS gross_margin_percent,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) AS average_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status != 'Cancelled';


-- Query: Monthly Revenue, Orders, and Gross Margin Trends
-- Used to display the revenue growth line chart
SELECT 
    strftime('%Y-%m', o.order_date) AS order_month,
    COUNT(DISTINCT o.order_id) AS orders_count,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_revenue,
    ROUND(SUM(oi.quantity * (oi.unit_price - p.cost)), 2) AS monthly_profit,
    ROUND((SUM(oi.quantity * (oi.unit_price - p.cost)) / SUM(oi.quantity * oi.unit_price)) * 100, 2) AS profit_margin_percent
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status != 'Cancelled'
GROUP BY 1
ORDER BY 1 ASC;


-- Query: Sales and Margin by Product Category
-- Used for the Category Performance Bar/Donut Charts
SELECT 
    p.category,
    COUNT(DISTINCT o.order_id) AS orders_count,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue,
    ROUND(SUM(oi.quantity * (oi.unit_price - p.cost)), 2) AS gross_profit,
    ROUND((SUM(oi.quantity * (oi.unit_price - p.cost)) / SUM(oi.quantity * oi.unit_price)) * 100, 2) AS margin_percent
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status != 'Cancelled'
GROUP BY 1
ORDER BY revenue DESC;


-- ==========================================
-- 2. PRODUCT PERFORMANCE
-- ==========================================

-- Query: Top 10 Selling Products by Revenue
SELECT 
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
    ROUND(SUM(oi.quantity * (oi.unit_price - p.cost)), 2) AS total_profit
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status != 'Cancelled'
GROUP BY p.product_id
ORDER BY total_revenue DESC
LIMIT 10;


-- Query: Inventory Health and Turnover rate
-- Compares sales rate with remaining stock
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.stock_quantity AS current_stock,
    COALESCE(SUM(oi.quantity), 0) AS units_sold_1yr,
    CASE 
        WHEN p.stock_quantity = 0 THEN 'OUT OF STOCK'
        WHEN p.stock_quantity < 15 THEN 'LOW STOCK ALERT'
        ELSE 'HEALTHY'
    END AS stock_status
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.order_id AND o.status != 'Cancelled'
GROUP BY p.product_id
ORDER BY current_stock ASC;


-- ==========================================
-- 3. CUSTOMER BEHAVIOR & FUNNEL ANALYSIS
-- ==========================================

-- Query: Web Conversion Funnel (Sessions -> Views -> Cart -> Purchase)
-- Calculated using the web_events clickstream table
WITH session_events AS (
    SELECT 
        session_id,
        MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) AS visited_home,
        MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS viewed_product,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS added_to_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS made_purchase
    FROM web_events
    GROUP BY session_id
)
SELECT 
    COUNT(*) AS total_sessions,
    SUM(viewed_product) AS sessions_with_product_view,
    SUM(added_to_cart) AS sessions_with_cart_add,
    SUM(made_purchase) AS sessions_with_purchase,
    ROUND(CAST(SUM(viewed_product) AS REAL) / COUNT(*) * 100, 2) AS home_to_view_rate,
    ROUND(CAST(SUM(added_to_cart) AS REAL) / SUM(viewed_product) * 100, 2) AS view_to_cart_rate,
    ROUND(CAST(SUM(made_purchase) AS REAL) / SUM(added_to_cart) * 100, 2) AS cart_to_purchase_rate,
    ROUND(CAST(SUM(made_purchase) AS REAL) / COUNT(*) * 100, 2) AS overall_conversion_rate
FROM session_events;


-- Query: User Acquisition Channel Conversion Performance
SELECT 
    u.acquisition_channel,
    COUNT(DISTINCT u.user_id) AS total_users_signed_up,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
    ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT u.user_id), 2) AS revenue_per_acquired_user
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id AND o.status != 'Cancelled'
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY 1
ORDER BY total_revenue DESC;


-- Query: RFM Segmentation (Recency, Frequency, Monetary Value)
-- Classifies users into segments to optimize marketing campaigns
WITH rfm_base AS (
    SELECT 
        u.user_id,
        u.first_name || ' ' || u.last_name AS customer_name,
        julianday('now') - julianday(MAX(o.order_date)) AS recency,
        COUNT(DISTINCT o.order_id) AS frequency,
        SUM(oi.quantity * oi.unit_price) AS monetary
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'Completed'
    GROUP BY u.user_id
),
rfm_scores AS (
    SELECT 
        user_id,
        customer_name,
        recency,
        frequency,
        monetary,
        -- SQLite doesn't support NTILE() as nicely in older versions or some setups, 
        -- so we do case-based scoring or standard NTILING for modern SQLite:
        NTILE(4) OVER (ORDER BY recency DESC) AS r_score,       -- Higher score is LESS recent (older purchase) in standard NTILE, so we invert it next
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,     -- Higher score is more frequent
        NTILE(4) OVER (ORDER BY monetary ASC) AS m_score       -- Higher score is higher spend
    )
SELECT 
    user_id,
    customer_name,
    ROUND(recency, 1) AS days_since_last_purchase,
    frequency AS order_count,
    ROUND(monetary, 2) AS total_spend,
    (5 - r_score) AS r_score_final, -- Invert so 4 is highly recent, 1 is inactive
    f_score,
    m_score,
    CASE 
        WHEN (5 - r_score) >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions (Loyal & High Spenders)'
        WHEN (5 - r_score) >= 3 AND f_score < 3 THEN 'Recent Buyers (New Customers)'
        WHEN (5 - r_score) < 3 AND f_score >= 3 THEN 'At Risk (Loyal but Inactive)'
        WHEN (5 - r_score) <= 2 AND f_score <= 2 THEN 'Lost Customers'
        ELSE 'Average Active Customer'
    END AS customer_segment
FROM rfm_scores
ORDER BY total_spend DESC;


-- Query: Customer Cohort Retention (Month-over-Month)
-- Group customers by their signup month and track how many make purchases in subsequent months.
WITH cohort_sizes AS (
    -- Size of each cohort based on signup month
    SELECT 
        strftime('%Y-%m', signup_date) AS cohort_month,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM users
    GROUP BY 1
),
user_orders_month AS (
    -- List of order months per user
    SELECT 
        u.user_id,
        strftime('%Y-%m', u.signup_date) AS cohort_month,
        strftime('%Y-%m', o.order_date) AS order_month,
        -- Calculate difference in months
        (strftime('%Y', o.order_date) - strftime('%Y', u.signup_date)) * 12 + 
        (strftime('%m', o.order_date) - strftime('%m', u.signup_date)) AS period_month
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    WHERE o.status = 'Completed'
)
SELECT 
    cs.cohort_month,
    cs.cohort_size,
    uom.period_month,
    COUNT(DISTINCT uom.user_id) AS active_users,
    ROUND(CAST(COUNT(DISTINCT uom.user_id) AS REAL) / cs.cohort_size * 100, 2) AS retention_rate
FROM cohort_sizes cs
LEFT JOIN user_orders_month uom ON cs.cohort_month = uom.cohort_month
WHERE uom.period_month >= 0 AND uom.period_month <= 6 -- View first 6 months
GROUP BY 1, 2, 3
ORDER BY 1, 3;
