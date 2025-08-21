from datetime import datetime
from typing import List, Optional

from pipelex.core.stuffs.stuff_content import StructuredContent


class Products(StructuredContent):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None


class ProofOfPurchase(StructuredContent):
    date_of_purchase: Optional[datetime] = None
    amount_paid: Optional[float] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    purchase_number: Optional[str] = None
    products: Optional[List[Products]] = None
