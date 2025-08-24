import re
from pyfiglet import Figlet
from tabulate import tabulate
import os
import uuid
import pickle
from datetime import datetime

figlet = Figlet()

# Files for owner credentials and inventory.
# Credentials file holds owner id and password.
# Inventory file stores the items dict with pickle.
CREDENTIALS_FILE = "owner_credentials.pkl"
INVENTORY_FILE = "inventory.pkl"

inventory = {}  # global inventory dict
# Keys: item code (int). Values: dict with Name, Price, Quantity.


# ---------- Helper functions (argument based) ----------
# These functions are useful for tests.
# They avoid input() and return or raise errors directly.

# parse and validate positive int from arg.
# Input: val (string or number).
# Output: int if valid.
# Raises ValueError for invalid or non-positive.
def input_positive_integer_arg(val):
    try:
        num = int(val)
        if num <= 0:
            raise ValueError("Value must be positive")
        return num
    except Exception:
        raise ValueError("Invalid integer input")


# add item to cart using passed structures.
# Inputs: user_cart dict, inventory_ref dict, item_code, quantity.
# Updates user_cart. Does not use IO.
# Raises KeyError if item missing. Raises ValueError for bad qty or low stock.
def add_to_cart_arg(user_cart, inventory_ref, item_code, quantity):
    if item_code not in inventory_ref:
        raise KeyError("Item code not found in inventory")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    available_quantity = inventory_ref[item_code]['Quantity']
    already_in_cart = user_cart.get(item_code, {}).get('Quantity', 0)
    if already_in_cart + quantity > available_quantity:
        raise ValueError("Not enough quantity available")
    if item_code in user_cart:
        user_cart[item_code]['Quantity'] += quantity
    else:
        user_cart[item_code] = {
            "Name": inventory_ref[item_code]['Name'],
            "Price": inventory_ref[item_code]['Price'],
            "Quantity": quantity
        }


# set new quantity for inventory item.
# Inputs: inventory_ref, item_code, new_quantity.
# Updates inventory_ref in place.
# Raises KeyError if item missing. Raises ValueError if negative.
def adjust_quantity_arg(inventory_ref, item_code, new_quantity):
    if item_code not in inventory_ref:
        raise KeyError("Item code not found in inventory")
    if new_quantity < 0:
        raise ValueError("Quantity cannot be negative")
    inventory_ref[item_code]['Quantity'] = new_quantity


# set new price for inventory item.
# Inputs: inventory_ref, item_code, new_price.
# Updates price in inventory. Price must be positive.
# Raises KeyError if missing. Raises ValueError if non-positive.
def adjust_item_price_arg(inventory_ref, item_code, new_price):
    if item_code not in inventory_ref:
        raise KeyError("Item code not found in inventory")
    if new_price <= 0:
        raise ValueError("Price must be positive")
    inventory_ref[item_code]['Price'] = new_price


# manage a cart item: remove or adjust.
# Inputs: user_cart, inventory_ref, item_code, action, new_quantity.
# Action 'remove' deletes item. Action 'adjust' sets new quantity.
# Raises KeyError or ValueError on bad inputs or insufficient stock.
def manage_cart_arg(user_cart, inventory_ref, item_code, action, new_quantity=None):
    if item_code not in user_cart:
        raise KeyError("Item not found in user cart")
    if action == 'remove':
        del user_cart[item_code]
    elif action == 'adjust':
        if new_quantity is None:
            raise ValueError("new_quantity must be provided for adjustment")
        if new_quantity <= 0:
            raise ValueError("Quantity must be positive")
        available_quantity = inventory_ref.get(item_code, {}).get('Quantity', 0)
        if new_quantity > available_quantity:
            raise ValueError("Not enough quantity available")
        user_cart[item_code]['Quantity'] = new_quantity
    else:
        raise ValueError("Invalid action. Use 'remove' or 'adjust'")


