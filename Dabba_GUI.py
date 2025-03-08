import os
import json
import datetime
import re
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from ttkbootstrap.widgets import DateEntry, Checkbutton, Menubutton
import jsonschema
import hashlib
import requests
from PIL import Image, ImageTk
import io

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
        elif key == "place":  # Places are inside the "location" object
            if "location" in entry and "place" in entry["location"]:
                values.add(entry["location"]["place"])
        elif key in entry:
            values.add(entry[key])
    return sorted(list(values))

def generate_id(name, place, shelf):
    """Generate a unique ID based on name and location, ensuring at least one letter."""
    data = f"{name.lower()}_{place.lower()}_{shelf}"
    hashed = hashlib.sha1(data.encode()).hexdigest()[:10]  # First 10 characters

    # Ensure at least one alphabet character
    if not re.search(r"[a-zA-Z]", hashed):  
        hashed = hashed[:-1] + 'a'  # Replace last char with 'a' to ensure a letter

    return hashed

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
            "1: pescetarian",
            "2: ovo-lacto-vegetarian",
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
        basic_frame.columnconfigure(3, weight=1)
        ttk.Label(basic_frame, text="ID:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.id_entry = ttk.Entry(basic_frame, state=READONLY)
        self.id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="GTIN:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.gtin_entry = ttk.Entry(basic_frame)
        self.gtin_entry.grid(row=1, column=1, padx=5, pady=5)
        self.gtin_button = ttk.Button(basic_frame, text="🔍", bootstyle="OUTLINE", command=self.fetch_gtin_data)
        self.gtin_button.grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(basic_frame, text="Name:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.name_entry = ttk.Entry(basic_frame)
        self.name_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="Category:").grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(basic_frame, textvariable=self.category_var, state=READONLY)
        self.update_dropdown(self.category_combo, get_unique_dropdown_options(self.ingredients, "category"))
        self.category_combo.grid(row=3, column=1, padx=5, pady=5)
        self.category_add_btn = ttk.Button(basic_frame, text="+", width=2, bootstyle=(INFO, OUTLINE),
                                           command=lambda: self.add_new_option(self.category_combo))
        self.category_add_btn.grid(row=3, column=2, padx=5, pady=5, sticky=W)

        ttk.Label(basic_frame, text="Source:").grid(row=4, column=0, sticky=W, padx=5, pady=5)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(basic_frame, textvariable=self.source_var, state=READONLY)
        self.update_dropdown(self.source_combo, get_unique_dropdown_options(self.ingredients, "source"))
        self.source_combo.grid(row=4, column=1, padx=5, pady=5)
        self.source_add_btn = ttk.Button(basic_frame, text="+", width=2, bootstyle=(INFO, OUTLINE),
                                         command=lambda: self.add_new_option(self.source_combo))
        self.source_add_btn.grid(row=4, column=2, padx=5, pady=5, sticky=W)

        ttk.Label(basic_frame, text="Synonyms (csv):").grid(row=5, column=0, sticky=W, padx=5, pady=5)
        self.synonyms_entry = ttk.Entry(basic_frame)
        self.synonyms_entry.grid(row=5, column=1, padx=5, pady=5)

        # Product Image Label (Spans all rows, centered vertically)
        self.image_label = ttk.Label(basic_frame, anchor="center")
        self.image_label.grid(row=0, column=3, rowspan=6, padx=10, pady=5, sticky="NS")
        self.image_label.grid_remove()


        # -------------------- Location Group --------------------
        location_frame = ttk.Labelframe(left_frame, text="Location", padding=10)
        location_frame.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
        # Place and Shelf on the same line
        self.place_var = tk.StringVar()
        self.place_combo = ttk.Combobox(location_frame, textvariable=self.place_var, state="readonly")
        self.update_dropdown(self.place_combo, get_unique_dropdown_options(self.ingredients, "place"))
        self.place_combo.grid(row=0, column=1, padx=5, pady=5)

        # Add "+" button to add new places
        self.place_add_btn = ttk.Button(location_frame, text="+", width=2, command=lambda: self.add_new_option(self.place_combo), bootstyle=(INFO, OUTLINE))
        self.place_add_btn.grid(row=0, column=2, padx=5, pady=5, sticky="W")

        ttk.Label(location_frame, text="Shelf:").grid(row=0, column=3, sticky=W, padx=5, pady=5)
        self.shelf_spin = ttk.Spinbox(location_frame, from_=0, to=100, width=5)
        self.shelf_spin.grid(row=0, column=4, padx=5, pady=5)
        self.shelf_spin.set(0)

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
        ttk.Label(additional_frame, text="Price (€):").grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.price_spin = ttk.Spinbox(additional_frame, from_=0, to=1000, increment=0.01)
        self.price_spin.set(0)
        self.price_spin.grid(row=3, column=1, padx=5, pady=5)

        # ------------------- Comment Group --------------------------
        comment_frame = ttk.Labelframe(left_frame, text="Comment", padding=10)
        comment_frame.grid(row=3, column=0, sticky="NSEW", padx=5, pady=5)
        comment_frame.columnconfigure(0, weight=1)
        self.comment_entry = ttk.Entry(comment_frame)
        self.comment_entry.grid(row=0, column=0, padx=5, pady=5, sticky="NSEW")

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

        self.is_staple_var = tk.BooleanVar()
        self.is_staple_check = Checkbutton(diet_frame, text="Is Staple", variable=self.is_staple_var, bootstyle="round-toggle")
        self.is_staple_check.grid(row=3, column=2, padx=5, pady=5)


        # -------------------- Nutritional Values Group --------------------
        nutrition_frame = ttk.Labelframe(right_frame, text="Nutritional Values", padding=10)
        nutrition_frame.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
        ttk.Label(nutrition_frame, text="Energy (/100g):").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.energy_spin = ttk.Spinbox(nutrition_frame, from_=0, to=10000, increment=0.1)
        self.energy_spin.grid(row=0, column=1, padx=5, pady=5)
        self.energy_spin.set(0)
        self.energy_unit_var = tk.StringVar()
        # Pre-fill with defined units and select the first entry
        self.energy_predefined_units = ["kJ", "kcal"]
        self.energy_unit_combo = ttk.Combobox(nutrition_frame, textvariable=self.energy_unit_var, width=8, state=READONLY)
        self.energy_unit_combo['values'] = self.energy_predefined_units
        self.energy_unit_combo.set(self.energy_predefined_units[0])
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

        # ---------------------- Button Frame ----------------------
        button_frame = ttk.Frame(mainframe)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        # Clear Button (Left of Submit)
        clear_btn = ttk.Button(button_frame, text="Clear", bootstyle="danger", command=self.clear_form)
        clear_btn.grid(row=0, column=0, padx=5)

        # Submit Button
        submit_btn = ttk.Button(button_frame, text="Submit", bootstyle="success", command=self.submit_entry)
        submit_btn.grid(row=0, column=1, padx=5)


        # --------------------- EVENT BINDINGS ----------------------
        self.name_entry.bind("<KeyRelease>", lambda event: self.update_id())
        self.place_combo.bind("<KeyRelease>", lambda event: self.update_id())
        self.shelf_spin.bind("<FocusOut>", lambda event: self.update_id())  # Update when user clicks out
        self.shelf_spin.bind("<Return>", lambda event: self.update_id())  # Update when Enter is pressed
        self.shelf_spin.bind("<<Increment>>", lambda event: self.update_id())  # Update when spinbox value increases
        self.shelf_spin.bind("<<Decrement>>", lambda event: self.update_id())  # Update when spinbox value decreases
        self.gtin_entry.bind("<Return>", lambda event: self.fetch_gtin_data())

        self.size_value_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.energy_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.fat_total_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.fat_sat_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.carb_total_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.sugar_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.proteins_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.fiber_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.salt_spin.bind("<FocusOut>", self.format_spinbox_value)
        self.price_spin.bind("<FocusOut>", self.format_spinbox_value)

        self.gtin_entry.focus()

    def test(self):
        pass

    def display_image(self, url):
        """Fetch and display product image from URL while maintaining aspect ratio."""
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                image_data = Image.open(io.BytesIO(response.content))

                # Define max width & height while maintaining aspect ratio
                max_size = (180, 180)  # Max width and height
                image_data.thumbnail(max_size, Image.Resampling.LANCZOS)  # Resize with aspect ratio

                self.image = ImageTk.PhotoImage(image_data)  # Keep a reference

                self.image_label.config(image=self.image)  # Show image
                self.image_label.grid()  # Make it visible
            else:
                print("Image could not be loaded (HTTP error). Hiding image.")  # Debugging
                self.image_label.grid_remove()  # Hide on error
        except Exception as e:
            print(f"Error loading image: {e}")  # Debugging
            self.image_label.grid_remove()  # Hide if an error occurs

    def format_spinbox_value(self, event):
        """Replace comma with dot in a spinbox value when focus is lost."""
        widget = event.widget  # Get the spinbox that triggered the event
        value = widget.get().replace(",", ".")  # Replace German decimal separator
        widget.delete(0, tk.END)  # Clear current value
        widget.insert(0, value)  # Insert corrected value

    def fetch_gtin_data(self):
        """Fetch and autofill ingredient details from GTIN."""
        gtin = self.gtin_entry.get().strip()
        if gtin:
            data = self.lookup_gtin(gtin)  # Calls the API lookup function
            if data:
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, data["name"])

                # Extract numeric part (size) and unit
                size_text = data["size"]
                match = re.match(r"([\d,.]+)\s*([a-zA-Z]*)", size_text)  # Extract number and unit

                if match:
                    size_value, unit_value = match.groups()
                    size_value = size_value.replace(",", ".")  # Convert comma to dot
                    self.size_value_spin.delete(0, tk.END)
                    self.size_value_spin.insert(0, size_value)  # Store numeric size

                    # Check if unit exists in the dropdown
                    existing_units = self.unit_combo["values"]
                    if unit_value in existing_units:
                        self.unit_combo.set(unit_value)  # Select the unit
                    else:
                        messagebox.showwarning("Unknown Unit", f"The unit '{unit_value}' is not in the list.")

                if not data["synonyms"] == "Unknown":
                    self.synonyms_entry.delete(0, tk.END)
                    self.synonyms_entry.insert(0, data["synonyms"])  # Fill in synonyms

                self.allergenes_entry.delete(0, tk.END)
                cleaned_allergens = [a.split(":")[-1] for a in data["allergenes"]]  # Remove country code
                self.allergenes_entry.insert(0, ", ".join(cleaned_allergens))  # Display cleaned list

                image_url = data.get("image_url", None)
                print(f"GTIN Image URL: {image_url}")
                if image_url:
                    self.display_image(image_url)
                else:
                    self.image_label.grid_remove()

                # Nutritional values
                if "nutritional_values" in data:
                    nutriments = data["nutritional_values"]
                    self.energy_spin.delete(0, tk.END)
                    self.energy_spin.insert(0, nutriments.get("energy-kcal_100g", 0))  # Energy
                    self.energy_unit_combo.set(self.energy_predefined_units[0])

                    self.fat_total_spin.delete(0, tk.END)
                    self.fat_total_spin.insert(0, nutriments.get("fat_100g", 0))  # Total fat

                    self.fat_sat_spin.delete(0, tk.END)
                    self.fat_sat_spin.insert(0, nutriments.get("saturated-fat_100g", 0))  # Saturated fat

                    self.carb_total_spin.delete(0, tk.END)
                    self.carb_total_spin.insert(0, nutriments.get("carbohydrates_100g", 0))  # Carbs

                    self.sugar_spin.delete(0, tk.END)
                    self.sugar_spin.insert(0, nutriments.get("sugars_100g", 0))  # Sugar

                    self.proteins_spin.delete(0, tk.END)
                    self.proteins_spin.insert(0, nutriments.get("proteins_100g", 0))  # Protein

                    self.fiber_spin.delete(0, tk.END)
                    self.fiber_spin.insert(0, nutriments.get("fiber_100g", 0))  # Fiber

                    self.salt_spin.delete(0, tk.END)
                    self.salt_spin.insert(0, nutriments.get("salt_100g", 0))  # Salt

                #messagebox.showinfo("GTIN Lookup", f"Product: {data['name']}\nBrand: {data['brand']}")
                self.category_combo.focus()
            else:
                messagebox.showwarning("GTIN Lookup", "No data found for this GTIN.")

    def lookup_gtin(self, gtin):
        """Fetch product details using GTIN from Open Food Facts."""
        url = f"https://de.openfoodfacts.org/api/v0/product/{gtin}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if "product" in data:
                product = data["product"]

                # Extract the best available image URL
                image_url = product.get("image_url") or \
                            product.get("image_front_url") or \
                            product.get("image_small_url")
            
                return {
                    "name": product.get("product_name", "Unknown"),
                    "brand": product.get("brands", "Unknown"),
                    "size": product.get("quantity", "Unknown"),  # Size of the product
                    "synonyms": product.get("generic_name", "Unknown"),  # Alternative names
                    "allergenes": product.get("allergens_tags", []),  # List of allergens
                    "nutritional_values": product.get("nutriments", {}),  # Nutritional information
                    "image_url": image_url
                }
        return None  # Return None if GTIN not found

    def update_id(self):
        """Update the ID field dynamically based on name and location."""

        # Only update if GTIN not present
        if not self.gtin_entry.get() == "":
            return

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
        if self.gtin_entry == "":
            entry["id"] = self.id_entry.get().strip()
        else:
            entry["id"] = self.gtin_entry.get().strip()
        entry["name"] = self.name_entry.get().strip()
        entry["location"] = {
            "place": self.place_var.get().strip(),
            "shelf": int(self.shelf_spin.get())
        }
        vegan_sel = self.vegan_var.get().split(":")
        entry["vegan_level"] = int(vegan_sel[0].strip()) if vegan_sel[0].isdigit() else 0
        diet_sel = self.diet_var.get().split(":")
        entry["diet_level"] = int(diet_sel[0].strip()) if diet_sel[0].isdigit() else 0
        entry["size"] = {
            "value": float(self.size_value_spin.get()),
            "unit": self.unit_var.get().strip()
        }
        entry["source"] = self.source_var.get().strip()
        entry["best_before_date"] = self.best_before_date.entry.get()

        # Check if kJ or kcal and store as kJ because I'm a physicist :)
        energy = float(self.energy_spin.get())
        if self.energy_unit_combo.get() == 'kcal':
            energy = 4.184 
        
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
        entry["price"] = float(self.price_spin.get())
        entry["comment"] = self.comment_entry.get().strip()

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
        self.gtin_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.place_combo.current(0)
        self.shelf_spin.delete(0, tk.END)
        self.shelf_spin.insert(0, "0")
        self.vegan_combo.current(0)
        self.diet_combo.current(0)
        self.size_value_spin.delete(0, tk.END)
        self.size_value_spin.insert(0, "0")
        self.unit_combo.current(0)
        self.source_combo.current(0)
        self.best_before_date.configure(startdate=datetime.date.today())
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
        self.price_spin.delete(0, tk.END)
        self.price_spin.insert(0, "0")
        self.synonyms_entry.delete(0, tk.END)
        self.is_staple_var = False
        self.comment_entry.delete(0, tk.END)

        self.gtin_entry.focus()

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
