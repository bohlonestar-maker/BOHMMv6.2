# Store-related Pydantic models
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid


class ProductVariation(BaseModel):
    id: str
    name: str
    price: float
    square_variation_id: Optional[str] = None
    inventory_count: int = 0
    sold_out: bool = False


class StoreProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    square_catalog_id: Optional[str] = None
    inventory_count: int = 0
    is_active: bool = True
    member_price: Optional[float] = None
    variations: List[dict] = []
    has_variations: bool = False
    allows_customization: bool = False
    show_in_supporter_store: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StoreProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image_url: Optional[str] = None
    inventory_count: int = 0
    member_price: Optional[float] = None
    show_in_supporter_store: bool = True
    allows_customization: bool = False


class StoreProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    inventory_count: Optional[int] = None
    is_active: Optional[bool] = None
    member_price: Optional[float] = None
    show_in_supporter_store: Optional[bool] = None
    allows_customization: Optional[bool] = None


class CartItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int
    image_url: Optional[str] = None
    variation_id: Optional[str] = None
    variation_name: Optional[str] = None
    customization: Optional[str] = None


class ShoppingCart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[CartItem] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StoreOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    items: List[CartItem]
    subtotal: float
    tax: float = 0.0
    total: float
    status: str = "pending"
    square_order_id: Optional[str] = None
    square_payment_id: Optional[str] = None
    payment_method: str = "card"
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaymentRequest(BaseModel):
    source_id: str
    amount_cents: int
    order_id: str
    customer_email: Optional[str] = None


class StoreAdmin(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    granted_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StoreAdminCreate(BaseModel):
    username: str


class SupporterCheckoutRequest(BaseModel):
    items: list
    customer_email: str
    customer_name: str
    shipping_address: Optional[str] = None
