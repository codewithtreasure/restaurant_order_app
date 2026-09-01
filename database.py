import os
import sqlite3
import json
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canteen.db")
FOOD_IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "food-images")

DEFAULT_FOOD_ITEMS = [
    # Swallows & Soups
    {
        "name": "Amala & Ewedu / Gbegiri",
        "category": "Swallows & Soups",
        "price": 1200.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_1024485269_CDOWpJTqwJGltwXXKGj0cJVi6uVQcQ7M.jpg"),
        "description": "Hot fluffy Amala served with authentic Yorùbá Ewedu and Gbegiri soup.",
        "is_available": 1,
    },
    {
        "name": "Eba & Egusi Soup",
        "category": "Swallows & Soups",
        "price": 1000.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_2113356951_sESUmlVYv7mYHpiW5MOk2f857r626q7R.jpg"),
        "description": "Yellow Garri Eba served with rich melon Egusi soup enriched with vegetables.",
        "is_available": 1,
    },
    {
        "name": "Pounded Yam (Iyan) & Efo Riro",
        "category": "Swallows & Soups",
        "price": 1500.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_221241321_PIn6TJUwdqRQjzYfkSPuusn5BdxLHzIX.jpg"),
        "description": "Smooth, pounded yam served with spicy vegetable Efo Riro stew.",
        "is_available": 1,
    },
    {
        "name": "Fufu & Ogbono Soup",
        "category": "Swallows & Soups",
        "price": 1000.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_235070270_ATYb6MZoLUmObHbgxwlNWJfz9LroFHIF.jpg"),
        "description": "Traditional Cassava Fufu paired with delicious draw Ogbono soup.",
        "is_available": 1,
    },
    {
        "name": "Semovita & Okra Soup",
        "category": "Swallows & Soups",
        "price": 1100.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_639370634_xD49nGqgcvRSMP69ugxWGkTp0kR8KhrF.jpg"),
        "description": "Soft Semovita served with fresh seafood and meat Okra soup.",
        "is_available": 1,
    },

    # Rice & Staples
    {
        "name": "Special Jollof Rice",
        "category": "Rice & Staples",
        "price": 1800.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_245963366_BqND8GrTG5yEQsT7ZZliyV1p2EsNDKzE.jpg"),
        "description": "Smoky Nigerian Party Jollof Rice cooked with aromatic herbs & spices.",
        "is_available": 1,
    },
    {
        "name": "Nigerian Fried Rice",
        "category": "Rice & Staples",
        "price": 1800.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_258080424_XlJ0nbRS7QnWDmGOlqkGfrjiEIJq5tRT.jpg"),
        "description": "Delicious fried rice loaded with diced liver, sweet peas, and carrots.",
        "is_available": 1,
    },
    {
        "name": "Ofada Rice & Ayamase Sauce",
        "category": "Rice & Staples",
        "price": 2500.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_331348043_D1HmdqaBu77rgz1fBpL2hbEgfXaQa8Sd.jpg"),
        "description": "Local unpolished Ofada rice served with spicy green pepper Ayamase stew.",
        "is_available": 1,
    },

    # Proteins & Meat
    {
        "name": "Fried Beef & Assorted Meat",
        "category": "Proteins & Meat",
        "price": 1000.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_339558219_p9s4gBkhbQJCqrWllRT11utqOPdBRFI6.jpg"),
        "description": "Tender seasoned beef and assorted meat portion.",
        "is_available": 1,
    },
    {
        "name": "Peppered Goat Meat (Asun)",
        "category": "Proteins & Meat",
        "price": 1500.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_364169070_C5MuNG6Hdbo4rD27L9GQXp72svPube0e.jpg"),
        "description": "Spicy roasted goat meat cutlets tossed in scotch bonnet peppers.",
        "is_available": 1,
    },
    {
        "name": "Grilled Chicken Portion",
        "category": "Proteins & Meat",
        "price": 1600.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_370760922_o4CeUnkXSAGVjbiG1gSSiokYJjhZFjJu.jpg"),
        "description": "Succulent flame-grilled quarter chicken seasoned with canteen spice mix.",
        "is_available": 1,
    },
    {
        "name": "Fried Fish & Dodo (Plantain)",
        "category": "Proteins & Meat",
        "price": 1200.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_379560913_Ia04VeSuRNndJ3LLWAXVobNbK9rbXjqf.jpg"),
        "description": "Crispy fried catfish/croaker portion with golden fried ripe plantain slices.",
        "is_available": 1,
    },
    {
        "name": "Peppered Snail Special",
        "category": "Proteins & Meat",
        "price": 2800.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_491688945_9lCRX2N6XQVeyJbnM9tWjm2TMTWIiogL.jpg"),
        "description": "Jumbo crunchy African giant snail sautéed in spicy pepper relish.",
        "is_available": 1,
    },
    {
        "name": "Spicy Ponmo (Cow Skin)",
        "category": "Proteins & Meat",
        "price": 600.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_495509521_PZ9aX8oFPvFGcKAsqJWthOGnbDPjR9z5.jpg"),
        "description": "Soft fried Ponmo Alata cooked in spicy red pepper sauce.",
        "is_available": 1,
    },
    {
        "name": "Beef Suya Skewers",
        "category": "Proteins & Meat",
        "price": 2000.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_581961604_zj2eSAU74omNgp786Ta4mDgWlWnP9PLg.jpg"),
        "description": "Northern style spicy grilled beef Suya with sliced onions & Yaji pepper.",
        "is_available": 1,
    },

    # Drinks & Snacks
    {
        "name": "Chilled Zobo Drink (50cl)",
        "category": "Drinks & Snacks",
        "price": 500.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_669807756_XdJJIRhLeWLAnMnK8m6FZcEmBqsxZHMA.jpg"),
        "description": "Refreshing natural Hibiscus Zobo infused with ginger & pineapple flavor.",
        "is_available": 1,
    },
    {
        "name": "Cold Soft Drinks & Malt",
        "category": "Drinks & Snacks",
        "price": 400.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_798668985_vs4JEeED45ihoRe7tBnCcodnhiDzWXSb.jpg"),
        "description": "Ice cold Coca-Cola, Fanta, Sprite, or premium canned Malt drink.",
        "is_available": 1,
    },
    {
        "name": "Fresh Palm Wine / Water",
        "category": "Drinks & Snacks",
        "price": 800.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_857813760_qbMRYBhG3rfrXCaJCMEzTgiBdGBEbmfG.jpg"),
        "description": "Freshly tapped unadulterated Palm Wine or cold bottled spring water.",
        "is_available": 1,
    },
    {
        "name": "Meat Pie & Snacks",
        "category": "Drinks & Snacks",
        "price": 700.0,
        "image_path": os.path.join(FOOD_IMAGES_DIR, "240_F_886880307_8CLg4L9mXWDDCQxgKN5feoXyasoeX08a.jpg"),
        "description": "Richly stuffed Nigerian beef meat pie baked with buttery crust.",
        "is_available": 1,
    },
]


