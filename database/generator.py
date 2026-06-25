import sqlite3
import random
import os
from datetime import datetime, timedelta

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "ecommerce_analytics.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# Lists of dummy data for realistic generation
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", 
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
               "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", 
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
STATES = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI", "WA", "AZ", "CO", "VA", "MA", "TN", "IN", "MO"]
CHANNELS = ["Organic Search", "Paid Search", "Social Media", "Email Marketing", "Referral", "Direct"]
PAYMENT_METHODS = ["Credit Card", "PayPal", "Debit Card", "Bank Transfer", "Apple Pay"]
CATEGORIES = {
    "Electronics": [
        ("Smart 4K TV", 499.99, 0.55), ("Wireless Headphones", 89.99, 0.40), ("Bluetooth Speaker", 45.99, 0.45),
        ("Smartphone 128GB", 799.99, 0.60), ("Laptop Pro 15\"", 1299.99, 0.65), ("Smartwatch Series X", 199.99, 0.50),
        ("Noise Cancelling Earbuds", 149.99, 0.42), ("Tablet HD 10", 229.99, 0.52)
    ],
    "Fashion": [
        ("Classic Denim Jacket", 59.99, 0.35), ("Leather Sneakers", 79.99, 0.38), ("Cotton T-Shirt (3-Pack)", 24.99, 0.28),
        ("Running Shoes", 99.99, 0.40), ("Slim Fit Chinos", 39.99, 0.32), ("Winter Wool Coat", 149.99, 0.45),
        ("Designer Sunglasses", 119.99, 0.35), ("Canvas Backpack", 34.99, 0.30)
    ],
    "Home & Kitchen": [
        ("Air Fryer Max", 119.99, 0.48), ("Espresso Coffee Machine", 299.99, 0.55), ("Non-Stick Cookware Set", 89.99, 0.40),
        ("Robotic Vacuum Cleaner", 249.99, 0.50), ("Memory Foam Pillow", 29.99, 0.30), ("Stainless Steel Kettle", 39.99, 0.35),
        ("Blender Professional", 79.99, 0.45), ("Chef Knife 8-Inch", 49.99, 0.38)
    ],
    "Books": [
        ("Sci-Fi Bestseller", 14.99, 0.25), ("Self-Improvement Guide", 18.99, 0.20), ("Mystery Thriller Novel", 12.99, 0.22),
        ("Python Programming 101", 39.99, 0.30), ("Business Strategy Handbook", 24.99, 0.28), ("Historical Fiction Epic", 15.99, 0.24),
        ("Children's Story Collection", 9.99, 0.18), ("Cooking Masterclass Book", 29.99, 0.30)
    ],
    "Beauty & Personal Care": [
        ("Hydrating Serum", 28.00, 0.20), ("Electric Toothbrush", 69.99, 0.45), ("Hair Dryer 2000W", 49.99, 0.40),
        ("Matte Lipstick Duo", 19.99, 0.15), ("Moisturizing Cream", 22.50, 0.18), ("Organic Beard Oil", 15.00, 0.12),
        ("Perfume 'Midnight Gold'", 85.00, 0.35), ("Exfoliating Scrub", 14.50, 0.15)
    ],
    "Sports & Outdoors": [
        ("Yoga Mat Extra Thick", 29.99, 0.30), ("Dumbbell Set 20lbs", 49.99, 0.45), ("Hydration Backpack", 39.99, 0.35),
        ("Camping Tent (4-Person)", 129.99, 0.50), ("Resistance Bands Set", 19.99, 0.25), ("Cycling Helmet", 44.99, 0.38),
        ("Sleeping Bag Lightweight", 34.99, 0.32), ("Adjustable Jump Rope", 9.99, 0.20)
    ]
}

def load_schema(conn):
    """Loads the SQL schema into the database."""
    print(f"Loading schema from {SCHEMA_PATH}...")
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()

