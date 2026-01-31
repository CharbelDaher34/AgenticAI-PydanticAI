"""Mock database for PydanticAI masterclass examples.

This module provides simple in-memory data structures that simulate
a database for learning purposes without requiring actual database setup.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class User:
    """User model for examples."""
    
    id: int
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class Product:
    """Product model for examples."""
    
    id: int
    name: str
    price: float
    category: str
    in_stock: bool = True
    description: Optional[str] = None


@dataclass
class Order:
    """Order model for examples."""
    
    id: int
    user_id: int
    product_id: int
    quantity: int
    order_date: date = field(default_factory=date.today)
    status: str = "pending"


class MockDatabase:
    """In-memory mock database for examples.
    
    Provides simple CRUD operations on mock data structures.
    Thread-safe is NOT guaranteed - for educational purposes only.
    """
    
    def __init__(self):
        """Initialize mock database with sample data."""
        self.users: dict[int, User] = {
            1: User(id=1, name="Alice Johnson", email="alice@example.com"),
            2: User(id=2, name="Bob Smith", email="bob@example.com"),
            3: User(id=3, name="Charlie Brown", email="charlie@example.com"),
        }
        
        self.products: dict[int, Product] = {
            1: Product(
                id=1,
                name="Laptop",
                price=999.99,
                category="Electronics",
                description="High-performance laptop for professionals",
            ),
            2: Product(
                id=2,
                name="Desk Chair",
                price=299.99,
                category="Furniture",
                description="Ergonomic office chair",
            ),
            3: Product(
                id=3,
                name="Coffee Maker",
                price=79.99,
                category="Appliances",
                description="Automatic drip coffee maker",
            ),
            4: Product(
                id=4,
                name="Notebook",
                price=4.99,
                category="Stationery",
                in_stock=False,
            ),
        }
        
        self.orders: dict[int, Order] = {
            1: Order(id=1, user_id=1, product_id=1, quantity=1, status="completed"),
            2: Order(id=2, user_id=2, product_id=3, quantity=2, status="shipped"),
            3: Order(id=3, user_id=1, product_id=2, quantity=1, status="pending"),
        }
        
        self._next_user_id = 4
        self._next_product_id = 5
        self._next_order_id = 4
    
    # User operations
    async def get_user(self, user_id: int) -> Optional[User]:
        """Fetch user by ID."""
        return self.users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email."""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def list_users(self) -> list[User]:
        """List all users."""
        return list(self.users.values())
    
    async def create_user(self, name: str, email: str) -> User:
        """Create a new user."""
        user = User(id=self._next_user_id, name=name, email=email)
        self.users[user.id] = user
        self._next_user_id += 1
        return user
    
    # Product operations
    async def get_product(self, product_id: int) -> Optional[Product]:
        """Fetch product by ID."""
        return self.products.get(product_id)
    
    async def list_products(
        self, category: Optional[str] = None, in_stock_only: bool = False
    ) -> list[Product]:
        """List products with optional filtering."""
        products = list(self.products.values())
        
        if category:
            products = [p for p in products if p.category.lower() == category.lower()]
        
        if in_stock_only:
            products = [p for p in products if p.in_stock]
        
        return products
    
    async def search_products(self, query: str) -> list[Product]:
        """Search products by name or description."""
        query_lower = query.lower()
        return [
            p
            for p in self.products.values()
            if query_lower in p.name.lower()
            or (p.description and query_lower in p.description.lower())
        ]
    
    # Order operations
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Fetch order by ID."""
        return self.orders.get(order_id)
    
    async def list_user_orders(self, user_id: int) -> list[Order]:
        """List all orders for a specific user."""
        return [o for o in self.orders.values() if o.user_id == user_id]
    
    async def create_order(
        self, user_id: int, product_id: int, quantity: int
    ) -> Optional[Order]:
        """Create a new order.
        
        Returns None if user or product doesn't exist, or product is out of stock.
        """
        user = await self.get_user(user_id)
        product = await self.get_product(product_id)
        
        if not user or not product or not product.in_stock:
            return None
        
        order = Order(
            id=self._next_order_id,
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
        )
        self.orders[order.id] = order
        self._next_order_id += 1
        return order
    
    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status. Returns True if successful."""
        order = await self.get_order(order_id)
        if order:
            order.status = status
            return True
        return False


# Global instance for simple examples
mock_db = MockDatabase()
