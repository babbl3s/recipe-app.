"""
Renee's Table — web app (Streamlit) with tiers.
 
Free plan: no login. Paid plans (Basic / Full / Unlimited): sign in with email,
subscribe through Stripe, and your perks unlock.
 
Files needed in the repo: recipe_app.py, tiers.py, billing.py, requirements.txt,
.streamlit/config.toml
Secrets: ANTHROPIC_API_KEY (required), plus STRIPE_SECRET_KEY + APP_URL for payments.
"""
 
import os
import io
import base64
import streamlit as st
 
import billing
from tiers import TIERS, TIER_ORDER, info
 
# ---------------------------------------------------------------- AI
def _get_key():
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")
 
 
def ask_claude(prompt):
    key = _get_key()
    if not key:
        return "_Add ANTHROPIC_API_KEY in Secrets to generate real recipes._"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
        messages = [{"role": "user", "content": prompt}]
        full = ""
        for _ in range(4):
            msg = client.messages.create(model=model, max_tokens=4096, messages=messages)
            chunk = "".join(b.text for b in msg.content if b.type == "text")
            full += chunk
            if msg.stop_reason != "max_tokens":
                break
            messages.append({"role": "assistant", "content": chunk})
            messages.append({"role": "user", "content": "Continue exactly where you left off, without repeating anything."})
        return full
    except Exception as e:
        return f"_Recipe request failed: {e}_"
 
 
CONVERT_INSTRUCTION = (
    "Convert this recipe to be STRICTLY gluten-free and safe for someone with celiac disease. "
    "Keep it as close to the original as possible — change only what's necessary. For every swap, "
    "name the gluten-free substitute and, in parentheses, what it replaced (e.g. 'gluten-free tamari "
    "(instead of soy sauce)'). Call out hidden-gluten watch-outs (soy sauce, broth, oats, seasoning "
    "blends, imitation seafood) and remind the cook to check labels for 'certified gluten-free'. "
    "Return: a Title, an Ingredients list with quantities, numbered Instructions, and a short "
    "'Substitutions made' summary at the end. If you can't find a recipe in what's provided, say so briefly."
)
 
 
def _read_docx(data):
    try:
        import docx
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    except Exception:
        return ""
 
 