def generate_ecommerce_data():
    """Generates synthetic e-commerce data and saves it in the database."""
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    load_schema(conn)
    cursor = conn.cursor()

    random.seed(42)  # For deterministic data generation
    start_date = datetime.now() - timedelta(days=365) # 1 year ago
    end_date = datetime.now()

    print("Generating Products...")
    products_db = []
    prod_id = 1
    for category, items in CATEGORIES.items():
        for name, price, cost_multiplier in items:
            cost = round(price * cost_multiplier, 2)
            stock = random.randint(10, 200)
            cursor.execute(
                "INSERT INTO products (product_id, product_name, category, price, cost, stock_quantity) VALUES (?, ?, ?, ?, ?, ?)",
                (prod_id, name, category, price, cost, stock)
            )
            products_db.append({
                "id": prod_id,
                "name": name,
                "category": category,
                "price": price,
                "cost": cost
            })
            prod_id += 1

    print(f"Generated {len(products_db)} products.")

    print("Generating Users...")
    num_users = 1500
    users_db = []
    for u_id in range(1, num_users + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        gender = "Female" if u_id % 2 == 0 else "Male"
        age = random.randint(18, 70)
        state = random.choice(STATES)
        channel = random.choice(CHANNELS)
        
        # Signup date distributed over the last 12 months
        signup_offset = random.randint(0, 360)
        signup_time = start_date + timedelta(days=signup_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        cursor.execute(
            "INSERT INTO users (user_id, signup_date, first_name, last_name, gender, age, state, acquisition_channel) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (u_id, signup_time.strftime("%Y-%m-%d %H:%M:%S"), first, last, gender, age, state, channel)
        )
        users_db.append({
            "id": u_id,
            "signup_date": signup_time,
            "channel": channel
        })

    print(f"Generated {num_users} users.")

    print("Generating Sessions and Transactions...")
    session_counter = 1
    total_sessions = 6000
    
    # We will generate sessions day-by-day to simulate seasonality & growth
    current_time = start_date
    day_step = 1
    
    # Pre-calculate active users pool based on signup dates
    while current_time < end_date:
        # Seasonality factors: Nov & Dec (holiday season) have 1.8x traffic. Spring has 1.2x. Weekends have 1.3x.
        season_multiplier = 1.0
        month = current_time.month
        day_of_week = current_time.weekday() # 5 = Saturday, 6 = Sunday

        if month in [11, 12]:
            season_multiplier *= 1.8
        elif month in [4, 5]:
            season_multiplier *= 1.2
            
        if day_of_week >= 5:
            season_multiplier *= 1.3
            
        # Overall platform growth: users increase over the year, traffic grows
        growth_multiplier = 1.0 + ((current_time - start_date).days / 365.0) * 0.5 # Up to 50% growth
        
        # Base daily sessions
        base_sessions = random.randint(10, 25)
        num_daily_sessions = int(base_sessions * season_multiplier * growth_multiplier)

        # Get list of users signed up before today
        available_users = [u for u in users_db if u["signup_date"] <= current_time]
        if not available_users:
            current_time += timedelta(days=1)
            continue
            
        for _ in range(num_daily_sessions):
            session_id = f"SESS_{session_counter:06d}"
            session_counter += 1
            
            # Select user: 80% existing user, 20% guest (NULL user_id for session, or brand new)
            is_guest = random.random() < 0.15
            user = None
            user_id = None
            if not is_guest:
                user = random.choice(available_users)
                user_id = user["id"]
                
            session_start = current_time + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59), seconds=random.randint(0, 59))
            
            # Session clickstream funnel behavior
            # Step 1: page_view (Always happens)
            cursor.execute(
                "INSERT INTO web_events (session_id, user_id, event_time, event_type, product_id) VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, session_start.strftime("%Y-%m-%d %H:%M:%S"), "page_view", None)
            )
            
            # Step 2: product_view (75% probability)
            t_offset = random.randint(10, 120)
            view_time = session_start + timedelta(seconds=t_offset)
            
            if random.random() < 0.75:
                selected_prod = random.choice(products_db)
                cursor.execute(
                    "INSERT INTO web_events (session_id, user_id, event_time, event_type, product_id) VALUES (?, ?, ?, ?, ?)",
                    (session_id, user_id, view_time.strftime("%Y-%m-%d %H:%M:%S"), "product_view", selected_prod["id"])
                )
                
                # Step 3: add_to_cart (35% probability of adding to cart if product is viewed)
                t_offset += random.randint(10, 120)
                cart_time = view_time + timedelta(seconds=t_offset)
                
                if random.random() < 0.35:
                    # Can add 1 or 2 items
                    cart_items = [selected_prod]
                    if random.random() < 0.25: # 25% chance of adding an additional random product
                        cart_items.append(random.choice(products_db))
                        
                    for prod in cart_items:
                        cursor.execute(
                            "INSERT INTO web_events (session_id, user_id, event_time, event_type, product_id) VALUES (?, ?, ?, ?, ?)",
                            (session_id, user_id, cart_time.strftime("%Y-%m-%d %H:%M:%S"), "add_to_cart", prod["id"])
                        )
                    
                    # Step 4: purchase (40% probability of purchase if items added to cart)
                    # Note: guest users can purchase too, but if they do, we'll associate them with a user or create a user.
                    # For simplicity, only registered users can finalize a purchase in our database model constraint
                    t_offset += random.randint(30, 240)
                    purchase_time = cart_time + timedelta(seconds=t_offset)
                    
                    if user_id is not None and random.random() < 0.40:
                        # Success purchase event
                        cursor.execute(
                            "INSERT INTO web_events (session_id, user_id, event_time, event_type, product_id) VALUES (?, ?, ?, ?, ?)",
                            (session_id, user_id, purchase_time.strftime("%Y-%m-%d %H:%M:%S"), "purchase", None)
                        )
                        
                        # Generate corresponding order and order items
                        # Determine order status: 88% Completed, 5% Shipped, 2% Processing, 3% Returned, 2% Cancelled
                        status_rnd = random.random()
                        if status_rnd < 0.88:
                            status = "Completed"
                        elif status_rnd < 0.93:
                            status = "Shipped"
                        elif status_rnd < 0.95:
                            status = "Processing"
                        elif status_rnd < 0.98:
                            status = "Returned"
                        else:
                            status = "Cancelled"
                            
                        pay_method = random.choice(PAYMENT_METHODS)
                        shipping = round(random.uniform(0.0, 15.0), 2) if random.random() < 0.5 else 0.0 # 50% free shipping
                        
                        # Insert Order Header
                        cursor.execute(
                            "INSERT INTO orders (user_id, order_date, status, payment_method, shipping_cost) VALUES (?, ?, ?, ?, ?)",
                            (user_id, purchase_time.strftime("%Y-%m-%d %H:%M:%S"), status, pay_method, shipping)
                        )
                        order_id = cursor.lastrowid
                        
                        # Insert Order Details
                        total_amount = 0.0
                        for prod in cart_items:
                            quantity = 1
                            if prod["price"] < 30.0:
                                quantity = random.choice([1, 1, 1, 2, 3]) # Higher likelihood of more items for cheaper products
                                
                            item_price = prod["price"]
                            cursor.execute(
                                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                                (order_id, prod["id"], quantity, item_price)
                            )
                            total_amount += (item_price * quantity)
                            
                        # Update the total amount in order (optional for display, but SQL logic works on line items)
                        # We calculate order total on the fly in SQL, but let's make sure our database holds valid details.
                        
        current_time += timedelta(days=1)
        day_step += 1

    conn.commit()
    
    # Let's count what we have
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"Final Users: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"Final Products: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM orders")
    print(f"Final Orders: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM order_items")
    print(f"Final Order Items: {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM web_events")
    print(f"Final Web Events: {cursor.fetchone()[0]}")
    
    conn.close()
    print("Database generation completed successfully!")

def NULL_check_ok(val):
    return val is not None

if __name__ == "__main__":
    generate_ecommerce_data()
