"""
Renee's Table — web app (Streamlit) with paid tiers via Stripe.
 
Secrets you set in Streamlit (⋮ → Settings → Secrets):
    ANTHROPIC_API_KEY = "sk-ant-..."
    STRIPE_SECRET_KEY = "sk_test_..."      # test key while building
    APP_URL = "https://your-app.streamlit.app"
 
People sign in with their email, subscribe through Stripe's hosted checkout, and
the app unlocks their tier. (Email sign-in is a simple first version; a stronger
login can be added later.)
"""
 
import os
import streamlit as st
 
import billing
from tiers import TIERS, TIER_ORDER, info
from my_recipes import MY_RECIPES
 
# ------------------------------------------------------------ AI generation
def generate_recipe(prompt):
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return "_Add ANTHROPIC_API_KEY in Secrets to generate real recipes._"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if b.type == "text")
    except Exception as e:
        return f"_Recipe request failed: {e}_"
 
 
INGREDIENTS = {
    "🥩 Meats & proteins": ["Beef tenderloin", "Steak", "Ground beef", "Chicken breast",
        "Chicken thighs", "Pork chops", "Bacon", "Turkey", "Salmon", "Shrimp", "Tuna", "Eggs", "Tofu"],
    "🥦 Vegetables": ["Potatoes", "Sweet potatoes", "Onion", "Garlic", "Bell pepper", "Broccoli",
        "Cauliflower", "Carrots", "Spinach", "Zucchini", "Mushrooms", "Tomatoes", "Green beans", "Kale"],
    "🍎 Fruits": ["Apple", "Banana", "Lemon", "Lime", "Orange", "Strawberries", "Blueberries",
        "Avocado", "Pineapple", "Mango", "Peaches"],
    "🧀 Dairy": ["Milk", "Butter", "Cheddar", "Mozzarella", "Parmesan", "Cream", "Sour cream", "Yogurt", "Feta"],
    "🌾 Gluten-free pantry": ["Gluten-free flour", "Marinara", "Rice", "Gluten-free pasta",
        "Quinoa", "Black beans", "Chickpeas", "Olive oil"],
}
 
st.set_page_config(page_title="Renee's Table", page_icon="🍳", layout="centered")
 
 
# ------------------------------------------------------------ sign-in gate
def sign_in():
    st.title("🍳 Renee's Table")
    st.caption("Gluten-free recipes, made for you.")
    st.write("Enter your email to start. If you've subscribed, this unlocks your plan.")
    email = st.text_input("Email", placeholder="you@example.com")
    if st.button("Continue", type="primary") and email and "@" in email:
        st.session_state["email"] = email.strip().lower()
        st.session_state.pop("tier", None)
        st.rerun()
 
if "email" not in st.session_state:
    sign_in()
    st.stop()
 
email = st.session_state["email"]
 
# resolve tier once per session (Refresh button re-checks)
if "tier" not in st.session_state:
    st.session_state["tier"] = billing.tier_for_email(email)
tier_key = st.session_state["tier"]
t = info(tier_key)
 
used = billing.get_usage(email)
remaining = float("inf") if t["recipes_per_week"] == float("inf") else max(0, t["recipes_per_week"] - used)
remaining_label = "Unlimited recipes" if remaining == float("inf") else f"{int(remaining)} recipe(s) left this week"
 
# ------------------------------------------------------------ header
top = st.columns([3, 1])
with top[0]:
    st.markdown(f"**{email}** · {t['name']} plan · {remaining_label}")
with top[1]:
    if st.button("Sign out"):
        for k in ("email", "tier"):
            st.session_state.pop(k, None)
        st.rerun()
 
tab_gen, tab_book, tab_plan = st.tabs(["✨ Generate", "📖 My Cookbook", "💚 Plan"])
 