# validate and apply purchase without IO.
# Inputs: user_cart, inventory_ref.
# Checks stock, reduces inventory, removes zero items, clears cart.
# Returns a short transaction id. Raises on errors.
def confirm_purchase_arg(user_cart, inventory_ref):
    if not user_cart:
        raise ValueError("Cart is empty")
    for code, item in user_cart.items():
        if code not in inventory_ref:
            raise KeyError(f"Item code {code} not found in inventory")
        if item['Quantity'] > inventory_ref[code]['Quantity']:
            raise ValueError(f"Not enough item {item['Name']} in inventory")

    for code, item in user_cart.items():
        inventory_ref[code]['Quantity'] -= item['Quantity']

    to_remove = [code for code, item in inventory_ref.items() if item['Quantity'] == 0]
    for code in to_remove:
        del inventory_ref[code]

    transaction_id = str(uuid.uuid4())[:8]
    user_cart.clear()
    return transaction_id


# ---------- Interactive / IO functions ----------
# These functions use input() and print().
# They form the main app and owner/user flows.

# prompt until positive int given.
# Input: prompt string.
# Returns a positive int.
def input_positive_integer(prompt):
    while True:
        val = input(prompt).strip()
        if val.isdigit() and int(val) > 0:
            return int(val)
        print("\nInput must be a positive integer. Please try again.\n")


# main app loop.
# Loads credentials and inventory.
# Shows main menu for owner, user, or exit.
def main():
    global inventory
    owner_id, owner_password = setup_or_load_credentials()
    load_inventory()


    while True:
        try:
            print("Choose one among the following \n1.Owner(To manage)\n2.User(To purchase)\n3.Exit\n")
            user_input = int(input("Enter your choice (1/2/3): "))

            if user_input == 1:
                if owner_lock(owner_id, owner_password):
                    load_inventory()
                    if not inventory:
                        print("\n                 ~~~~ No inventory found. ~~~~")
                        print("   ~~~~ Your vending machine is empty. Please add items first. ~~~~")
                    load_items()

            elif user_input == 2:
                if not inventory:
                    print("\nWe're sorry for the inconvenience, but the vending machine is currently empty. "
                          "Please check back later or contact the owner to add items.\n")
                    continue
                display_items(inventory)
                if purchase_items():
                    break

            elif user_input == 3:
                save_inventory()
                break

            else:
                print("\nInvalid choice. Please enter (1/2/3).\n")

        except ValueError:
            print("\nInvalid choice. Please enter (1/2/3).\n")


# load or setup owner credentials.
# If file exists, load and greet.
# If not, prompt for new id and password and save them.
def setup_or_load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        f = Figlet(font='smslant')
        print(f.renderText("Welcome back!"))
        with open(CREDENTIALS_FILE, 'rb') as f:
            owner_id, owner_password = pickle.load(f)
        return owner_id, owner_password
    else:
        f = Figlet(font='smslant')
        print(f.renderText("Welcome"))
        print("\nIt looks like you're setting up for the first time.")
        owner_id = input("Enter your new Owner ID: ").strip()
        owner_password = input("Enter your new password: ").strip()
        with open(CREDENTIALS_FILE, 'wb') as f:
            pickle.dump((owner_id, owner_password), f)
        print("\nCredentials set up successfully!\n")
        return owner_id, owner_password


# prompt owner login.
# Compares entered id and password with stored values.
# Returns True on success. Prints messages.
def owner_lock(owner_id, owner_password):
    print("\n--- Owner Login ---")
    entered_id = input("Enter Owner ID: ").strip()
    entered_password = input("Enter your password: ").strip()
    if entered_id == owner_id and entered_password == owner_password:
        print("\nAccess granted to the owner menu.")
        return True
    else:
        print("\nIncorrect ID or password. Access denied!\n")
        return False


# load inventory from file if exists.
# Sets global inventory dict.
def load_inventory():
    global inventory
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'rb') as f:
            inventory = pickle.load(f)


# save inventory to file.
# Uses pickle to write current inventory.
def save_inventory():
    global inventory
    with open(INVENTORY_FILE, 'wb') as f:
        pickle.dump(inventory, f)
    print("\nInventory saved successfully.\n")


# owner menu to load, manage, display, or finish.
# Loops until owner chooses Done.
def load_items():
    while True:
        try:
            choice = int(input(
                "\nChoose one\n1.Load items into your machine\n2.Manage your machine\n3.Display items in the machine\n4.Done\nEnter your choice: "))
            if choice == 1:
                load_item_to_machine()
            elif choice == 2:
                manage_machine()
            elif choice == 3:
                display_items(inventory)
                total_value = sum(item['Price'] * item['Quantity'] for item in inventory.values())
                print(f"\nTotal Inventory Value: ${total_value:.2f}")

            elif choice == 4:
                if not inventory:
                    # If still empty after loading, exit managing as there's nothing to manage
                    print("\nNo items added. Returning to owner menu.\n")
                    return
                else:
                    print("\nNow your Vending machine is ready to sell items.")
                    save_inventory()
                    break
            else:
                print("\nInvalid input. Please enter (1/2/3/4).")

        except ValueError:
            print("\nInvalid input. Please enter (1/2/3/4).")


