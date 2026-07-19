import bson
from enum import Enum

class PaymentMethod(str, Enum):
    COD = "COD"

doc = {"method": PaymentMethod.COD}
try:
    print(bson.encode(doc))
except Exception as e:
    print("BSON Error:", repr(e))
