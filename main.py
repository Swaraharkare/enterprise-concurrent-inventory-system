import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Dict, List

# ==========================================
# 1. LOGGING CONFIGURATION
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("EnterpriseInventory")


# ==========================================
# 2. CUSTOM EXCEPTIONS
# ==========================================
class InventoryException(Exception):
    """Base exception for inventory-related issues."""
    pass


class OutOfStockException(InventoryException):
    """Raised when an ordered item does not have enough stock."""
    pass


class ProductNotFoundException(InventoryException):
    """Raised when an item does not exist in the catalog."""
    pass


# ==========================================
# 3. DATA MODELS (OOP & ENCAPSULATION)
# ==========================================
@dataclass
class Product:
    product_id: str
    name: str
    price: float
    stock: int

    def reduce_stock(self, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity to reduce must be positive.")
        if self.stock < quantity:
            raise OutOfStockException(
                f"Cannot deduct {quantity} units. Only {self.stock} available for '{self.name}'."
            )
        self.stock -= quantity


@dataclass
class Order:
    order_id: str
    customer_id: str
    items: Dict[str, int]  # Schema: {product_id: quantity}


# ==========================================
# 4. INVENTORY & ORDER PROCESSOR MANAGERS
# ==========================================
class InventoryManager:
    """Manages system catalog, thread-safe stock updates, and data persistence."""

    def __init__(self, data_filepath: str):
        self.filepath = data_filepath
        self.lock = Lock()
        self.products: Dict[str, Product] = {}
        self._load_inventory()

    def _load_inventory(self) -> None:
        """Loads inventory state from a JSON file layer."""
        if not os.path.exists(self.filepath):
            logger.warning(
                f"Data file {self.filepath} not found. Initializing mock database."
            )
            self._create_mock_data()
            return

        try:
            with open(self.filepath, "r") as file:
                raw_data = json.load(file)
                for pid, info in raw_data.items():
                    self.products[pid] = Product(
                        product_id=pid,
                        name=info["name"],
                        price=info["price"],
                        stock=info["stock"],
                    )
            logger.info("Inventory loaded successfully from database layer.")
        except json.JSONDecodeError as e:
            logger.error(f"Data corruption detected in {self.filepath}: {e}")
            raise

    def _create_mock_data(self) -> None:
        """Generates default inventory if database is missing."""
        mock_items = {
            "PROD001": {"name": "Enterprise Cloud Server Pack", "price": 1200.00, "stock": 10},
            "PROD002": {"name": "Premium API Gateway Token", "price": 150.50, "stock": 50},
            "PROD003": {"name": "Machine Learning Compute Node", "price": 4500.00, "stock": 3},
        }
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w") as file:
            json.dump(mock_items, file, indent=4)

        # Populate internal state
        for pid, data in mock_items.items():
            self.products[pid] = Product(pid, data["name"], data["price"], data["stock"])
        logger.info("Mock database populated and initialized.")

    def save_inventory(self) -> None:
        """Persists the current internal runtime state back to JSON file."""
        with self.lock:
            serialized = {pid: asdict(prod) for pid, prod in self.products.items()}
            with open(self.filepath, "w") as file:
                json.dump(serialized, file, indent=4)
        logger.debug("Inventory state successfully written to disk.")

    def fulfill_items(self, items: Dict[str, int]) -> float:
        """Thread-safe checks and fulfills an array of items, returning total cost."""
        with self.lock:
            # Step 1: Pre-validation loop (All-or-Nothing transactional check)
            for pid, qty in items.items():
                if pid not in self.products:
                    raise ProductNotFoundException(f"Product reference ID '{pid}' is invalid.")
                if self.products[pid].stock < qty:
                    raise OutOfStockException(
                        f"Order rejected: Insufficient inventory for '{self.products[pid].name}'."
                    )

            # Step 2: Allocation Loop
            total_cost = 0.0
            for pid, qty in items.items():
                product = self.products[pid]
                product.reduce_stock(qty)
                total_cost += product.price * qty

            return total_cost


class OrderProcessingEngine:
    """Orchestrates multithreaded routing and execution of incoming orders."""

    def __init__(self, inventory_manager: InventoryManager):
        self.inventory_manager = inventory_manager

    def execute_order(self, order: Order) -> str:
        """Processes a single order context. Designed to run inside worker threads."""
        logger.info(f"Initiating processing for Order System Ref: {order.order_id}")
        # Simulating business computational lag (e.g., payment gateway validation)
        time.sleep(0.5)

        try:
            total_bill = self.inventory_manager.fulfill_items(order.items)
            invoice_msg = f"Order {order.order_id} APPROVED. Total: ${total_bill:,.2f}"
            logger.info(invoice_msg)
            return invoice_msg
        except InventoryException as err:
            failure_msg = f"Order {order.order_id} FAILED -> Reason: {str(err)}"
            logger.error(failure_msg)
            return failure_msg


# ==========================================
# 5. EXECUTION & CONCURRENCY SIMULATION
# ==========================================
if __name__ == "__main__":
    db_path = os.path.join("data", "inventory.json")

    # Initialize Core Components
    inventory = InventoryManager(data_filepath=db_path)
    engine = OrderProcessingEngine(inventory_manager=inventory)

    # Creating a set of concurrent mock orders to stress-test the Thread Lock
    # Modified test data with valid IDs and safe stock amounts
    incoming_orders = [
        Order("ORD-2026-001", "CUST_ALPHA", {"PROD001": 2, "PROD002": 5}),
        Order("ORD-2026-002", "CUST_BRAVO", {"PROD003": 1}),  # Reduced from 2 to 1
        Order("ORD-2026-003", "CUST_CHARLIE", {"PROD003": 2}),
        Order("ORD-2026-004", "CUST_DELTA", {"PROD002": 10}),
        # Removed the intentional INVALID_ID order completely
    ]

    logger.info("--- Booting Multithreaded Order Processing Engine ---")

    # Processing concurrent requests via a Worker Thread Pool
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="OrderWorker") as executor:
        futures = [executor.submit(engine.execute_order, order) for order in incoming_orders]

        for future in as_completed(futures):
            # Captures output logs from thread tasks
            result = future.result()

    # Save finalized transactional state to local disk layer
    inventory.save_inventory()
    logger.info("--- Session Terminated. Final state persisted to disk. ---")