# add new item(s) to machine.
# Prompts for code, name, price, quantity.
# Validates name and prevents duplicate names.
def load_item_to_machine():
    global inventory
    while True:
        choice_input = input("\nChoose one\n1. Add new item\n2. Done\nEnter your choice: ").strip()
        if not choice_input.isdigit():
            print("\nInvalid input. Please enter 1 or 2.")
            continue
        choice = int(choice_input)

        if choice == 1:
            while True:
                item_code = input_positive_integer("Enter Item_code: ")
                if item_code <= 0:
                    print("\nItem code must be a positive integer. Please try again.\n")
                    continue
                break

            if item_code in inventory:
                while True:
                    add_more = input(f"Item code {item_code} already exists. Add more quantity? (y/n): ").strip().lower()
                    if add_more in ['y', 'yes']:
                        quantity_to_add = input_positive_integer("Enter quantity to add: ")
                        inventory[item_code]['Quantity'] += quantity_to_add
                        print(f"\nQuantity updated. New quantity: {inventory[item_code]['Quantity']}")
                        break
                    elif add_more in ['n', 'no']:
                        print("\nNo quantity added.\n")
                        break
                    else:
                        print("\nInvalid choice. Please enter (y) or (n).\n")
                continue  # Restart add item menu



            while True:
                name = input("Enter Item_name: ").strip().title()
                # Allow letters, numbers, spaces, hyphen, apostrophe, ampersand
                # Require at least one letter (A-Z or a-z)
                if not name or not re.match(r"^(?=.*[A-Za-z])[A-Za-z0-9\s\-\&']+$", name):
                    print("\nItem name must contain at least one letter and can include letters, numbers, spaces, hyphens (-), apostrophes ('), and ampersands (&). Please try again.\n")
                    continue

                # Check for duplicate names in inventory (case-insensitive)
                if any(item['Name'].lower() == name.lower() for item in inventory.values()):
                    print(f"\nAn item with the name '{name}' already exists in the inventory. Please use a different name.\n")
                    continue

                break


            while True:
                price_input = input("Enter Price of the Item: ").strip()
                try:
                    price = float(price_input)
                    if price <= 0:
                        print("\nPrice must be a positive number. Please try again.\n")
                        continue
                except ValueError:
                    print("\nPrice must be a positive number. Please try again.\n")
                    continue
                break

            quantity = input_positive_integer("Enter Quantity of Item: ")

            inventory[item_code] = {"Name": name, "Price": price, "Quantity": quantity}
            print(f"\n{quantity} {name}(s) added successfully into your Vending Machine.")

        elif choice == 2:
            print("\nDone adding items.")
            break
        else:
            print("\nInvalid Choice. Please Choose 1 or 2.")


# owner manage menu.
# Shows items then allows adjust, remove, or change price.
# Ensures inventory exists before operations.
def manage_machine():
    global inventory
    if not inventory:
        print("\n   ~~~~ Your vending machine is empty. Please add items first. ~~~~")
        load_item_to_machine()
        if not inventory:
            # If still empty after loading, exit managing as there's nothing to manage
            print("\nNo items added. Returning to owner menu.")
            return

    while True:
        display_items(inventory)
        try:
            manage_choice = int(input(
                "\nManage your machine\n1.Adjust quantity of item\n2.Remove item\n3.Adjust the price of the item\n4.Done\nEnter your choice: "))

            if manage_choice == 1:
                if not inventory:
                    print("\n   ~~~~ Your vending machine is empty. Please add items first. ~~~~")
                    load_item_to_machine()
                    continue
                adjust_quantity()

            elif manage_choice == 2:
                if not inventory:
                    print("\n   ~~~~ Your vending machine is empty. Please add items first. ~~~~")
                    load_item_to_machine()
                    continue
                remove_items(inventory)

            elif manage_choice == 3:
                if not inventory:
                    print("\n   ~~~~ Your vending machine is empty. Please add items first. ~~~~")
                    load_item_to_machine()
                    continue
                adjust_item_price()

            elif manage_choice == 4:
                break

            else:
                print("\nInvalid input. Please enter (1/2/3/4).")

        except ValueError:
            print("\nInvalid input. Please enter (1/2/3/4).")


