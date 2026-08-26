
"""
tiers.py — the four membership tiers and what each unlocks.
 
After you create the products in Stripe (test mode), paste each one's PRICE ID
(looks like "price_1Abc...") into `price_id` below. Find it in Stripe:
Product catalog → open the product → copy the API ID under its price.
"""
 
TIERS = {
    "free": {
        "key": "free", "name": "Free", "price_label": "$0",
        "recipes_per_week": 1, "cookbook": False, "ads": True,
        "price_id": None,
    },
    "basic": {
        "key": "basic", "name": "Basic", "price_label": "$4.99/mo",
        "recipes_per_week": 5, "cookbook": False, "ads": True,
        "price_id": "REPLACE_WITH_BASIC_PRICE_ID",
    },
    "full": {
        "key": "full", "name": "Full", "price_label": "$9.99/mo",
        "recipes_per_week": 20, "cookbook": True, "ads": False,
        "price_id": "REPLACE_WITH_FULL_PRICE_ID",
    },
    "unlimited": {
        "key": "unlimited", "name": "Unlimited", "price_label": "$14.99/mo",
        "recipes_per_week": float("inf"), "cookbook": True, "ads": False,
        "price_id": "REPLACE_WITH_UNLIMITED_PRICE_ID",
    },
}
 
TIER_ORDER = ["free", "basic", "full", "unlimited"]
 
# price_id -> tier key (built from the table above)
PRICE_TO_TIER = {
    t["price_id"]: t["key"] for t in TIERS.values() if t.get("price_id")
}
 
def info(key):
    return TIERS.get(key, TIERS["free"])
