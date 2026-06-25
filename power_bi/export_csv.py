import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "ecommerce_analytics.db")
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "data")

def export_db_to_csv():
    """Exports SQLite tables and custom analytical queries to CSV for Power BI load."""
    print("Initializing exports...")
    
    # Ensure export directory exists
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        print(f"Created directory: {EXPORT_DIR}")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Define exports (Table Name, Output CSV Name, and optional Custom SQL Query)
    exports = [
        ("users", "users.csv", "SELECT * FROM users;"),
        ("products", "products.csv", "SELECT * FROM products;"),
        ("orders", "orders.csv", "SELECT * FROM orders;"),
        ("order_items", "order_items.csv", "SELECT * FROM order_items;"),
        ("web_events", "web_events.csv", "SELECT * FROM web_events;"),
        
        # We also pre-compute the RFM Segments and Cohort Retention to make it easy for direct loading
        ("rfm_analysis", "rfm_analysis.csv", """
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
                    NTILE(4) OVER (ORDER BY recency DESC) AS r_score,
                    NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
                    NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
                FROM rfm_base
            )
            SELECT 
                user_id,
                customer_name,
                ROUND(recency, 1) AS days_since_last_purchase,
                frequency AS order_count,
                ROUND(monetary, 2) AS total_spend,
                (5 - r_score) AS recency_score,
                f_score AS frequency_score,
                m_score AS monetary_score,
                CASE 
                    WHEN (5 - r_score) >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
                    WHEN (5 - r_score) >= 3 AND f_score < 3 THEN 'Recent Buyers'
                    WHEN (5 - r_score) < 3 AND f_score >= 3 THEN 'At Risk'
                    WHEN (5 - r_score) <= 2 AND f_score <= 2 THEN 'Lost Customers'
                    ELSE 'Average Active Customer'
                END AS customer_segment
            FROM rfm_scores;
        """)
    ]
    
    exported_files = []
    
    for table_name, filename, query in exports:
        output_path = os.path.join(EXPORT_DIR, filename)
        print(f"Exporting {table_name} to {filename}...")
        
        cursor.execute(query)
        
        # Get headers
        headers = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers) # Write headers
            writer.writerows(rows)   # Write rows
            
        print(f"Saved {len(rows)} rows to {output_path}")
        exported_files.append(output_path)
        
    conn.close()
    print("All exports completed successfully!")
    return len(exported_files)

if __name__ == "__main__":
    export_db_to_csv()