# adjust quantity for an item.
# Prompts for item code then new quantity.
# Updates inventory and prints result.
def adjust_quantity():
    global inventory
    while True:
        item_code = input_positive_integer("Enter Item Code to adjust quantity: ")
        if item_code in inventory:
            while True:
                new_quantity = input_positive_integer("Enter new quantity: ")
                if new_quantity < 0:
                    print("\nQuantity must be a positive integer. Please try again.\n")
                else:
                    inventory[item_code]['Quantity'] = new_quantity
                    print(f"\nQuantity of {inventory[item_code]['Name']} adjusted to {new_quantity}.")
                    return
        else:
            print(f"\nItem with code {item_code} not found in inventory.\n")


# remove item from inventory.
# Shows current items then removes chosen code.
# Prints confirmation.
def remove_items(inventory_ref):
    while True:
        print("\nCurrent Inventory Items:")
        display_items(inventory_ref)
        remove_item_code = input_positive_integer("Enter Item Code to remove: ")
        if remove_item_code in inventory_ref:
            removed_item_name = inventory_ref[remove_item_code]['Name']
            del inventory_ref[remove_item_code]
            print(f"\nItem {removed_item_name} with code {remove_item_code} removed from inventory.")
            return
        else:
            print(f"\nItem with code {remove_item_code} not found in inventory.\n")


# adjust price for an item.
# Prompts for code and new price.
# Validates price and updates inventory.
def adjust_item_price():
    global inventory
    while True:
        item_code = input_positive_integer("Enter Item Code to adjust price: ")
        if item_code in inventory:
            while True:
                price_input = input("Enter new price: ").strip()
                try:
                    new_price = float(price_input)
                    if new_price <= 0:
                        print("\nPrice cannot be negative. Please try again.\n")
                    else:
                        inventory[item_code]['Price'] = new_price
                        print(f"\nPrice of {inventory[item_code]['Name']} adjusted to ${new_price:.2f}.")
                        return
                except ValueError:
                    print("\nPrice must be a positive number. Please try again.\n")
        else:
            print(f"\nItem with code {item_code} not found in inventory.\n")



# display inventory table.
# If empty, prompts to add items.
# Uses tabulate to print a fancy_grid table.
def display_items(inventory_ref):
    if not inventory_ref:
        print("\n   ~~~~ Your vending machine is empty. Please add items first. ~~~~   ")
        load_item_to_machine()
        if not inventory:
            # If still empty after loading, exit managing as there's nothing to manage
            print("\nNo items added. Returning to owner menu.")
            return

    print("\n           ~~~~~~~~~~~~~ Available Items ~~~~~~~~~~~~~")
    table_data = []
    for code, item_data in inventory_ref.items():
        row = [
            code,
            item_data['Name'],
            item_data['Price'],
            item_data['Quantity']
        ]
        table_data.append(row)

    headers = ['Item Code', 'Item Name', 'Price(in $)', 'Quantity(units)']
    print(tabulate(table_data, headers=headers, tablefmt='fancy_grid'))


