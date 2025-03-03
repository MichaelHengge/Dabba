import os
import json
import datetime
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from ttkbootstrap.widgets import DateEntry, Checkbutton, Menubutton
import jsonschema
import hashlib

date_entry_available = True


# File and folder paths
JSON_DIR = "Json"
INGREDIENTS_FILE = os.path.join(JSON_DIR, "Ingredients.json")
SCHEMA_FILE = os.path.join(JSON_DIR, "Ingredient_Schema.json")

def ensure_files_exist():
    """Ensure that the Json folder and Ingredients.json file exist.
       Also, verify that the Ingredient_Schema.json exists."""
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
    if not os.path.exists(INGREDIENTS_FILE):
        # Initialize as an empty list database
        with open(INGREDIENTS_FILE, "w") as f:
            json.dump([], f, indent=4)
    if not os.path.exists(SCHEMA_FILE):
        messagebox.showerror("Error", "Ingredient_Schema.json not found in the Json folder.")
        exit(1)

def load_database():
    """Load the ingredients database from file."""
    with open(INGREDIENTS_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_database(db):
    """Save the ingredients database to file."""
    with open(INGREDIENTS_FILE, "w") as f:
        json.dump(db, f, indent=4)

def load_schema():
    """Load the JSON schema for ingredients."""
    with open(SCHEMA_FILE, "r") as f:
        return json.load(f)

def get_unique_dropdown_options(db, key):
    """Collect unique values from the database for the given key.
       For 'unit' (which is inside the size object) the lookup is done differently."""
    values = set()
    for entry in db:
        if key == "unit":
            if "size" in entry and "unit" in entry["size"]:
                values.add(entry["size"]["unit"])
        elif key in entry:
            values.add(entry[key])
    return sorted(list(values))

def generate_id(name, place, shelf):
        """Generate a unique ID based on name and location (place + shelf)."""
        data = f"{name.lower()}_{place.lower()}_{shelf}"
        return hashlib.sha1(data.encode()).hexdigest()[:10]

class IngredientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Masala Dabba")
        # Load database and schema at startup
        self.ingredients = load_database()
        self.schema = load_schema()

        # Define vegan and diet level options (showing number and description)
        self.vegan_options = [
            "0: non-vegan",
            "1: vegetarian",
            "2: ovo-vegetarian",
            "3: lacto-vegetarian",
            "4: vegan"
        ]
        self.diet_options = [
            "0: unrestricted",
            "1: restricted",
            "2: prohibited"
        ]

        # Main frame with overall padding
        mainframe = ttk.Frame(root, padding="10")
        mainframe.grid(row=0, column=0, sticky="NSEW")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Create two frames for left and right columns (wider-than-tall layout)
        left_frame = ttk.Frame(mainframe)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="NSEW")
        right_frame = ttk.Frame(mainframe)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="NSEW")

        # -------------------- Basic Info Group --------------------
        basic_frame = ttk.Labelframe(left_frame, text="Basic Info", padding=10)
        basic_frame.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        ttk.Label(basic_frame, text="ID:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.id_entry = ttk.Entry(basic_frame, state=READONLY)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="Name:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.name_entry = ttk.Entry(basic_frame)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="Category:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(basic_frame, textvariable=self.category_var, state=READONLY)
        self.update_dropdown(self.category_combo, get_unique_dropdown_options(self.ingredients, "category"))
        self.category_combo.grid(row=2, column=1, padx=5, pady=5)
        self.category_add_btn = ttk.Button(basic_frame, text="+", width=2, bootstyle=(INFO, OUTLINE),
                                           command=lambda: self.add_new_option(self.category_combo))
        self.category_add_btn.grid(row=2, column=2, padx=5, pady=5, sticky=W)

        ttk.Label(basic_frame, text="Source:").grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(basic_frame, textvariable=self.source_var, state=READONLY)
        self.update_dropdown(self.source_combo, get_unique_dropdown_options(self.ingredients, "source"))
        self.source_combo.grid(row=3, column=1, padx=5, pady=5)
        self.source_add_btn = ttk.Button(basic_frame, text="+", width=2, bootstyle=(INFO, OUTLINE),
                                         command=lambda: self.add_new_option(self.source_combo))
        self.source_add_btn.grid(row=3, column=2, padx=5, pady=5, sticky=W)

        ttk.Label(basic_frame, text="Synonyms (csv):").grid(row=4, column=0, sticky=W, padx=5, pady=5)
        self.synonyms_entry = ttk.Entry(basic_frame)
        self.synonyms_entry.grid(row=4, column=1, padx=5, pady=5)

        # -------------------- Location Group --------------------
        location_frame = ttk.Labelframe(left_frame, text="Location", padding=10)
        location_frame.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
        # Place and Shelf on the same line, with Is Staple next to Shelf
        ttk.Label(location_frame, text="Place:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.place_entry = ttk.Entry(location_frame)
        self.place_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(location_frame, text="Shelf:").grid(row=0, column=2, sticky=W, padx=5, pady=5)
        self.shelf_spin = ttk.Spinbox(location_frame, from_=0, to=100, width=5)
        self.shelf_spin.grid(row=0, column=3, padx=5, pady=5)
        self.shelf_spin.set(0)
        self.is_staple_var = tk.BooleanVar()
        self.is_staple_check = Checkbutton(location_frame, text="Is Staple", variable=self.is_staple_var, bootstyle="round-toggle")
        self.is_staple_check.grid(row=0, column=4, padx=5, pady=5)


        # -------------------- Additional Info Group --------------------
        additional_frame = ttk.Labelframe(left_frame, text="Additional Info", padding=10)
        additional_frame.grid(row=2, column=0, sticky="NSEW", padx=5, pady=5)
        ttk.Label(additional_frame, text="Storage Conditions (csv):").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.storage_entry = ttk.Entry(additional_frame)
        self.storage_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(additional_frame, text="Allergenes (csv):").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.allergenes_entry = ttk.Entry(additional_frame)
        self.allergenes_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(additional_frame, text="Personal Distaste (csv):").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.distaste_entry = ttk.Entry(additional_frame)
        self.distaste_entry.grid(row=2, column=1, padx=5, pady=5)

        # -------------------- Diet & Size Group --------------------
        diet_frame = ttk.Labelframe(right_frame, text="Diet & Size", padding=10)
        diet_frame.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        ttk.Label(diet_frame, text="Vegan Level:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.vegan_var = tk.StringVar()
        self.vegan_combo = ttk.Combobox(diet_frame, textvariable=self.vegan_var,
                                        values=self.vegan_options, state="readonly")
        self.vegan_combo.grid(row=0, column=1, padx=5, pady=5)
        self.vegan_combo.current(0)

        ttk.Label(diet_frame, text="Diet Level:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.diet_var = tk.StringVar()
        self.diet_combo = ttk.Combobox(diet_frame, textvariable=self.diet_var,
                                       values=self.diet_options, state="readonly")
        self.diet_combo.grid(row=1, column=1, padx=5, pady=5)
        self.diet_combo.current(0)

        # Size (value and unit on one line)
        ttk.Label(diet_frame, text="Size:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.size_value_spin = ttk.Spinbox(diet_frame, from_=0, to=10000, increment=1)
        self.size_value_spin.grid(row=2, column=1, padx=5, pady=5)
        self.size_value_spin.set(0)
        self.unit_var = tk.StringVar()
        # Pre-fill with defined units and select the first entry
        predefined_units = ["g", "kg", "ml", "l", "piece"]
        self.unit_combo = ttk.Combobox(diet_frame, textvariable=self.unit_var, width=8, state=READONLY)
        self.unit_combo['values'] = predefined_units
        self.unit_combo.set(predefined_units[0])
        self.unit_combo.grid(row=2, column=2, padx=5, pady=5)
        self.unit_add_btn = ttk.Button(diet_frame, text="+", width=2, bootstyle=(INFO, OUTLINE),
                                       command=lambda: self.add_new_option(self.unit_combo))
        self.unit_add_btn.grid(row=2, column=3, padx=5, pady=5, sticky=W)

        ttk.Label(diet_frame, text="Best Before Date:").grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.best_before_date = DateEntry(diet_frame, dateformat='%d.%m.%Y')
        self.best_before_date.grid(row=3, column=1, padx=5, pady=5)


        # -------------------- Nutritional Values Group --------------------
        nutrition_frame = ttk.Labelframe(right_frame, text="Nutritional Values", padding=10)
        nutrition_frame.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
        ttk.Label(nutrition_frame, text="Energy (kcal):").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.energy_spin = ttk.Spinbox(nutrition_frame, from_=0, to=10000, increment=0.1)
        self.energy_spin.grid(row=0, column=1, padx=5, pady=5)
        self.energy_spin.set(0)
        self.energy_unit_var = tk.StringVar()
        # Pre-fill with defined units and select the first entry
        energy_predefined_units = ["kJ", "kcal"]
        self.energy_unit_combo = ttk.Combobox(nutrition_frame, textvariable=self.energy_unit_var, width=8, state=READONLY)
        self.energy_unit_combo['values'] = energy_predefined_units
        self.energy_unit_combo.set(energy_predefined_units[0])
        self.energy_unit_combo.grid(row=0, column=2, padx=5, pady=5)

        # Fats subgroup
        fats_frame = ttk.Labelframe(nutrition_frame, text="Fats", padding=10)
        fats_frame.grid(row=1, column=0, columnspan=2, sticky="NSEW", padx=5, pady=5)
        ttk.Label(fats_frame, text="Total (g/100g):").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.fat_total_spin = ttk.Spinbox(fats_frame, from_=0, to=100, increment=0.1)
        self.fat_total_spin.grid(row=0, column=1, padx=5, pady=5)
        self.fat_total_spin.set(0)
        ttk.Label(fats_frame, text="Saturated (g/100g):").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.fat_sat_spin = ttk.Spinbox(fats_frame, from_=0, to=100, increment=0.1)
        self.fat_sat_spin.grid(row=1, column=1, padx=5, pady=5)
        self.fat_sat_spin.set(0)

        # Carbohydrates subgroup
        carb_frame = ttk.Labelframe(nutrition_frame, text="Carbohydrates", padding=10)
        carb_frame.grid(row=2, column=0, columnspan=2, sticky="NSEW", padx=5, pady=5)
        ttk.Label(carb_frame, text="Total (g/100g):").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.carb_total_spin = ttk.Spinbox(carb_frame, from_=0, to=100, increment=0.1)
        self.carb_total_spin.grid(row=0, column=1, padx=5, pady=5)
        self.carb_total_spin.set(0)
        ttk.Label(carb_frame, text="Sugar (g/100g):").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.sugar_spin = ttk.Spinbox(carb_frame, from_=0, to=100, increment=0.1)
        self.sugar_spin.grid(row=1, column=1, padx=5, pady=5)
        self.sugar_spin.set(0)

        ttk.Label(nutrition_frame, text="Fiber (g/100g):").grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.fiber_spin = ttk.Spinbox(nutrition_frame, from_=0, to=100, increment=0.1)
        self.fiber_spin.grid(row=3, column=1, padx=5, pady=5)
        self.fiber_spin.set(0)
        ttk.Label(nutrition_frame, text="Proteins (g/100g):").grid(row=4, column=0, sticky=W, padx=5, pady=5)
        self.proteins_spin = ttk.Spinbox(nutrition_frame, from_=0, to=100, increment=0.1)
        self.proteins_spin.grid(row=4, column=1, padx=5, pady=5)
        self.proteins_spin.set(0)
        ttk.Label(nutrition_frame, text="Salt (g/100g):").grid(row=5, column=0, sticky=W, padx=5, pady=5)
        self.salt_spin = ttk.Spinbox(nutrition_frame, from_=0, to=100, increment=0.1)
        self.salt_spin.grid(row=5, column=1, padx=5, pady=5)
        self.salt_spin.set(0)

        # -------------------- Submit Button --------------------
        submit_btn = ttk.Button(mainframe, text="Submit", command=self.submit_entry)
        submit_btn.grid(row=1, column=0, columnspan=2, pady=10)


        # --------------------- EVENT BINDINGS ----------------------
        self.name_entry.bind("<KeyRelease>", lambda event: self.update_id())
        self.place_entry.bind("<KeyRelease>", lambda event: self.update_id())
        self.shelf_spin.bind("<FocusOut>", lambda event: self.update_id())  # Update when user clicks out
        self.shelf_spin.bind("<Return>", lambda event: self.update_id())  # Update when Enter is pressed
        self.shelf_spin.bind("<<Increment>>", lambda event: self.update_id())  # Update when spinbox value increases
        self.shelf_spin.bind("<<Decrement>>", lambda event: self.update_id())  # Update when spinbox value decreases



        self.name_entry.focus()

    def update_id(self):
        """Update the ID field dynamically based on name and location."""
        name = self.name_entry.get().strip()
        place = self.place_entry.get().strip()
        shelf = self.shelf_spin.get().strip()  # Spinbox values are strings

        new_id = generate_id(name, place, shelf)
        self.id_entry.config(state='normal')
        self.id_entry.delete(0, tk.END)
        self.id_entry.insert(0, new_id)
        self.id_entry.config(state='readonly')


    def update_dropdown(self, combobox, items):
        """Sort the items and update the combobox options."""
        items = sorted(items)
        combobox['values'] = items
        if items:
            combobox.set(items[0])
        else:
            combobox.set("")

    def add_new_option(self, combobox):
        """Allow the user to add a new option to a dropdown."""
        new_value = simpledialog.askstring("Add New", "Enter new value:")
        if new_value:
            current_items = list(combobox['values'])
            if new_value not in current_items:
                current_items.append(new_value)
                current_items = sorted(current_items)
                combobox['values'] = current_items
                combobox.set(new_value)

    def submit_entry(self):
        """Gather data from the form, validate it against the schema, and save if valid."""
        entry = {}
        entry["id"] = self.id_entry.get().strip()
        entry["name"] = self.name_entry.get().strip()
        entry["location"] = {
            "place": self.place_entry.get().strip(),
            "shelf": int(self.shelf_spin.get())
        }
        vegan_sel = self.vegan_var.get().split(":")
        entry["vegan_level"] = int(vegan_sel[0].strip()) if vegan_sel[0].isdigit() else 0
        diet_sel = self.diet_var.get().split(":")
        entry["diet_level"] = int(diet_sel[0].strip()) if diet_sel[0].isdigit() else 0
        entry["size"] = {
            "value": int(self.size_value_spin.get()),
            "unit": self.unit_var.get().strip()
        }
        entry["source"] = self.source_var.get().strip()
        entry["best_before_date"] = self.best_before_date.entry.get().strftime("%d.%m.%Y")

        # Check if kJ or kcal and store as kJ because I'm a physicist :)
        energy = float(self.energy_spin.get())
        if self.energy_unit_combo.get() == 'kcal':
            energy *= 4.184 
        
        entry["nutritional_values"] = {
            "energy": energy,
            "fats": {
                "total": float(self.fat_total_spin.get()),
                "saturated": float(self.fat_sat_spin.get())
            },
            "carbohydrates": {
                "total": float(self.carb_total_spin.get()),
                "sugar": float(self.sugar_spin.get())
            },
            "proteins": float(self.proteins_spin.get()),
            "fiber": float(self.fiber_spin.get()),
            "salt": float(self.salt_spin.get())
        }
        entry["storage_conditions"] = [s.strip() for s in self.storage_entry.get().split(",") if s.strip()]
        entry["category"] = self.category_var.get().strip()
        entry["is_staple"] = self.is_staple_var.get()
        entry["allergenes"] = [s.strip() for s in self.allergenes_entry.get().split(",") if s.strip()]
        entry["personal_distaste"] = [s.strip() for s in self.distaste_entry.get().split(",") if s.strip()]
        entry["synonyms"] = [s.strip() for s in self.synonyms_entry.get().split(",") if s.strip()]

        try:
            jsonschema.validate(instance=entry, schema=self.schema)
        except jsonschema.ValidationError as e:
            messagebox.showerror("Validation Error", f"Data validation error: {e.message}")
            return

        self.ingredients.append(entry)
        save_database(self.ingredients)
        messagebox.showinfo("Success", "Ingredient added successfully!")
        self.update_dropdown(self.unit_combo, get_unique_dropdown_options(self.ingredients, "unit"))
        self.update_dropdown(self.source_combo, get_unique_dropdown_options(self.ingredients, "source"))
        self.update_dropdown(self.category_combo, get_unique_dropdown_options(self.ingredients, "category"))
        self.clear_form()

    def clear_form(self):
        """Reset all form fields."""
        self.id_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.place_entry.delete(0, tk.END)
        self.shelf_spin.delete(0, tk.END)
        self.shelf_spin.insert(0, "0")
        self.vegan_combo.current(0)
        self.diet_combo.current(0)
        self.size_value_spin.delete(0, tk.END)
        self.size_value_spin.insert(0, "0")
        self.unit_combo.set("")
        self.source_combo.set("")
        if date_entry_available:
            self.best_before_date.set_date(datetime.date.today())
        else:
            self.best_before_date.delete(0, tk.END)
        self.energy_spin.delete(0, tk.END)
        self.energy_spin.insert(0, "0")
        self.fat_total_spin.delete(0, tk.END)
        self.fat_total_spin.insert(0, "0")
        self.fat_sat_spin.delete(0, tk.END)
        self.fat_sat_spin.insert(0, "0")
        self.carb_total_spin.delete(0, tk.END)
        self.carb_total_spin.insert(0, "0")
        self.sugar_spin.delete(0, tk.END)
        self.sugar_spin.insert(0, "0")
        self.proteins_spin.delete(0, tk.END)
        self.proteins_spin.insert(0, "0")
        self.fiber_spin.delete(0, tk.END)
        self.fiber_spin.insert(0, "0")
        self.salt_spin.delete(0, tk.END)
        self.salt_spin.insert(0, "0")
        self.storage_entry.delete(0, tk.END)
        self.allergenes_entry.delete(0, tk.END)
        self.distaste_entry.delete(0, tk.END)
        self.synonyms_entry.delete(0, tk.END)

def create_gui():
    """Create the main GUI window and return the root and app instance."""
    root = ttk.Window(themename="lumen")
    app = IngredientApp(root)
    return root, app

def main():
    ensure_files_exist()
    root, app = create_gui()
    root.mainloop()

if __name__ == "__main__":
    main()
