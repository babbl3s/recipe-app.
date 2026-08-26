"""
Renee's Table — web app (Streamlit). Self-contained: needs only streamlit + anthropic.
Set ANTHROPIC_API_KEY in Streamlit Secrets.
Tabs: Generate a recipe · Convert a recipe to gluten-free · My Cookbook.
"""
 
import os
import streamlit as st
 
# ---------------------------------------------------------------- AI
def _get_key():
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")
 
 
def ask_claude(prompt):
    """Send a prompt to Claude. Auto-continues so long answers never cut off."""
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
 
st.set_page_config(page_title="Renee's Table", page_icon="🍳", layout="centered")
st.title("🍳 Renee's Table")
st.caption("Gluten-free recipes, made for you.")
 
tab_gen, tab_convert, tab_book = st.tabs(["✨ Generate", "♻️ Make it Gluten-Free", "📖 My Cookbook"])
 
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
 
    restrictions = ["celiac (strictly gluten-free)"]
    if veg: restrictions.append("vegetarian")
    if dairy_free: restrictions.append("dairy-free")
    ing_text = ", ".join(chosen) if chosen else "cook's choice (a great gluten-free dish)"
 
    prompt = (
        f"Create ONE gluten-free, celiac-safe recipe using these ingredients: {ing_text}.\n"
        f"Dietary restrictions (strict): {', '.join(restrictions)}. "
        f"Difficulty: {experience}. Maximum spice on a 0-10 scale: {max_spice}.\n\n"
        "Structure the response with these labeled sections, in order:\n"
        "1. Title\n"
        "2. Description — two inviting sentences.\n"
        "3. Shopping List — grouped by store section (Produce, Meat & Seafood, Dairy, Pantry), "
        "with quantities; flag gluten-free items (e.g. 'gluten-free soy sauce').\n"
        "4. Ingredients — the measured amounts used.\n"
        "5. Directions — clear numbered steps with prep, temperatures, timing, and how to tell "
        "each step is done.\n"
        "6. Time & Servings.\n\n"
        "IMPORTANT: Keep the whole recipe COMPLETE — always finish every section, especially the "
        "full Directions. Aim for about 400–650 words. Everything must be gluten-free and celiac-safe."
    )
 
    if st.button("Generate my recipe 🍽️", type="primary"):
        with st.spinner("Writing your recipe..."):
            st.session_state["gen_result"] = ask_claude(prompt)
    if st.session_state.get("gen_result"):
        st.markdown("---")
        st.markdown(st.session_state["gen_result"])
 
# ============================ CONVERT ============================
with tab_convert:
    st.header("Make any recipe gluten-free")
    st.caption("Paste a recipe below and I'll rewrite it to be safe for celiac disease — keeping it as close to the original as possible.")
    user_recipe = st.text_area("Paste your recipe here", height=220,
                               placeholder="Paste the full recipe — ingredients and instructions.")
 
    if st.button("Convert to gluten-free ♻️", type="primary"):
        if not user_recipe.strip():
            st.info("Paste a recipe first, then tap convert.")
        else:
            convert_prompt = (
                "Convert the following recipe to be STRICTLY gluten-free and safe for someone with "
                "celiac disease. Keep it as close to the original as possible — change only what's "
                "necessary. For every swap, name the gluten-free substitute and, in parentheses, what "
                "it replaced (e.g. 'gluten-free tamari (instead of soy sauce)'). Call out hidden-gluten "
                "watch-outs (soy sauce, broth, oats, seasoning blends, imitation seafood) and remind the "
                "cook to check labels for 'certified gluten-free'.\n\n"
                "Return: a Title, an Ingredients list with quantities, numbered Instructions, and a short "
                "'Substitutions made' summary at the end.\n\n"
                f"RECIPE TO CONVERT:\n{user_recipe.strip()}"
            )
            with st.spinner("Converting your recipe..."):
                st.session_state["convert_result"] = ask_claude(convert_prompt)
    if st.session_state.get("convert_result"):
        st.markdown("---")
        st.markdown(st.session_state["convert_result"])
 
# ============================ COOKBOOK ============================
with tab_book:
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