# user purchase menu.
# Lets user add, view, manage, confirm purchase, or exit.
# Returns True to exit without purchase, False after a purchase.
def purchase_items():
    global inventory
    # If inventory is empty
    if not inventory:
        print("\nWe're sorry for the inconvenience, but the vending machine is currently empty. "
              "Please check back later or contact the owner to add items.\n")
        return False

    user_cart = {}
    while True:
        print("\nChoose one\n1. Add items into your cart\n2. View your cart\n3. Manage your cart\n4. Confirm Purchase\n5. Done(To Exit)")
        choice_input = input("\nEnter your choice: ").strip()
        if not choice_input.isdigit() or int(choice_input) not in [1, 2, 3, 4, 5]:
            print("\nInvalid input. Please enter (1/2/3/4/5).")
            continue
        user_choice = int(choice_input)

        # ---------------- OPTION 1: ADD ITEMS ----------------
        if user_choice == 1:
            while True:
                sub_choice = input("\n1. Add new item into your cart\n2. Done\nEnter your choice: ").strip()
                if sub_choice == "1":
                    add_to_cart(user_cart, inventory)
                elif sub_choice == "2":
                    break
                else:
                    print("\nInvalid input. Please enter 1 or 2.")

        # ---------------- OPTIONS 2, 3, 4: EMPTY CART CHECK ----------------
        elif user_choice in [2, 3, 4]:
            if not user_cart:
                print("\n----- Your cart is empty. Please add items to purchase. -----")
                while True:
                    sub_choice = input("\n1. Add new item into your cart\n2. Done\nEnter your choice: ").strip()
                    if sub_choice == "1":
                        add_to_cart(user_cart, inventory)
                        break
                    elif sub_choice == "2":
                        break
                    else:
                        print("\nInvalid input. Please enter 1 or 2.\n")
                continue

            # When cart has items
            if user_choice == 2:
                view_cart(user_cart)
            elif user_choice == 3:
                manage_cart(user_cart, inventory)
            elif user_choice == 4:
                if confirm_purchase(user_cart, inventory):
                    return False  # Exit after successful purchase

        # ---------------- OPTION 5: EXIT ----------------
        elif user_choice == 5:
            while True:
                exit_input = input("Do you want to exit? (y/n): ").strip().lower()
                if exit_input in ['y', 'yes']:
                    return True  # Exit confirmed
                elif exit_input in ['n', 'no']:
                    break  # Cancel exit, back to menu
                else:
                    print("\nInvalid input. Please enter 'y' or 'n'.\n")



# interactive add to cart.
# Prompts for code and quantity.
# Checks available stock and updates user_cart.
def add_to_cart(user_cart, inventory_ref):
    while True:
        user_item_code = input_positive_integer("Enter Item_code (positive integer): ")
        if user_item_code not in inventory_ref:
            print(f"\nItem with code {user_item_code} not found in inventory.\n")
            continue
        quantity = input_positive_integer("Enter Quantity of Item (positive integer): ")
        available_quantity = inventory_ref[user_item_code]['Quantity']
        item_name = inventory_ref[user_item_code]['Name']
        already_in_cart = user_cart[user_item_code]['Quantity'] if user_item_code in user_cart else 0
        if quantity + already_in_cart > available_quantity:
            print(f"\nOnly {available_quantity - already_in_cart} {item_name}(s) available for adding. Please adjust your quantity.\n")
            if available_quantity - already_in_cart == 0:
                print("No more can be added to cart.")
                break
            continue
        if user_item_code in user_cart:
            user_cart[user_item_code]['Quantity'] += quantity
        else:
            user_cart[user_item_code] = {
                "Name": item_name,
                "Price": inventory_ref[user_item_code]['Price'],
                "Quantity": quantity
            }
        print(f"\n{quantity} {item_name}(s) added to cart.")
        break


# print cart and total.
# Shows table of cart items and total cost.
def view_cart(user_cart):
    if not user_cart:
        print("\n   ----- Your cart is empty. Please add items to purchase. -----")
    else:
        print("\n               ~~~~~~~~~~~~~ Your Cart ~~~~~~~~~~~~~       ")
        table_data = []
        total_price = 0
        for code, item_data in user_cart.items():
            row = [
                code,
                item_data['Name'],
                item_data['Price'],
                item_data['Quantity']
            ]
            table_data.append(row)
            total_price += item_data['Price'] * item_data['Quantity']
        headers = ['Item Code', 'Item Name', 'Price(in $)', 'Quantity(units)']
        print(tabulate(table_data, headers=headers, tablefmt='fancy_grid'))
        print(f"\nTotal Price: ${total_price:.2f}\n")