class CanteenDatabase:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Table for Food Items
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS food_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    price REAL NOT NULL,
                    image_path TEXT,
                    description TEXT,
                    is_available INTEGER DEFAULT 1
                )
            """)

            # Table for Receipts / Sales History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_no TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    customer_name TEXT,
                    payment_method TEXT,
                    items_json TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    discount REAL DEFAULT 0.0,
                    total REAL NOT NULL
                )
            """)

            # Table for Invoices
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    customer_name TEXT,
                    customer_email TEXT,
                    customer_phone TEXT,
                    payment_method TEXT,
                    items_json TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    tax REAL DEFAULT 0.0,
                    discount REAL DEFAULT 0.0,
                    total REAL NOT NULL,
                    due_date TEXT,
                    status TEXT DEFAULT 'Pending'
                )
            """)
            conn.commit()

        # Seed initial Nigerian food menu items if empty
        if self.is_food_table_empty():
            self.seed_default_items()

    def is_food_table_empty(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM food_items")
            count = cursor.fetchone()[0]
            return count == 0

    def seed_default_items(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for item in DEFAULT_FOOD_ITEMS:
                cursor.execute("""
                    INSERT INTO food_items (name, category, price, image_path, description, is_available)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item["name"],
                    item["category"],
                    item["price"],
                    item["image_path"],
                    item["description"],
                    item["is_available"]
                ))
            conn.commit()

    def reset_to_default_menu(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM food_items")
            conn.commit()
        self.seed_default_items()

    def get_all_items(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM food_items ORDER BY category, name")
            return [dict(row) for row in cursor.fetchall()]

    def search_items(self, query="", category="All"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM food_items WHERE 1=1"
            params = []

            if category and category != "All":
                sql += " AND category = ?"
                params.append(category)

            if query and query.strip():
                sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
                q_param = f"%{query.strip()}%"
                params.extend([q_param, q_param, q_param])

            sql += " ORDER BY category, name"
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def add_food_item(self, name, category, price, image_path="", description="", is_available=1):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO food_items (name, category, price, image_path, description, is_available)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, category, float(price), image_path, description, int(is_available)))
            conn.commit()
            return cursor.lastrowid

    def update_food_item(self, item_id, name, category, price, image_path="", description="", is_available=1):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE food_items
                SET name = ?, category = ?, price = ?, image_path = ?, description = ?, is_available = ?
                WHERE id = ?
            """, (name, category, float(price), image_path, description, int(is_available), int(item_id)))
            conn.commit()

    def delete_food_item(self, item_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM food_items WHERE id = ?", (int(item_id),))
            conn.commit()

    def save_receipt(self, receipt_no, customer_name, payment_method, items, subtotal, discount, total):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items_json = json.dumps(items)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO receipts (receipt_no, timestamp, customer_name, payment_method, items_json, subtotal, discount, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (receipt_no, timestamp, customer_name, payment_method, items_json, subtotal, discount, total))
            conn.commit()
            return cursor.lastrowid

    def get_all_receipts(self, limit=50):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM receipts ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item_dict = dict(r)
                item_dict["items"] = json.loads(item_dict["items_json"])
                results.append(item_dict)
            return results

    def save_invoice(self, invoice_no, customer_name, customer_email, customer_phone, payment_method, items, subtotal, tax, discount, total, due_date, status="Pending"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items_json = json.dumps(items)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (invoice_no, timestamp, customer_name, customer_email, customer_phone, payment_method, items_json, subtotal, tax, discount, total, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_no, timestamp, customer_name, customer_email, customer_phone, payment_method, items_json, subtotal, tax, discount, total, due_date, status))
            conn.commit()
            return cursor.lastrowid

    def get_all_invoices(self, limit=50):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item_dict = dict(r)
                item_dict["items"] = json.loads(item_dict["items_json"])
                results.append(item_dict)
            return results

    def get_next_invoice_number(self):
        """Generate next invoice number based on current date and count"""
        today = datetime.now().strftime("%Y%m%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE invoice_no LIKE ?", (f"INV-{today}-%",))
            count = cursor.fetchone()[0]
            return f"INV-{today}-{count + 1:04d}"
