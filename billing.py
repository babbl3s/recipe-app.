"""billing.py — all Stripe logic in one place."""

import datetime
import streamlit as st

try:
    import stripe
except Exception:
    stripe = None

from tiers import PRICE_TO_TIER, info


def _key():
    try:
        return st.secrets.get("STRIPE_SECRET_KEY")
    except Exception:
        return None


def available():
    return stripe is not None and bool(_key())


def _init():
    if not available():
        return False
    stripe.api_key = _key()
    return True


def _app_url():
    try:
        return st.secrets.get("APP_URL", "https://your-app.streamlit.app")
    except Exception:
        return "https://your-app.streamlit.app"


def _week_start():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    return monday.isoformat()


def get_or_create_customer(email):
    if not _init():
        return None
    existing = stripe.Customer.list(email=email, limit=1).data
    if existing:
        return existing[0]
    return stripe.Customer.create(email=email)


def tier_for_email(email):
    if not _init():
        return "free"
    try:
        customers = stripe.Customer.list(email=email, limit=1).data
        if not customers:
            return "free"
        subs = stripe.Subscription.list(customer=customers[0].id, status="active", limit=10).data
        best = "free"
        rank = {"free": 0, "basic": 1, "full": 2, "unlimited": 3}
        for sub in subs:
            for item in sub["items"]["data"]:
                t = PRICE_TO_TIER.get(item["price"]["id"])
                if t and rank.get(t, 0) > rank.get(best, 0):
                    best = t
        return best
    except Exception:
        return "free"


def get_usage(email):
    if not _init():
        return 0
    try:
        cust = get_or_create_customer(email)
        md = cust.get("metadata", {}) or {}
        if md.get("week_start") != _week_start():
            return 0
        return int(md.get("recipe_count", 0))
    except Exception:
        return 0


def record_generation(email):
    if not _init():
        return
    try:
        cust = get_or_create_customer(email)
        md = cust.get("metadata", {}) or {}
        count = int(md.get("recipe_count", 0)) if md.get("week_start") == _week_start() else 0
        stripe.Customer.modify(
            cust.id,
            metadata={"week_start": _week_start(), "recipe_count": count + 1},
        )
    except Exception:
        pass


def checkout_url(tier_key, email):
    if not _init():
        return None
    price_id = info(tier_key).get("price_id")
    if not price_id or price_id.startswith("REPLACE_"):
        return None
    try:
        cust = get_or_create_customer(email)
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=cust.id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=_app_url(),
            cancel_url=_app_url(),
        )
        return session.url
    except Exception:
        return None


def portal_url(email):
    if not _init():
        return None
    try:
        cust = get_or_create_customer(email)
        session = stripe.billing_portal.Session.create(customer=cust.id, return_url=_app_url())
        return session.url
    except Exception:
        return None