# manage items in cart.
# Lets user remove or change quantity of one cart item.
# Validates code and stock before applying changes.
def manage_cart(user_cart, inventory_ref):
    if not user_cart:
        print("\n   ----- Your cart is empty. Please add items to purchase. -----")
        return
    print("\n           ~~~~~~~~~~~~ Manage Your Cart ~~~~~~~~~~~~    ")
    table_data = []
    for code, item_data in user_cart.items():
        row = [
            code,
            item_data['Name'],
            item_data['Price'],
            item_data['Quantity']
        ]
        table_data.append(row)
    headers = ['Item Code', 'Item Name', 'Price(in $)', 'Quantity(units)']
    print(tabulate(table_data, headers=headers, tablefmt='fancy_grid'))
    while True:
        manage_item_code = input_positive_integer("Enter Item Code to manage: ")
        if manage_item_code not in user_cart:
            print(f"\nItem with code {manage_item_code} not found in cart.\n")
            continue
        break

    while True:
        manage_choice_input = input("Do you want to \n(1) Remove item or \n(2) Adjust quantity? \nEnter your choice: ").strip()
        if not manage_choice_input.isdigit() or int(manage_choice_input) not in [1, 2]:
            print("\nInvalid choice. Please enter 1 or 2.\n")
            continue
        manage_choice = int(manage_choice_input)
        if manage_choice == 1:
            del user_cart[manage_item_code]
            print(f"\nItem with code {manage_item_code} removed from cart.")
            break
        elif manage_choice == 2:
            while True:
                new_qty = input_positive_integer("Enter new quantity (positive integer): ")
                available_quantity = inventory_ref[manage_item_code]['Quantity']
                if new_qty > available_quantity:
                    print(f"Only {available_quantity} {user_cart[manage_item_code]['Name']}(s) available.\n")
                    continue
                user_cart[manage_item_code]['Quantity'] = new_qty
                print(f"\nQuantity of {user_cart[manage_item_code]['Name']} updated to {new_qty}.")
                break
            break


# confirm purchase with IO.
# Shows bill preview and asks for confirmation.
# Updates inventory, prints messages, saves inventory, and clears cart on success.
def confirm_purchase(user_cart, inventory_ref):
    if not user_cart:
        print("\n   ----- Your cart is empty. Please add items to purchase. -----")
        return False

    print("\n                   ~~~~~~~~~~~~~ Confirm Purchase ~~~~~~~~~~~~~       ")

    table_data = []
    total_price = 0
    for code, item_data in user_cart.items():
        each_item_total = item_data['Price'] * item_data['Quantity']
        total_price += each_item_total
        row = [
            code,
            item_data['Name'],
            item_data['Price'],
            item_data['Quantity'],
            each_item_total
        ]
        table_data.append(row)

    headers = ['Item Code', 'Item Name', 'Price(in $)', 'Quantity(units)', 'Each Item Total(in $)']
    print(tabulate(table_data, headers=headers, tablefmt='fancy_grid'))
    print(f"\nTotal Price: ${total_price:.2f}\n")

    while True:
        confirm = input("Confirm purchase? (y/n): ").strip().lower()
        if confirm in ["y", "yes"]:
            transaction_id = str(uuid.uuid4())[:8]

            for code, item_data in dict(user_cart).items():
                inventory_ref[code]['Quantity'] -= item_data['Quantity']
                if inventory_ref[code]['Quantity'] == 0:
                    print(f"{item_data['Name']} is now out of stock and removed from inventory.\n")
                    del inventory_ref[code]
            print("\n   ~~~~ Purchase successful ~~~~")
            generate_bill(user_cart, total_price, transaction_id)
            user_cart.clear()
            save_inventory()
            return True
        elif confirm in ["n", "no"]:
            print("\n   ~~~~ Purchase cancelled ~~~~")
            return False
        else:
            print("\nInvalid input. Please enter 'y' or 'n'.\n")


# print bill and thank you.
# Shows timestamp, transaction id, items table, and total.
# Prints a thank you ascii art at the end.
def generate_bill(user_cart, total_price, transaction_id=None):
    print("\n   ~~~~~ Generating Bill ~~~~~")

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    if transaction_id:
        print(f"Transaction ID: {transaction_id}")
    print(f"Date & Time: {timestamp}\n")

    table_data = []
    for code, item_data in user_cart.items():
        row = [
            code,
            item_data['Name'],
            item_data['Price'],
            item_data['Quantity'],
            item_data['Price'] * item_data['Quantity']
        ]
        table_data.append(row)

    headers = ['Item Code', 'Item Name', '1 Item Cost(in $)', 'Quantity(units)', 'Total(in $)']
    print(tabulate(table_data, headers=headers, tablefmt='fancy_grid'))
    print(f"\nTotal Price: ${total_price:.2f}\n")

    f = Figlet(font='standard')
    print(f.renderText("Thank You\nVisit Us Again"))


if __name__ == "__main__":
    main()
