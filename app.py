from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

# File paths
JSON_DIR = "Json"
INGREDIENTS_FILE = os.path.join(JSON_DIR, "Ingredients.json")
SCHEMA_FILE = os.path.join(JSON_DIR, "Ingredient_Schema.json")

# Hardcoded password for security (later, move this to an environment variable)
ADMIN_PASSWORD = "Dabba!"

# Ensure JSON directory exists
os.makedirs(JSON_DIR, exist_ok=True)

#------------------ FUNCTIONS -----------------------------

# Load ingredients database
def load_database():
    if not os.path.exists(INGREDIENTS_FILE):
        return []
    with open(INGREDIENTS_FILE, "r") as f:
        return json.load(f)

# Save ingredients database
def save_database(data):
    with open(INGREDIENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load schema
def load_schema():
    with open(SCHEMA_FILE, "r") as f:
        return json.load(f)

# Validate ingredient against schema
def validate_ingredient(data):
    schema = load_schema()
    from jsonschema import validate, ValidationError
    try:
        validate(instance=data, schema=schema)
        return None
    except ValidationError as e:
        return str(e)
    
#--------------------- ENDPOINTS -----------------------------

@app.route("/")
@app.route("/index")
def home():
    return render_template("index.html")

@app.route("/ingredient-list")
def ingredient_list():
    return render_template("ingredient_list.html")

@app.route("/add")
def add_page():
    return render_template("add_ingredient.html")

@app.route("/ingredients", methods=["GET"])
def get_all_ingredients():
    """Retrieve all ingredients."""
    return jsonify(load_database())

@app.route("/ingredients/<id>", methods=["GET"])
def get_ingredient(id):
    """Retrieve a single ingredient by ID."""
    ingredients = load_database()
    ingredient = next((ing for ing in ingredients if ing["id"] == id), None)
    return jsonify(ingredient) if ingredient else ("Ingredient not found", 404)

@app.route("/ingredients", methods=["POST"])
def add_ingredient():
    """Add a new ingredient."""
    ingredients = load_database()
    new_ingredient = request.json

    # Validate ingredient
    validation_error = validate_ingredient(new_ingredient)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    # Check if ID already exists
    if any(ing["id"] == new_ingredient["id"] for ing in ingredients):
        return jsonify({"error": "Ingredient with this ID already exists"}), 400

    ingredients.append(new_ingredient)
    save_database(ingredients)
    return jsonify(new_ingredient), 201

@app.route("/ingredients/<id>", methods=["PUT"])
def update_ingredient(id):
    """Update an existing ingredient (requires password)."""
    if request.headers.get("Authorization") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403

    ingredients = load_database()
    updated_ingredient = request.json

    # Validate ingredient
    validation_error = validate_ingredient(updated_ingredient)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    for i, ingredient in enumerate(ingredients):
        if ingredient["id"] == id:
            ingredients[i] = updated_ingredient
            save_database(ingredients)
            return jsonify(updated_ingredient)

    return jsonify({"error": "Ingredient not found"}), 404

@app.route("/ingredients/<id>", methods=["DELETE"])
def delete_ingredient(id):
    """Delete an ingredient (requires password)."""
    if request.headers.get("Authorization") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 403

    ingredients = load_database()
    ingredients = [ing for ing in ingredients if ing["id"] != id]

    save_database(ingredients)
    return jsonify({"message": "Ingredient deleted"}), 200

@app.route("/ingredients/search", methods=["GET"])
def search_ingredients():
    """Search for ingredients by name, category, or other fields."""
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    ingredients = load_database()
    results = [ing for ing in ingredients if query in ing["name"].lower() or query in ing["category"].lower()]
    
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