def build_convert_content(pasted, upload):
    """Return message content for Claude from pasted text OR an uploaded photo/file."""
    if upload is not None:
        data = upload.getvalue()
        name = (upload.name or "").lower()
        mtype = upload.type or ""
        # Image → Claude reads it directly (vision)
        if mtype.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            media = mtype if mtype.startswith("image/") else "image/jpeg"
            b64 = base64.standard_b64encode(data).decode()
            return [
                {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
                {"type": "text", "text": CONVERT_INSTRUCTION + " The recipe is in the attached image."},
            ]
        # PDF → Claude reads it directly
        if mtype == "application/pdf" or name.endswith(".pdf"):
            b64 = base64.standard_b64encode(data).decode()
            return [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
                {"type": "text", "text": CONVERT_INSTRUCTION + " The recipe is in the attached PDF."},
            ]
        # Word doc → extract text
        if name.endswith(".docx"):
            text = _read_docx(data)
            if not text.strip():
                return CONVERT_INSTRUCTION + "\n\n(The .docx couldn't be read — ask the user to paste the text.)"
            return CONVERT_INSTRUCTION + "\n\nRECIPE:\n" + text
        # Plain text
        text = data.decode("utf-8", errors="ignore")
        return CONVERT_INSTRUCTION + "\n\nRECIPE:\n" + text
    # Pasted text
    return CONVERT_INSTRUCTION + "\n\nRECIPE:\n" + pasted.strip()
 
 
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
 
MY_RECIPES = [
    {"title": "Grandma's Gluten-Free Cornbread",
     "description": "Golden, slightly sweet, and completely gluten-free — a family favorite.",
     "ingredients": ["1 cup cornmeal", "1 cup gluten-free flour", "1 tbsp baking powder",
        "1/4 cup sugar", "1/2 tsp salt", "1 cup milk", "2 eggs", "1/3 cup melted butter"],
     "steps": ["Preheat oven to 400°F and grease an 8-inch pan.",
        "Whisk cornmeal, gluten-free flour, baking powder, sugar, and salt.",
        "Mix milk, eggs, and melted butter, then combine with the dry ingredients.",
        "Pour into the pan and bake 20–25 minutes until golden."]},
    {"title": "Weeknight Tenderloin & Potatoes",
     "description": "Seared tenderloin with crispy roasted potatoes, all gluten-free.",
     "ingredients": ["2 beef tenderloin steaks", "1 lb baby potatoes, halved",
        "2 tbsp olive oil", "1 tsp paprika", "Salt and pepper"],
     "steps": ["Roast potatoes with oil, paprika, and salt at 425°F for 30 minutes.",
        "Season the steaks well with salt and pepper.",
        "Sear 3 minutes per side in a hot pan, then rest 5 minutes.",
        "Serve the steaks alongside the potatoes."]},
]
 
# ---------------------------------------------------------------- plan state
st.set_page_config(page_title="Renee's Table", page_icon="🍳", layout="centered")
 
email = st.session_state.get("email")          # None = anonymous Free user
if email:
    if "tier" not in st.session_state:
        st.session_state["tier"] = billing.tier_for_email(email)
    tier_key = st.session_state["tier"]
else:
    tier_key = "free"
t = info(tier_key)
 
# usage this week
if email:
    used = billing.get_usage(email)
else:
    used = st.session_state.get("free_used", 0)
limit = t["recipes_per_week"]
remaining = float("inf") if limit == float("inf") else max(0, limit - used)
 
 
def record_use():
    if email:
        billing.record_generation(email)
    else:
        st.session_state["free_used"] = st.session_state.get("free_used", 0) + 1
 
 
def out_of_recipes():
    return remaining != float("inf") and remaining <= 0
 
 
def show_ad():
    if t["ads"]:
        st.info("🟩 Ad space — set up Google AdSense before launch (hidden for Full & Unlimited).")
 
 
# ---------------------------------------------------------------- header
st.title("🍳 Renee's Table")
rem_label = "Unlimited recipes" if remaining == float("inf") else f"{int(remaining)} left this week"
who = f"Signed in · {t['name']} plan" if email else f"Free plan (no account needed)"
st.caption(f"{who} · {rem_label}")
 
tab_gen, tab_convert, tab_book, tab_plan = st.tabs(
    ["✨ Generate", "♻️ Make it Gluten-Free", "📖 My Cookbook", "💚 Plan"]
)
 
# ============================ GENERATE ============================
with tab_gen:
    st.header("What's in your kitchen?")
    chosen = []
    for cat, items in INGREDIENTS.items():
        chosen += st.multiselect(cat, items, key=f"ms_{cat}")
 
    c1, c2 = st.columns(2)
    experience = c1.selectbox("Experience level", ["beginner", "intermediate", "expert"], index=1)
    max_spice = c2.slider("Max spice (0–10)", 0, 10, 6)
    veg = c1.checkbox("Vegetarian")
    dairy_free = c2.checkbox("Dairy-free")
 
    show_ad()
 
    restrictions = ["celiac (strictly gluten-free)"]
    if veg: restrictions.append("vegetarian")
    if dairy_free: restrictions.append("dairy-free")
    ing_text = ", ".join(chosen) if chosen else "cook's choice (a great gluten-free dish)"
 
    prompt = (
        f"Create ONE gluten-free, celiac-safe recipe using these ingredients: {ing_text}.\n"
        f"Dietary restrictions (strict): {', '.join(restrictions)}. "
        f"Difficulty: {experience}. Maximum spice on a 0-10 scale: {max_spice}.\n\n"
        "Structure the response with these labeled sections, in order:\n"
        "1. Title\n2. Description — two inviting sentences.\n"
        "3. Shopping List — grouped by store section (Produce, Meat & Seafood, Dairy, Pantry), "
        "with quantities; flag gluten-free items.\n"
        "4. Ingredients — the measured amounts used.\n"
        "5. Directions — clear numbered steps with prep, temperatures, timing, and doneness cues.\n"
        "6. Time & Servings.\n\n"
        "IMPORTANT: Keep the whole recipe COMPLETE — finish every section. Aim for ~400–650 words. "
        "Everything must be gluten-free and celiac-safe."
    )
 
    if out_of_recipes():
        st.warning("You're out of recipes this week. Open the 💚 Plan tab to upgrade for more.")
    elif st.button("Generate my recipe 🍽️", type="primary"):
        with st.spinner("Writing your recipe..."):
            st.session_state["gen_result"] = ask_claude(prompt)
            record_use()
        st.rerun()
    if st.session_state.get("gen_result"):
        st.markdown("---")
        st.markdown(st.session_state["gen_result"])
 
# ============================ CONVERT ============================
with tab_convert:
    st.header("Make any recipe gluten-free")
    st.caption("Three ways to give me a recipe — paste it, snap a photo, or upload a file. "
               "I'll rewrite it to be celiac-safe, keeping it as close to the original as possible.")
 
    user_recipe = st.text_area("① Paste your recipe here", height=180,
                               placeholder="Paste the full recipe — ingredients and instructions.")
    upload = st.file_uploader("② …or upload a photo of a recipe, or a file (PDF, Word, or text)",
                              type=["png", "jpg", "jpeg", "webp", "gif", "pdf", "txt", "md", "docx"])
    if upload is not None:
        if (upload.type or "").startswith("image/"):
            st.image(upload, caption="Your recipe photo", width=280)
        else:
            st.success(f"Attached: {upload.name}")
    show_ad()
 
    if out_of_recipes():
        st.warning("You're out of recipes this week. Open the 💚 Plan tab to upgrade for more.")
    elif st.button("Convert to gluten-free ♻️", type="primary"):
        if not user_recipe.strip() and upload is None:
            st.info("Paste a recipe, snap a photo, or upload a file first.")
        else:
            content = build_convert_content(user_recipe, upload)
            with st.spinner("Reading and converting your recipe..."):
                st.session_state["convert_result"] = ask_claude(content)
                record_use()
            st.rerun()
    if st.session_state.get("convert_result"):
        st.markdown("---")
        st.markdown(st.session_state["convert_result"])
 
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
    st.header("Your plan")
    if email:
        cols = st.columns([3, 1])
        cols[0].markdown(f"Signed in as **{email}** — **{t['name']}** plan.")
        if cols[1].button("Sign out"):
            for k in ("email", "tier"):
                st.session_state.pop(k, None)
            st.rerun()
    else:
        st.markdown("You're on the **Free** plan — no account needed. Sign in to subscribe or reach a paid plan.")
        e = st.text_input("Your email", placeholder="you@example.com", key="signin_email")
        if st.button("Sign in"):
            if e and "@" in e:
                st.session_state["email"] = e.strip().lower()
                st.session_state.pop("tier", None)
                st.rerun()
            else:
                st.warning("Please enter a valid email.")
 
    if not billing.available():
        st.info("Preview: add STRIPE_SECRET_KEY in Secrets and your price IDs in tiers.py to turn on subscriptions.")
 
    for key in TIER_ORDER:
        if key == "free":
            continue
        ti = TIERS[key]
        with st.container(border=True):
            st.subheader(f"{ti['name']} — {ti['price_label']}")
            cap = "Unlimited" if ti["recipes_per_week"] == float("inf") else ti["recipes_per_week"]
            st.write(f"• {cap} recipes / week  \n"
                     f"• {'Cookbook included' if ti['cookbook'] else 'No cookbook'}  \n"
                     f"• {'No ads' if not ti['ads'] else 'Some ads'}")
            if email and tier_key == key:
                st.success("Current plan")
            elif email:
                url = billing.checkout_url(key, email)
                if url:
                    st.link_button(f"Subscribe — {ti['price_label']}", url, type="primary")
                else:
                    st.button(f"Subscribe — {ti['price_label']}", key=f"sub_{key}", disabled=True,
                              help="Set your Stripe key + price IDs to enable.")
            else:
                st.caption("↑ Sign in above to subscribe.")
 
    if email:
        st.divider()
        c = st.columns(2)
        portal = billing.portal_url(email)
        if portal:
            c[0].link_button("Manage subscription", portal)
        if c[1].button("Refresh my plan"):
            st.session_state["tier"] = billing.tier_for_email(email)
            st.rerun()
        st.caption("Billed monthly through Stripe; cancel anytime from Manage subscription.")
