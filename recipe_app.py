"""
Renee's Table — live-AI gluten-free recipe generator (Streamlit web app)
Two tabs: AI generator + your own cookbook (my_recipes.py).
"""

import os
import streamlit as st

def _secret(name):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def generate_recipe(prompt):
    anthropic_key = _secret("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model=os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
                max_tokens=900,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(b.text for b in msg.content if b.type == "text")
        except Exception as err:
            return f"_Claude request failed: {err}_\n\n" + _sample()

    openai_key = _secret("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            out = client.chat.completions.create(
                model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are a helpful gluten-free cooking assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return out.choices[0].message.content
        except Exception as err:
            return f"_OpenAI request failed: {err}_\n\n" + _sample()

    return _sample()


def _sample():
    return (
        "**No AI key set yet — showing a sample.** Add `ANTHROPIC_API_KEY` "
        "(or `OPENAI_API_KEY`) in the app's Secrets to generate real recipes.\n\n"
        "### Seared Tenderloin over Garlic Mashed Potatoes\n"
        "A tender, gluten-free centerpiece. Season tenderloin with salt, pepper, "
        "and paprika; sear 3 min per side and rest. Boil potatoes, mash with butter, "
        "milk, and roasted garlic. Slice the beef over the potatoes and finish with "
        "fresh herbs."
    )


try:
    from my_recipes import MY_RECIPES
except Exception:
    MY_RECIPES = []


INGREDIENTS = {
    "🥩 Meats & proteins": [
        "Beef tenderloin", "Steak", "Ground beef", "Chicken breast", "Chicken thighs",
        "Pork chops", "Bacon", "Ham", "Turkey", "Lamb", "Sausage (gluten-free)",
        "Salmon", "Shrimp", "Tuna", "Cod", "Eggs", "Tofu",
    ],
    "🥦 Vegetables": [
        "Potatoes", "Sweet potatoes", "Onion", "Garlic", "Bell pepper", "Broccoli",
        "Cauliflower", "Carrots", "Spinach", "Zucchini", "Mushrooms", "Tomatoes",
        "Green beans", "Corn", "Peas", "Asparagus", "Kale", "Cabbage", "Lettuce",
    ],
    "🍎 Fruits": [
        "Apple", "Banana", "Lemon", "Lime", "Orange", "Strawberries", "Blueberries",
        "Avocado", "Pineapple", "Mango", "Grapes", "Peaches", "Raspberries",
    ],
    "🧀 Dairy": [
        "Milk", "Butter", "Cheddar", "Mozzarella", "Parmesan", "Cream", "Sour cream",
        "Yogurt", "Cream cheese", "Feta", "Ricotta",
    ],
    "🌾 Gluten-free pantry": [
        "Gluten-free flour", "Marinara", "Rice", "Gluten-free pasta", "Quinoa",
        "Black beans", "Chickpeas", "Olive oil", "Gluten-free breadcrumbs",
    ],
}

st.set_page_config(page_title="Renee's Table", page_icon="🍳", layout="centered")
st.title("🍳 Renee's Table")

tab_generate, tab_cookbook = st.tabs(["✨ Generate a recipe", "📖 My Cookbook"])

with tab_generate:
    st.caption("Pick any ingredients you like — the AI writes you a gluten-free recipe.")
    st.subheader("What's in your kitchen?")
    chosen = []
    for category, items in INGREDIENTS.items():
        picked = st.multiselect(category, items, key=category)
        chosen.extend(picked)

    custom = st.text_input(
        "Anything else? (type extra ingredients, comma-separated)",
        placeholder="e.g. basil, coconut milk, pine nuts",
    )
    if custom.strip():
        chosen.extend([c.strip() for c in custom.split(",") if c.strip()])

    st.subheader("Preferences")
    col1, col2 = st.columns(2)
    with col1:
        experience_level = st.selectbox("Experience level", ["beginner", "intermediate", "expert"], index=2)
    with col2:
        max_spice = st.slider("Max spice (0–10)", 0, 10, 6)

    c3, c4 = st.columns(2)
    with c3:
        vegetarian = st.checkbox("Vegetarian", value=False)
    with c4:
        dairy_free = st.checkbox("Dairy-free", value=False)

    extra_notes = st.text_input("Any special requests? (optional)", placeholder="e.g. quick weeknight dinner, one pan, kid-friendly")

    restrictions = ["celiac (must be strictly gluten-free)"]
    if vegetarian:
        restrictions.append("vegetarian")
    if dairy_free:
        restrictions.append("dairy-free")

    ingredient_text = ", ".join(chosen) if chosen else "cook's choice (suggest a great gluten-free dish)"

    prompt = f"""Please create ONE recipe that tries to include these ingredients:
{ingredient_text}.

Requirements:
- Dietary restrictions (strict): {", ".join(restrictions)}.
- Difficulty level: {experience_level}.
- Maximum spice level on a scale of 0-10: {max_spice}.
{("- Extra request: " + extra_notes) if extra_notes.strip() else ""}

Format your answer as:
1. A recipe title (as a markdown heading).
2. A two-sentence description.
3. An "Ingredients" list with quantities.
4. A numbered "Instructions" list.
Make sure every ingredient and product is gluten-free and safe for celiac disease."""

    if st.button("Generate my recipe 🍽️", type="primary"):
        if not chosen:
            st.info("Tip: pick a few ingredients above for a more tailored recipe — or just hit generate for a surprise.")
        with st.spinner("Writing your recipe..."):
            recipe = generate_recipe(prompt)
        st.markdown("---")
        st.markdown(recipe)

    with st.expander("See the exact prompt sent to the AI"):
        st.code(prompt)

with tab_cookbook:
    st.caption("Your own recipes. Add more by editing my_recipes.py in GitHub.")
    if not MY_RECIPES:
        st.info("Your cookbook is empty. Add recipes to my_recipes.py in your GitHub repo and they'll show up here.")
    else:
        search = st.text_input("Search your cookbook", placeholder="Type a recipe name or ingredient")
        shown = 0
        for r in MY_RECIPES:
            haystack = (r.get("title", "") + " " + r.get("description", "") + " " +
                        " ".join(r.get("ingredients", []))).lower()
            if search.strip() and search.strip().lower() not in haystack:
                continue
            shown += 1
            with st.expander(f"📖  {r.get('title', 'Untitled')}", expanded=False):
                if r.get("description"):
                    st.write(r["description"])
                if r.get("ingredients"):
                    st.markdown("**Ingredients**")
                    for ing in r["ingredients"]:
                        st.markdown(f"- {ing}")
                if r.get("steps"):
                    st.markdown("**Instructions**")
                    for i, step in enumerate(r["steps"], 1):
                        st.markdown(f"{i}. {step}")
        if search.strip() and shown == 0:
            st.warning("No recipes matched that search.")
        st.caption(f"{len(MY_RECIPES)} recipe(s) in your cookbook.")

st.caption("Every AI recipe is generated gluten-free / celiac-safe. Add to Home Screen: "
           "iPhone → Share → Add to Home Screen · Android → ⋮ → Add to Home screen.")
