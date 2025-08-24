# Vending Machine Management System

#### Video Demo: https://youtu.be/xH3iBCPr17U

---

## Description

This is a command-line based **Vending Machine Management System** built with Python. It’s designed to be used by two kinds of people:

- **Owners** – load and manage stock in the vending machine.
- **Users** – add and manage the items to the cart and purchase items.

The program stores data (inventory and owner credentials) in `.pkl` files using Python’s `pickle` module, meaning everything persists even after you close and reopen it. The UI is purely terminal-based, with neat ASCII banners (`pyfiglet`) and clean tables (`tabulate`) for a better experience.

A key part of the design is separating **logic** from **user interaction**. Argument-based helper functions do the actual work without calling `input()` or `print()`, making them easy to test with `pytest`. Interactive functions handle menus, prompts, and display output.

---

## Requirements

- pyfiglet
- tabulate
- pytest

---
## List of Libraries & Modules used


- [re](#re)
- [pyfiglet](#pyfiglet)
- [tabulate](#tabulate)
- [os](#os)
- [uuid](#uuid)
- [pickle](#pickle)
- [datetime](#datetime)
- [pytest](#pytest)

---
## Key Features

### Owner
- **First-time setup**: Prompted to set Owner ID and password.
- **Login system** with stored credentials.
- **Load new items** into inventory with checks to prevent duplicate codes or names.
- **Manage stock**: adjust quantity, update prices, or remove items.
- **View inventory** in a table with a calculated total stock value.
- **Save changes** automatically to `inventory.pkl`.

### User
- **See available items** in a nicely formatted table.
- **Add items to cart** with quantity validation against stock.
- **View/Manage cart**: remove items or change quantities.
- **Confirm a purchase**: show a bill, update inventory, and generate a unique short transaction ID.
- **Print receipt** with date, time, and final total.

### Persistent Data Storage
  - Credentials saved in `owner_credentials.pkl`.
  - Inventory saved in `inventory.pkl`, retaining updates between program runs.

### Readable CLI Output
  - ASCII art headings using `pyfiglet`.
  - Clear, table-based displays using `tabulate`.

---

## File Overview

### `project.py`
The main application file.
Contains:
- **Helper (testable) functions** – handle all logic like `add_to_cart_arg`, `adjust_quantity_arg`, `confirm_purchase_arg` etc.
- **Interactive functions** – handle owner and user flows, menus, and printed output.
- **Persistence functions** – load and save inventory/credentials using `pickle`.
- **Billing** – generates a neat bill with totals and ASCII art at checkout.

### `test_project.py`
A small but useful test suite using `pytest`.
Checks all the argument-based helper functions for:
- Correct results for normal inputs.
- Proper error handling for invalid data.
- Edge case correctness like stock limits and nonexistent items.

### `requirements.txt`
Lists required Python packages (`pyfiglet`, `tabulate`, `pytest`) that can be installed using PIP.


---

## Libraries and Modules Used

Here are the libraries and modules used in this project and why they are included:

- ### re
  This is Python’s regular expression module. It is used when adding a new item to check if the name is valid. The check makes sure the name has at least one letter and only certain characters like letters, numbers, spaces, hyphens, apostrophes, and ampersands.

- ### pyfiglet
  This shows text in big ASCII art style in the terminal. It is used for welcome messages and the “thank you” note at the end, to make the program look nicer.

- ### tabulate
  This makes it easy to print tables in the terminal. It is used to show the inventory, the cart, and the bill in a clean and readable layout.

- ### os
  This is from Python’s standard library. It is used here to check if the files for saving credentials or inventory already exist.

- ### uuid
  This creates unique IDs. In this project, it is used to give each purchase a special transaction ID so it can be tracked.

- ### pickle
  This is part of Python and is used to save and load data. The inventory and owner credentials are stored in files using pickle so that the information is kept even when the program is closed.

- ### datetime
  This is used to get the current date and time. It is included on the bill so the purchase has a timestamp.

- ### pytest
  This is a Python testing framework used in this project to check that core functions work correctly and handle errors as expected.

---

## Example Flow

### Owner:
1. Run `python project.py`
2. Pick option `1` (Owner).
3. Enter credentials (or set them up the first time).
4. Add a few items, say:
   - `101` - Water - $1.00 - 10 units
   - `102` - Soda - $1.50 - 5 units
5. Save and exit. Vending machine is now ready for customers(users).

### User:
1. Pick option `2` (User) from the menu.
2. Check what’s in stock.
3. Add some items to cart, keeping an eye on available quantity.
4. View cart, make changes if needed.
5. Proceed to purchase – see the bill, confirm, and get a transaction ID.

---
