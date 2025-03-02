import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import jsonschema

# File paths
JSON_FOLDER = "Json"
INGREDIENTS_FILE = os.path.join(JSON_FOLDER, "Ingredients.json")
SCHEMA_FILE = os.path.join(JSON_FOLDER, "Ingredient_Schema.json")

def ensure_files_exist():
    """Ensure the Json folder, ingredients file, and schema file exist."""
    if not os.path.exists(JSON_FOLDER):
        os.makedirs(JSON_FOLDER)
    # Create Ingredients.json if it doesn't exist (initialize as an empty list)
    if not os.path.exists(INGREDIENTS_FILE):
        with open(INGREDIENTS_FILE, "w") as f:
            json.dump([], f, indent=4)
    # It is assumed that Ingredient_Schema.json is provided in the folder.

def load_data():
    """Load the current list of ingredients."""
    try:
        with open(INGREDIENTS_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        data = []
    return data

def load_schema():
    """Load the ingredient JSON schema."""
    with open(SCHEMA_FILE, "r") as f:
        schema = json.load(f)
    return schema

def save_data(data):
    """Save the updated ingredients list to the file."""
    with open(INGREDIENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_array(text):
    """Helper to split a comma-separated string into a list."""
    return [item.strip() for item in text.split(",") if item.strip()]

def get_dropdown_values(key_path):
    """
    Retrieve unique values from the loaded ingredients data.
    key_path can be 'source', 'category', or 'size.unit' for nested keys.
    """
    values = set()
    for ingredient in ingredients_data:
        try:
            keys = key_path.split('.')
            val = ingredient
            for key in keys:
                val = val[key]
            if isinstance(val, str) and val.strip():
                values.add(val.strip())
        except KeyError:
            continue
    return sorted(list(values), key=str.lower)

def add_new_dropdown_value(combobox, category):
    """Allow the user to add a new value to a dropdown list."""
    prompt = f"Enter a new value for {category}:"
    new_value = simpledialog.askstring("Add new", prompt, parent=root)
    if new_value:
        current_values = list(combobox['values'])
        if new_value not in current_values:
            current_values.append(new_value)
            current_values.sort(key=str.lower)
            combobox['values'] = current_values
        combobox.set(new_value)

def update_dropdowns():
    """Update the Source, Category, and Unit dropdowns from the database."""
    source_values = get_dropdown_values("source")
    category_values = get_dropdown_values("category")
    unit_values = get_dropdown_values("size.unit")
    # If no units found, set a default list
    if not unit_values:
        unit_values = ["g", "kg", "ml", "piece"]
    combo_source['values'] = source_values
    combo_category['values'] = category_values
    combo_unit['values'] = unit_values

# --- ID Generation Functions ---

def compute_id():
    """
    Compute the ID in the format aaaa-bbb-cc-d:
    a: 4-digit value from the name,
    b: 3-digit value from the location (place),
    c: 2-digit count (existing items with same name + 1),
    d: checksum digit (sum of digits in a+b+c mod 10).
    """
    name_val = entry_name.get().strip()
    loc_val = entry_location_place.get().strip()
    # Compute a from name
    if not name_val:
        a_str = "0000"
    else:
        a_num = sum(ord(c) for c in name_val if c.isalnum()) % 10000
        a_str = f"{a_num:04d}"
    # Compute b from location place
    if not loc_val:
        b_str = "000"
    else:
        b_num = sum(ord(c) for c in loc_val if c.isalnum()) % 1000
        b_str = f"{b_num:03d}"
    # Compute c: count of existing items with same name + 1
    count = sum(1 for ingr in ingredients_data if ingr.get("name", "").lower() == name_val.lower()) + 1
    c_str = f"{count:02d}"
    # Compute checksum d: sum of digits in a_str+b_str+c_str mod 10
    combined = a_str + b_str + c_str
    checksum = sum(int(digit) for digit in combined) % 10
    d_str = str(checksum)
    new_id = f"{a_str}-{b_str}-{c_str}-{d_str}"
    return new_id

def update_id(event=None):
    """Update the ID field based on the name and location inputs."""
    new_id = compute_id()
    entry_id.config(state="normal")
    entry_id.delete(0, tk.END)
    entry_id.insert(0, new_id)
    entry_id.config(state="disabled")

def submit():
    """Collect data from the form, validate it against the schema, and save."""
    new_entry = {}
    # Basic information
    new_entry["id"] = entry_id.get().strip()
    new_entry["name"] = entry_name.get().strip()
    new_entry["category"] = combo_category.get().strip()
    new_entry["source"] = combo_source.get().strip()
    new_entry["best_before_date"] = date_entry.get().strip()  # Format: dd.mm.yyyy
    new_entry["is_staple"] = var_is_staple.get()
    
    # Location information
    new_entry["location"] = {"place": entry_location_place.get().strip()}
    shelf_val = entry_location_shelf.get().strip()
    try:
        new_entry["location"]["shelf"] = int(shelf_val) if shelf_val else 0
    except ValueError:
        new_entry["location"]["shelf"] = 0

    # Extract integer from the formatted dropdown text (e.g., "4: Vegan")
    try:
        new_entry["vegan_level"] = int(var_vegan_level.get().split(":")[0])
    except Exception:
        new_entry["vegan_level"] = 0
    try:
        new_entry["diet_level"] = int(var_diet_level.get().split(":")[0])
    except Exception:
        new_entry["diet_level"] = 0

    # Size information
    new_entry["size"] = {}
    try:
        new_entry["size"]["value"] = float(entry_size_value.get().strip())
    except ValueError:
        new_entry["size"]["value"] = 0.0
    new_entry["size"]["unit"] = combo_unit.get().strip()

    # Nutritional values
    new_entry["nutritional_values"] = {}
    try:
        new_entry["nutritional_values"]["energy"] = float(entry_energy.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["energy"] = 0.0

    new_entry["nutritional_values"]["fats"] = {}
    try:
        new_entry["nutritional_values"]["fats"]["total"] = float(entry_fat_total.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["fats"]["total"] = 0.0
    try:
        new_entry["nutritional_values"]["fats"]["saturated"] = float(entry_fat_saturated.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["fats"]["saturated"] = 0.0

    new_entry["nutritional_values"]["carbohydrates"] = {}
    try:
        new_entry["nutritional_values"]["carbohydrates"]["total"] = float(entry_carb_total.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["carbohydrates"]["total"] = 0.0
    try:
        new_entry["nutritional_values"]["carbohydrates"]["sugar"] = float(entry_carb_sugar.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["carbohydrates"]["sugar"] = 0.0

    try:
        new_entry["nutritional_values"]["proteins"] = float(entry_proteins.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["proteins"] = 0.0
    try:
        new_entry["nutritional_values"]["fiber"] = float(entry_fiber.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["fiber"] = 0.0
    try:
        new_entry["nutritional_values"]["salt"] = float(entry_salt.get().strip())
    except ValueError:
        new_entry["nutritional_values"]["salt"] = 0.0

    new_entry["storage_conditions"] = parse_array(entry_storage_conditions.get())
    new_entry["allergenes"] = parse_array(entry_allergenes.get())
    new_entry["personal_distaste"] = parse_array(entry_personal_distaste.get())
    new_entry["synonyms"] = parse_array(entry_synonyms.get())

    # Validate against the schema
    try:
        jsonschema.validate(instance=new_entry, schema=schema)
    except jsonschema.ValidationError as ve:
        messagebox.showerror("Validation Error", f"Data validation error:\n{ve.message}")
        return

    # Append new entry and save
    ingredients_data.append(new_entry)
    save_data(ingredients_data)
    messagebox.showinfo("Success", "Ingredient added successfully!")

    # Clear all fields after submission and update dropdowns
    entry_name.delete(0, tk.END)
    combo_category.set("")
    combo_source.set("")
    date_entry.set_date("")
    entry_location_place.delete(0, tk.END)
    entry_location_shelf.delete(0, tk.END)
    var_vegan_level.set(vegan_options[0])
    var_diet_level.set(diet_options[0])
    entry_size_value.delete(0, tk.END)
    combo_unit.set("")
    entry_energy.delete(0, tk.END)
    entry_fat_total.delete(0, tk.END)
    entry_fat_saturated.delete(0, tk.END)
    entry_carb_total.delete(0, tk.END)
    entry_carb_sugar.delete(0, tk.END)
    entry_proteins.delete(0, tk.END)
    entry_fiber.delete(0, tk.END)
    entry_salt.delete(0, tk.END)
    entry_storage_conditions.delete(0, tk.END)
    entry_allergenes.delete(0, tk.END)
    entry_personal_distaste.delete(0, tk.END)
    entry_synonyms.delete(0, tk.END)

    update_dropdowns()
    update_id()

# Ensure files and load data/schema
ensure_files_exist()
ingredients_data = load_data()
schema = load_schema()  # Schema from Ingredient_Schema.json

# Mapping options for vegan and diet levels
vegan_options = [
    "0: Non-Vegan",
    "1: Vegetarian / Ovo-Vegetarian",
    "2: Lacto-Vegetarian",
    "3: Semi-Vegan",
    "4: Vegan"
]
diet_options = [
    "0: Unrestricted",
    "1: Restricted",
    "2: Prohibited"
]

# Build main GUI
root = tk.Tk()
root.title("Masala Dabba")
root.geometry("1200x700")

# Main frame with overall padding
main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.grid(row=0, column=0, sticky="nsew")

# ----- Basic Information Group -----
# Split into two side-by-side frames for alignment.
frame_basic = ttk.LabelFrame(main_frame, text="Basic Information", padding="10 10 10 10")
frame_basic.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

left_basic = ttk.Frame(frame_basic)
left_basic.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
right_basic = ttk.Frame(frame_basic)
right_basic.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

# Left side: ID, Category, Best Before Date, Staple
ttk.Label(left_basic, text="ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_id = ttk.Entry(left_basic, width=20, state="disabled")
entry_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(left_basic, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
combo_category = ttk.Combobox(left_basic, width=18)
combo_category.grid(row=1, column=1, padx=5, pady=5, sticky="w")
btn_add_category = ttk.Button(left_basic, text="+", width=3,
                              command=lambda: add_new_dropdown_value(combo_category, "category"))
btn_add_category.grid(row=1, column=2, padx=5, pady=5, sticky="w")

ttk.Label(left_basic, text="Best Before Date:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
date_entry = DateEntry(left_basic, date_pattern="dd.mm.yyyy", width=18)
date_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")

var_is_staple = tk.BooleanVar()
chk_is_staple = ttk.Checkbutton(left_basic, text="Staple Ingredient", variable=var_is_staple)
chk_is_staple.grid(row=3, column=0, padx=5, pady=5, columnspan=2, sticky="w")

# Right side: Name and Source
ttk.Label(right_basic, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_name = ttk.Entry(right_basic, width=20)
entry_name.grid(row=0, column=1, padx=5, pady=5, sticky="w")
entry_name.bind("<KeyRelease>", update_id)

ttk.Label(right_basic, text="Source:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
combo_source = ttk.Combobox(right_basic, width=18)
combo_source.grid(row=1, column=1, padx=5, pady=5, sticky="w")
btn_add_source = ttk.Button(right_basic, text="+", width=3,
                            command=lambda: add_new_dropdown_value(combo_source, "source"))
btn_add_source.grid(row=1, column=2, padx=5, pady=5, sticky="w")

# ----- Location Group -----
frame_location = ttk.LabelFrame(main_frame, text="Location", padding="10 10 10 10")
frame_location.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

ttk.Label(frame_location, text="Place:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_location_place = ttk.Entry(frame_location, width=20)
entry_location_place.grid(row=0, column=1, padx=5, pady=5, sticky="w")
entry_location_place.bind("<KeyRelease>", update_id)

ttk.Label(frame_location, text="Shelf:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
entry_location_shelf = ttk.Entry(frame_location, width=10)
entry_location_shelf.grid(row=0, column=3, padx=5, pady=5, sticky="w")

# ----- Dietary Levels Group -----
frame_diet = ttk.LabelFrame(main_frame, text="Dietary Levels", padding="10 10 10 10")
frame_diet.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(frame_diet, text="Vegan Level:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
var_vegan_level = tk.StringVar(value=vegan_options[0])
combo_vegan = ttk.Combobox(frame_diet, textvariable=var_vegan_level,
                           values=vegan_options, state="readonly", width=30)
combo_vegan.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_diet, text="Diet Level:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
var_diet_level = tk.StringVar(value=diet_options[0])
combo_diet = ttk.Combobox(frame_diet, textvariable=var_diet_level,
                          values=diet_options, state="readonly", width=30)
combo_diet.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# ----- Size Group -----
frame_size = ttk.LabelFrame(main_frame, text="Size", padding="10 10 10 10")
frame_size.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

ttk.Label(frame_size, text="Value:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_size_value = ttk.Entry(frame_size, width=10)
entry_size_value.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_size, text="Unit:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
combo_unit = ttk.Combobox(frame_size, width=10)
combo_unit.grid(row=0, column=3, padx=5, pady=5, sticky="w")
btn_add_unit = ttk.Button(frame_size, text="+", width=3,
                          command=lambda: add_new_dropdown_value(combo_unit, "unit"))
btn_add_unit.grid(row=0, column=4, padx=5, pady=5, sticky="w")

# ----- Nutritional Values Group -----
frame_nutrition = ttk.LabelFrame(main_frame, text="Nutritional Values", padding="10 10 10 10")
frame_nutrition.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

ttk.Label(frame_nutrition, text="Energy (kcal):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_energy = ttk.Entry(frame_nutrition, width=10)
entry_energy.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_nutrition, text="Fat Total (g):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
entry_fat_total = ttk.Entry(frame_nutrition, width=10)
entry_fat_total.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_nutrition, text="Fat Saturated (g):").grid(row=1, column=2, padx=5, pady=5, sticky="w")
entry_fat_saturated = ttk.Entry(frame_nutrition, width=10)
entry_fat_saturated.grid(row=1, column=3, padx=5, pady=5, sticky="w")

ttk.Label(frame_nutrition, text="Carb Total (g):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
entry_carb_total = ttk.Entry(frame_nutrition, width=10)
entry_carb_total.grid(row=2, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_nutrition, text="Carb Sugar (g):").grid(row=2, column=2, padx=5, pady=5, sticky="w")
entry_carb_sugar = ttk.Entry(frame_nutrition, width=10)
entry_carb_sugar.grid(row=2, column=3, padx=5, pady=5, sticky="w")

ttk.Label(frame_nutrition, text="Proteins (g):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
entry_proteins = ttk.Entry(frame_nutrition, width=10)
entry_proteins.grid(row=3, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_nutrition, text="Fiber (g):").grid(row=3, column=2, padx=5, pady=5, sticky="w")
entry_fiber = ttk.Entry(frame_nutrition, width=10)
entry_fiber.grid(row=3, column=3, padx=5, pady=5, sticky="w")

ttk.Label(frame_nutrition, text="Salt (g):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
entry_salt = ttk.Entry(frame_nutrition, width=10)
entry_salt.grid(row=4, column=1, padx=5, pady=5, sticky="w")

# ----- Additional Information Group -----
frame_additional = ttk.LabelFrame(main_frame, text="Additional Information", padding="10 10 10 10")
frame_additional.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

ttk.Label(frame_additional, text="Storage Conditions (comma separated):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_storage_conditions = ttk.Entry(frame_additional, width=40)
entry_storage_conditions.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_additional, text="Allergenes (comma separated):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
entry_allergenes = ttk.Entry(frame_additional, width=40)
entry_allergenes.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_additional, text="Personal Distaste (comma separated):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
entry_personal_distaste = ttk.Entry(frame_additional, width=40)
entry_personal_distaste.grid(row=2, column=1, padx=5, pady=5, sticky="w")

ttk.Label(frame_additional, text="Synonyms (comma separated):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
entry_synonyms = ttk.Entry(frame_additional, width=40)
entry_synonyms.grid(row=3, column=1, padx=5, pady=5, sticky="w")

# ----- Submit Button -----
submit_button = ttk.Button(main_frame, text="Submit", command=submit)
submit_button.grid(row=4, column=0, columnspan=2, pady=10)

# Now that all widgets are defined, update the dropdowns and the auto-generated ID.
update_dropdowns()
update_id()

root.geometry("940x750")
root.mainloop()
