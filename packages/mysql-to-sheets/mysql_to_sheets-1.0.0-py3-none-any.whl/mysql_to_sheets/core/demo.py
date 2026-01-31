"""Demo database management for evaluation and testing.

Provides a pre-populated SQLite database with sample data for users
to try the sync functionality without connecting to a real database.
"""

import logging
import sqlite3
from pathlib import Path

from mysql_to_sheets.core.paths import get_data_dir

logger = logging.getLogger(__name__)

# Sample data constants
SAMPLE_CUSTOMERS = [
    (1, "Alice Johnson", "alice@example.com", "2024-01-15 10:30:00", "active"),
    (2, "Bob Smith", "bob@example.com", "2024-01-16 14:22:00", "active"),
    (3, "Carol Williams", "carol@example.com", "2024-01-17 09:15:00", "active"),
    (4, "David Brown", "david@example.com", "2024-01-18 16:45:00", "inactive"),
    (5, "Eve Davis", "eve@example.com", "2024-01-19 11:00:00", "active"),
    (6, "Frank Miller", "frank@example.com", "2024-01-20 13:30:00", "pending"),
    (7, "Grace Wilson", "grace@example.com", "2024-01-21 08:45:00", "active"),
    (8, "Henry Moore", "henry@example.com", "2024-01-22 15:20:00", "active"),
    (9, "Ivy Taylor", "ivy@example.com", "2024-01-23 10:10:00", "inactive"),
    (10, "Jack Anderson", "jack@example.com", "2024-01-24 12:00:00", "active"),
]

SAMPLE_PRODUCTS = [
    (1, "Widget Pro", "Electronics", 29.99),
    (2, "Gadget X", "Electronics", 49.99),
    (3, "Basic Notebook", "Office Supplies", 4.99),
    (4, "Premium Pen Set", "Office Supplies", 19.99),
    (5, "Desk Organizer", "Office Supplies", 34.99),
    (6, "USB Cable", "Electronics", 9.99),
    (7, "Wireless Mouse", "Electronics", 24.99),
    (8, "Coffee Mug", "Kitchen", 12.99),
    (9, "Water Bottle", "Kitchen", 15.99),
    (10, "Backpack", "Accessories", 45.99),
]

SAMPLE_ORDERS = [
    (1, 1, 79.98, "2024-01-25"),
    (2, 2, 49.99, "2024-01-25"),
    (3, 3, 24.98, "2024-01-26"),
    (4, 1, 29.99, "2024-01-26"),
    (5, 5, 45.99, "2024-01-27"),
    (6, 7, 34.99, "2024-01-27"),
    (7, 2, 59.97, "2024-01-28"),
    (8, 8, 12.99, "2024-01-28"),
    (9, 10, 69.98, "2024-01-29"),
    (10, 3, 19.99, "2024-01-29"),
    (11, 4, 49.99, "2024-01-30"),
    (12, 6, 79.98, "2024-01-30"),
    (13, 1, 24.99, "2024-01-31"),
    (14, 5, 15.99, "2024-01-31"),
    (15, 9, 34.99, "2024-02-01"),
]


def get_demo_db_path() -> Path:
    """Get path to demo database file.

    Returns:
        Path to demo.db in the data directory.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "demo.db"


def create_demo_database(force: bool = False) -> Path:
    """Create demo database with sample data.

    Creates a SQLite database with sample_customers, sample_orders,
    and sample_products tables populated with test data.

    Args:
        force: If True, recreate database even if it exists.

    Returns:
        Path to the created database file.

    Example:
        >>> db_path = create_demo_database()
        >>> print(f"Demo database created at: {db_path}")
    """
    db_path = get_demo_db_path()

    if db_path.exists() and not force:
        logger.debug(f"Demo database already exists at {db_path}")
        return db_path

    logger.info(f"Creating demo database at {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Create sample_customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sample_customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        # Create sample_products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sample_products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)

        # Create sample_orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sample_orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                order_date TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES sample_customers(id)
            )
        """)

        # Clear existing data if forcing recreate
        if force:
            cursor.execute("DELETE FROM sample_orders")
            cursor.execute("DELETE FROM sample_products")
            cursor.execute("DELETE FROM sample_customers")

        # Insert sample data
        cursor.executemany(
            "INSERT OR REPLACE INTO sample_customers (id, name, email, created_at, status) VALUES (?, ?, ?, ?, ?)",
            SAMPLE_CUSTOMERS,
        )

        cursor.executemany(
            "INSERT OR REPLACE INTO sample_products (id, name, category, price) VALUES (?, ?, ?, ?)",
            SAMPLE_PRODUCTS,
        )

        cursor.executemany(
            "INSERT OR REPLACE INTO sample_orders (id, customer_id, amount, order_date) VALUES (?, ?, ?, ?)",
            SAMPLE_ORDERS,
        )

        conn.commit()
        logger.info(
            f"Demo database created with {len(SAMPLE_CUSTOMERS)} customers, "
            f"{len(SAMPLE_PRODUCTS)} products, {len(SAMPLE_ORDERS)} orders"
        )

    finally:
        conn.close()

    return db_path


def cleanup_demo_database() -> bool:
    """Remove demo database file.

    Returns:
        True if file was removed, False if it didn't exist.
    """
    db_path = get_demo_db_path()

    if db_path.exists():
        db_path.unlink()
        logger.info(f"Removed demo database at {db_path}")
        return True

    return False


def demo_database_exists() -> bool:
    """Check if demo database exists.

    Returns:
        True if demo database file exists.
    """
    return get_demo_db_path().exists()


def get_demo_queries() -> list[dict[str, str]]:
    """Get list of example queries for demo database.

    Returns:
        List of dicts with 'name' and 'query' keys.
    """
    return [
        {
            "name": "All Customers",
            "query": "SELECT * FROM sample_customers ORDER BY id",
        },
        {
            "name": "Active Customers",
            "query": "SELECT * FROM sample_customers WHERE status = 'active'",
        },
        {
            "name": "All Products",
            "query": "SELECT * FROM sample_products ORDER BY category, name",
        },
        {
            "name": "Products by Category",
            "query": "SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM sample_products GROUP BY category",
        },
        {
            "name": "Recent Orders",
            "query": "SELECT * FROM sample_orders ORDER BY order_date DESC LIMIT 10",
        },
        {
            "name": "Customer Orders Summary",
            "query": """
                SELECT
                    c.name,
                    c.email,
                    COUNT(o.id) as order_count,
                    SUM(o.amount) as total_spent
                FROM sample_customers c
                LEFT JOIN sample_orders o ON c.id = o.customer_id
                GROUP BY c.id
                ORDER BY total_spent DESC
            """,
        },
        {
            "name": "Top Products by Revenue",
            "query": """
                SELECT
                    p.name,
                    p.category,
                    p.price,
                    COUNT(o.id) as times_ordered
                FROM sample_products p
                LEFT JOIN sample_orders o ON p.price = o.amount
                GROUP BY p.id
                ORDER BY times_ordered DESC
            """,
        },
    ]
