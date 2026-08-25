"""
Renee's Table — web app (Streamlit). Self-contained: needs only streamlit + anthropic.
Set ANTHROPIC_API_KEY in Streamlit Secrets.
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
 
 
def generate_recipe(prompt):
    key = _get_key()
    if not key:
        return "_Add ANTHROPIC_API_KEY in Secrets to generate real recipes._"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        model = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
        messages = [{"role": "user", "content": prompt}]
        full = ""
        # Auto-continue if a recipe is ever too long for one response, so it
        # can never get cut off. Up to 4 passes is far more than any recipe needs.
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
 
tab_gen, tab_book = st.tabs(["✨ Generate", "📖 My Cookbook"])
 
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
        "IMPORTANT: Keep the whole recipe COMPLETE and self-contained — always finish every "
        "section, especially the full Directions. Aim for about 400–650 words total so nothing "
        "gets cut off. Do not pad or over-explain. Everything must be gluten-free and safe for "
        "someone with celiac disease."
    )
 
    if st.button("Generate my recipe 🍽️", type="primary"):
        with st.spinner("Writing your recipe..."):
            recipe = generate_recipe(prompt)
        st.markdown("---")
        st.markdown(recipe)
 
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
