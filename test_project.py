import pytest
from project import (
    input_positive_integer_arg,
    add_to_cart_arg,
    adjust_quantity_arg,
    adjust_item_price_arg,
    manage_cart_arg,
    confirm_purchase_arg
)

def test_input_positive_integer_arg():
    assert input_positive_integer_arg("1") == 1
    assert input_positive_integer_arg("42") == 42
    assert input_positive_integer_arg("99999") == 99999

    with pytest.raises(ValueError):
        input_positive_integer_arg("0")
    with pytest.raises(ValueError):
        input_positive_integer_arg("-5")
    with pytest.raises(ValueError):
        input_positive_integer_arg("abc")
    with pytest.raises(ValueError):
        input_positive_integer_arg("3.14")


def test_add_to_cart_arg():
    inventory = {
        1: {"Name": "Water", "Price": 1.0, "Quantity": 10},
        2: {"Name": "Soda", "Price": 1.5, "Quantity": 5}
    }
    cart = {}

    # Add item normally
    add_to_cart_arg(cart, inventory, 1, 3)
    assert cart[1]["Quantity"] == 3

    # Add more quantity to existing item in cart
    add_to_cart_arg(cart, inventory, 1, 4)
    assert cart[1]["Quantity"] == 7

    # Add new item to cart
    add_to_cart_arg(cart, inventory, 2, 2)
    assert cart[2]["Quantity"] == 2

    # Try adding invalid item code
    with pytest.raises(KeyError):
        add_to_cart_arg(cart, inventory, 3, 1)

    # Quantity zero or negative
    with pytest.raises(ValueError):
        add_to_cart_arg(cart, inventory, 1, 0)
    with pytest.raises(ValueError):
        add_to_cart_arg(cart, inventory, 1, -1)

    # Quantity exceeding availability
    with pytest.raises(ValueError):
        # Trying to add more than available after considering cart quantity
        add_to_cart_arg(cart, inventory, 2, 10)


def test_adjust_quantity_arg():
    inventory = {
        1: {"Name": "Water", "Price": 1.0, "Quantity": 10}
    }
    adjust_quantity_arg(inventory, 1, 5)
    assert inventory[1]["Quantity"] == 5

    with pytest.raises(KeyError):
        adjust_quantity_arg(inventory, 2, 1)

    with pytest.raises(ValueError):
        adjust_quantity_arg(inventory, 1, -10)


def test_adjust_item_price_arg():
    inventory = {
        1: {"Name": "Water", "Price": 1.0, "Quantity": 10}
    }
    adjust_item_price_arg(inventory, 1, 2.5)
    assert inventory[1]["Price"] == 2.5

    with pytest.raises(KeyError):
        adjust_item_price_arg(inventory, 2, 1.5)

    with pytest.raises(ValueError):
        adjust_item_price_arg(inventory, 1, 0)

    with pytest.raises(ValueError):
        adjust_item_price_arg(inventory, 1, -3.5)


def test_manage_cart_arg():
    inventory = {
        1: {"Name": "Water", "Price": 1.0, "Quantity": 10},
        2: {"Name": "Soda", "Price": 1.5, "Quantity": 5}
    }
    cart = {
        1: {"Name": "Water", "Price": 1.0, "Quantity": 3},
        2: {"Name": "Soda", "Price": 1.5, "Quantity": 2}
    }

    # Remove item
    manage_cart_arg(cart, inventory, 1, 'remove')
    assert 1 not in cart

    # Adjust quantity valid
    manage_cart_arg(cart, inventory, 2, 'adjust', 4)
    assert cart[2]["Quantity"] == 4

    # Adjust quantity exceeding stock
    with pytest.raises(ValueError):
        manage_cart_arg(cart, inventory, 2, 'adjust', 10)

    # Adjust with zero or negative quantity
    with pytest.raises(ValueError):
        manage_cart_arg(cart, inventory, 2, 'adjust', 0)
    with pytest.raises(ValueError):
        manage_cart_arg(cart, inventory, 2, 'adjust', -1)

    # Invalid action
    with pytest.raises(ValueError):
        manage_cart_arg(cart, inventory, 2, 'invalid_action')

    # Item not in cart
    with pytest.raises(KeyError):
        manage_cart_arg(cart, inventory, 999, 'remove')


def test_confirm_purchase_arg():
    inventory = {
        1: {"Name": "Water", "Price": 1.0, "Quantity": 10},
        2: {"Name": "Soda", "Price": 1.5, "Quantity": 5}
    }
    cart = {
        1: {"Name": "Water", "Price": 1.0, "Quantity": 3},
        2: {"Name": "Soda", "Price": 1.5, "Quantity": 5}
    }

    # Confirm purchase success
    transaction_id = confirm_purchase_arg(cart, inventory)
    assert isinstance(transaction_id, str)
    assert len(transaction_id) == 8
    assert cart == {}  # Cart cleared
    assert inventory[1]["Quantity"] == 7  # 10 - 3
    assert 2 not in inventory  # Sold out and removed

    # Confirm purchase with empty cart
    with pytest.raises(ValueError):
        confirm_purchase_arg({}, inventory)

    # Cart item not in inventory
    cart_invalid = {3: {"Name": "Juice", "Price": 2.0, "Quantity": 1}}
    with pytest.raises(KeyError):
        confirm_purchase_arg(cart_invalid, inventory)

    # Not enough stock in inventory
    inventory[4] = {"Name": "Chips", "Price": 1.0, "Quantity": 1}
    cart_too_much = {4: {"Name": "Chips", "Price": 1.0, "Quantity": 2}}
    with pytest.raises(ValueError):
        confirm_purchase_arg(cart_too_much, inventory)