# ============================ GENERATE ============================
with tab_gen:
    st.header("What's in your kitchen?")
    chosen = []
    for cat, items in INGREDIENTS.items():
        chosen += st.multiselect(cat, items, key=f"ms_{cat}")
 
    c1, c2 = st.columns(2)
    experience = c1.selectbox("Experience level", ["beginner", "intermediate", "expert"], index=2)
    max_spice = c2.slider("Max spice (0–10)", 0, 10, 6)
    veg = c1.checkbox("Vegetarian")
    dairy_free = c2.checkbox("Dairy-free")
 
    if t["ads"]:
        st.info("🟩 Ad space — wire up Google AdSense before launch (hidden for Full/Unlimited).")
 
    restrictions = ["celiac (strictly gluten-free)"]
    if veg: restrictions.append("vegetarian")
    if dairy_free: restrictions.append("dairy-free")
    ing_text = ", ".join(chosen) if chosen else "cook's choice (a great gluten-free dish)"
    prompt = (
        f"Please create ONE gluten-free, celiac-safe recipe that includes these ingredients: {ing_text}.\n"
        f"Dietary restrictions (strict): {', '.join(restrictions)}.\n"
        f"Difficulty: {experience}. Maximum spice on a 0-10 scale: {max_spice}.\n\n"
        "Write the response with these clearly labeled sections, in this order:\n"
        "1. Recipe title.\n"
        "2. Description — two inviting sentences.\n"
        "3. Shopping List — everything the cook needs to buy, with exact quantities, grouped "
        "by store section (Produce, Meat & Seafood, Dairy, Pantry). Flag gluten-free items "
        "explicitly (for example, 'gluten-free soy sauce').\n"
        "4. Ingredients — the measured amounts used in the recipe.\n"
        "5. Instructions — detailed, numbered steps a beginner could follow. For each step give "
        "specifics: prep work, exact heat or oven temperature, the pan or dish to use, timing, "
        "and what to look, smell, or feel for to know it's done. Be thorough and reassuring "
        "rather than brief.\n"
        "6. Time & Servings — prep time, cook time, and how many it serves.\n\n"
        "Every ingredient and product must be gluten-free and safe for someone with celiac disease."
    )
 
    if remaining <= 0:
        st.warning("You're out of recipes for this week. Upgrade in the 💚 Plan tab for more.")
    elif st.button("Generate my recipe 🍽️", type="primary"):
        with st.spinner("Writing your recipe..."):
            recipe = generate_recipe(prompt)
            billing.record_generation(email)
        st.markdown("---")
        st.markdown(recipe)
        st.caption("Refresh the page to update your remaining count.")
 
# ============================ COOKBOOK ============================
with tab_book:
    if not t["cookbook"]:
        st.subheader("🔒 Cookbook is a Full perk")
        st.write("Upgrade to **Full** or **Unlimited** in the 💚 Plan tab to unlock your cookbook.")
    else:
        st.header("Your cookbook")
        q = st.text_input("Search", placeholder="Recipe name or ingredient")
        for r in MY_RECIPES:
            hay = (r["title"] + " " + r["description"] + " " + " ".join(r["ingredients"])).lower()
            if q.strip() and q.strip().lower() not in hay:
                continue
            with st.expander(f"📖 {r['title']}"):
                st.write(r["description"])
                st.markdown("**Ingredients**")
                for i in r["ingredients"]:
                    st.markdown(f"- {i}")
                st.markdown("**Method**")
                for n, s in enumerate(r["steps"], 1):
                    st.markdown(f"{n}. {s}")
 
# ============================ PLAN ============================
with tab_plan:
    st.header("Your membership")
    st.write(f"You're on the **{t['name']}** plan.")
 
    if not billing.available():
        st.info("Preview: add STRIPE_SECRET_KEY in Secrets and your price IDs in tiers.py to turn on subscriptions.")
 
    for key in TIER_ORDER:
        if key == "free":
            continue
        ti = TIERS[key]
        with st.container(border=True):
            st.subheader(f"{ti['name']} — {ti['price_label']}")
            cap = "Unlimited" if ti["recipes_per_week"] == float("inf") else ti["recipes_per_week"]
            st.write(f"• {cap} recipes / week  \n• {'Cookbook included' if ti['cookbook'] else 'No cookbook'}  \n• {'No ads' if not ti['ads'] else 'Some ads'}")
            if tier_key == key:
                st.success("Current plan")
            else:
                url = billing.checkout_url(key, email)
                if url:
                    st.link_button(f"Subscribe — {ti['price_label']}", url, type="primary")
                else:
                    st.button(f"Subscribe — {ti['price_label']}", disabled=True,
                              help="Set your Stripe key + price IDs to enable.")
 
    st.divider()
    cols = st.columns(2)
    portal = billing.portal_url(email)
    if portal:
        cols[0].link_button("Manage subscription", portal)
    if cols[1].button("Refresh my plan"):
        st.session_state["tier"] = billing.tier_for_email(email)
        st.rerun()
 
    st.caption("Billed monthly through Stripe; cancel anytime from Manage subscription.")
