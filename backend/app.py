import http.server
import socketserver
import json
import sqlite3
import os
import re
from datetime import datetime

PORT = 8000
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "ecommerce_analytics.db")
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class ECommerceAnalyticsHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Initialize with the frontend directory as the root for static files
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        # Route API requests
        if self.path == "/api/kpis":
            self.handle_kpis()
        elif self.path == "/api/revenue-trends":
            self.handle_revenue_trends()
        elif self.path == "/api/category-performance":
            self.handle_category_performance()
        elif self.path == "/api/top-products":
            self.handle_top_products()
        elif self.path == "/api/funnel":
            self.handle_funnel()
        elif self.path == "/api/channels":
            self.handle_channels()
        elif self.path == "/api/cohorts":
            self.handle_cohorts()
        else:
            # Fallback to serving static files from frontend/
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/sql":
            self.handle_sql_playground()
        elif self.path == "/api/export-csv":
            self.handle_export_csv()
        else:
            self.send_error_response(404, "Endpoint not found")

    def handle_export_csv(self):
        try:
            import sys
            root_dir = os.path.dirname(os.path.dirname(__file__))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
            from power_bi.export_csv import export_db_to_csv
            count = export_db_to_csv()
            self.send_json_response({"status": "success", "file_count": count})
        except Exception as e:
            self.send_error_response(500, str(e))

    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def send_error_response(self, status_code, message):
        self.send_json_response({"error": message}, status_code)

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    # --- API ENDPOINTS HANDLERS ---

    def handle_kpis(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Overall metrics
            cursor.execute("""
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
            """)
            row = cursor.fetchone()
            
            # Conversion rate
            cursor.execute("""
                WITH session_events AS (
                    SELECT 
                        session_id,
                        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS made_purchase
                    FROM web_events
                    GROUP BY session_id
                )
                SELECT 
                    ROUND(CAST(SUM(made_purchase) AS REAL) / COUNT(*) * 100, 2) AS conversion_rate
                FROM session_events;
            """)
            conv_row = cursor.fetchone()
            
            conn.close()

            response_data = {
                "total_revenue": row["total_revenue"],
                "total_cost": row["total_cost"],
                "gross_profit": row["gross_profit"],
                "gross_margin_percent": row["gross_margin_percent"],
                "total_orders": row["total_orders"],
                "average_order_value": row["average_order_value"],
                "conversion_rate": conv_row["conversion_rate"] if conv_row else 0.0
            }
            self.send_json_response(response_data)
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_revenue_trends(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
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
            """)
            rows = cursor.fetchall()
            conn.close()

            data = [dict(row) for row in rows]
            self.send_json_response(data)
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_category_performance(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
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
            """)
            rows = cursor.fetchall()
            conn.close()

            data = [dict(row) for row in rows]
            self.send_json_response(data)
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_top_products(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
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
            """)
            rows = cursor.fetchall()
            conn.close()

            data = [dict(row) for row in rows]
            self.send_json_response(data)
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_funnel(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
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
                    SUM(made_purchase) AS sessions_with_purchase
                FROM session_events;
            """)
            row = cursor.fetchone()
            conn.close()

            self.send_json_response(dict(row))
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_channels(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    u.acquisition_channel,
                    COUNT(DISTINCT u.user_id) AS total_users,
                    COUNT(DISTINCT o.order_id) AS total_orders,
                    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
                FROM users u
                LEFT JOIN orders o ON u.user_id = o.user_id AND o.status != 'Cancelled'
                LEFT JOIN order_items oi ON o.order_id = oi.order_id
                GROUP BY 1
                ORDER BY total_revenue DESC;
            """)
            rows = cursor.fetchall()
            conn.close()

            data = [dict(row) for row in rows]
            self.send_json_response(data)
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_cohorts(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                WITH cohort_sizes AS (
                    SELECT 
                        strftime('%Y-%m', signup_date) AS cohort_month,
                        COUNT(DISTINCT user_id) AS cohort_size
                    FROM users
                    GROUP BY 1
                ),
                user_orders_month AS (
                    SELECT 
                        u.user_id,
                        strftime('%Y-%m', u.signup_date) AS cohort_month,
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
                WHERE uom.period_month >= 0 AND uom.period_month <= 6
                GROUP BY 1, 2, 3
                ORDER BY 1, 3;
            """)
            rows = cursor.fetchall()
            conn.close()

            # Format database result into a cohort matrix
            cohorts = {}
            for r in rows:
                m = r["cohort_month"]
                if m not in cohorts:
                    cohorts[m] = {
                        "cohort_month": m,
                        "size": r["cohort_size"],
                        "retention": {}
                    }
                if r["period_month"] is not None:
                    cohorts[m]["retention"][r["period_month"]] = r["retention_rate"]

            # Convert to list sorted by cohort month
            cohort_list = sorted(list(cohorts.values()), key=lambda x: x["cohort_month"])
            self.send_json_response(cohort_list)
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_sql_playground(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            body = json.loads(post_data)
            query = body.get("query", "").strip()

            if not query:
                self.send_error_response(400, "Empty query")
                return

            # Safety check: enforce read-only
            # We reject queries containing modification statements
            forbidden_keywords = r"\b(insert|update|delete|drop|alter|create|replace|truncate|grant|revoke|reindex)\b"
            if re.search(forbidden_keywords, query, re.IGNORECASE):
                self.send_error_response(403, "Query rejected. Only SELECT and WITH statements are allowed.")
                return

            # Ensure it starts with select or with (case insensitive)
            if not query.lower().startswith("select") and not query.lower().startswith("with"):
                self.send_error_response(403, "Query rejected. Query must begin with SELECT or WITH.")
                return

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Fetch column headers
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch limited rows to prevent crashing the client
            rows = cursor.fetchmany(100)
            conn.close()

            # Format row data as list of lists
            row_data = []
            for row in rows:
                row_data.append(list(row))

            self.send_json_response({
                "columns": columns,
                "rows": row_data,
                "row_count": len(rows),
                "has_more": len(rows) == 100
            })
        except Exception as e:
            self.send_error_response(400, str(e))

if __name__ == "__main__":
    # Ensure database exists before launching
    if not os.path.exists(DB_PATH):
        print(f"Warning: SQLite database not found at {DB_PATH}. Please run the generator first.")

    # Configure server
    handler = ECommerceAnalyticsHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"E-Commerce Analytics Server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
