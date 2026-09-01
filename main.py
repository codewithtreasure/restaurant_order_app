import os
import sys
import json
from datetime import datetime

import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock

from database import CanteenDatabase, FOOD_IMAGES_DIR

# Set default window size and clear background color
Window.clearcolor = (0.10, 0.07, 0.07, 1.0)
Window.size = (1200, 780)
Window.minimum_width, Window.minimum_height = 980, 680


class ColorCard(BoxLayout):
    """Custom Card container with rounded background styling."""
    def __init__(self, bg_color=(0.16, 0.12, 0.11, 1.0), radius=[10], border_color=None, padding=10, spacing=8, **kwargs):
        super().__init__(padding=padding, spacing=spacing, **kwargs)
        self.bg_color = bg_color
        self.radius = radius
        self.border_color = border_color
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            if self.border_color:
                Color(*self.border_color)
                self.line = Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], self.radius[0]), width=1.4)
            else:
                self.line = None
                
        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def _update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        if self.line:
            self.line.rounded_rectangle = (instance.pos[0], instance.pos[1], instance.size[0], instance.size[1], self.radius[0])


class StyledButton(Button):
    """Custom styled button with rounded aesthetic and hover/press response."""
    def __init__(self, bg_color=(0.06, 0.72, 0.51, 1.0), text_color=(1, 1, 1, 1), radius=[8], **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = text_color
        self.bold = True
        self.bg_color = bg_color
        self.radius = radius
        
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)
            
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class FoodCardWidget(ColorCard):
    """Visual food menu card item showing image, name, category, price, and add button with legible typography."""
    def __init__(self, item, on_add_callback, **kwargs):
        super().__init__(
            bg_color=(0.18, 0.14, 0.13, 1.0),
            border_color=(0.32, 0.25, 0.22, 1.0),
            orientation="vertical",
            padding=10,
            spacing=8,
            radius=[12],
            **kwargs
        )
        self.item = item
        self.on_add_callback = on_add_callback
        
        # Image Header Container
        img_container = BoxLayout(size_hint_y=None, height=130)
        img_path = item.get("image_path", "")
        if img_path and os.path.exists(img_path):
            img_widget = Image(source=img_path, allow_stretch=True, keep_ratio=False)
        else:
            img_widget = Image(source="", allow_stretch=True) # Fallback image
        img_container.add_widget(img_widget)
        self.add_widget(img_container)

        # Title & Category Box
        info_box = BoxLayout(orientation="vertical", spacing=3, size_hint_y=None, height=52)
        name_lbl = Label(
            text=item.get("name", "Food Item"),
            font_size="15sp",
            bold=True,
            color=(0.99, 0.98, 0.97, 1.0),
            halign="left",
            valign="middle",
            text_size=(220, None)
        )
        name_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        
        cat_lbl = Label(
            text=f"🏷️ {item.get('category', 'General')}",
            font_size="12sp",
            color=(0.88, 0.82, 0.76, 1.0),
            halign="left",
            valign="middle",
            text_size=(220, None)
        )
        cat_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        info_box.add_widget(name_lbl)
        info_box.add_widget(cat_lbl)
        self.add_widget(info_box)

        # Price and Action Row
        action_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=38, spacing=6)
        price_val = float(item.get("price", 0.0))
        price_lbl = Label(
            text=f"₦{price_val:,.2f}",
            font_size="16sp",
            bold=True,
            color=(0.96, 0.62, 0.04, 1.0),
            size_hint_x=0.55,
            halign="left",
            valign="middle"
        )
        price_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))

        btn_add = StyledButton(
            text="➕ ADD",
            font_size="13sp",
            bg_color=(0.06, 0.72, 0.51, 1.0),
            size_hint_x=0.45,
            height=36
        )
        btn_add.bind(on_press=lambda inst: self.on_add_callback(self.item))
        
        action_row.add_widget(price_lbl)
        action_row.add_widget(btn_add)
        self.add_widget(action_row)


class AKomolafeCanteenApp(App):
    def build(self):
        self.title = "AKomolafe Food Canteen - POS & Management System"
        self.db = CanteenDatabase()
        self.orders = []  # List of ordered item dicts: {"item_id", "name", "price", "quantity", "cost"}
        self.current_category = "All"
        self.search_query = ""

        # Main Root Layout
        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        # 1. Header Banner
        header = ColorCard(
            bg_color=(0.22, 0.14, 0.12, 1.0),
            border_color=(0.96, 0.62, 0.04, 1.0),
            orientation="horizontal",
            size_hint_y=None,
            height=85,
            padding=[16, 10],
            spacing=12
        )
        
        # Restaurant Title & Slogan
        title_box = BoxLayout(orientation="vertical", spacing=3, size_hint_x=0.48)
        t_lbl = Label(
            text="🍲 AKOMOLAFE FOOD CANTEEN",
            font_size="22sp",
            bold=True,
            color=(0.96, 0.62, 0.04, 1.0),
            halign="left",
            valign="middle"
        )
        t_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        sub_lbl = Label(
            text="Authentic Nigerian Delicacies • Spot-On Quality & Taste",
            font_size="13sp",
            color=(0.90, 0.85, 0.80, 1.0),
            halign="left",
            valign="middle"
        )
        sub_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        title_box.add_widget(t_lbl)
        title_box.add_widget(sub_lbl)
        header.add_widget(title_box)

        # Header Action Controls (Inventory Box & Sales Receipts)
        header_actions = BoxLayout(orientation="horizontal", spacing=10, size_hint_x=0.52)
        
        btn_inventory = StyledButton(
            text="📦 INVENTORY BOX",
            font_size="13sp",
            bg_color=(0.85, 0.45, 0.10, 1.0),
            size_hint_y=None,
            height=46
        )
        btn_inventory.bind(on_press=self.open_inventory_modal)
        
        btn_invoice = StyledButton(
            text="📄 GENERATE INVOICE",
            font_size="13sp",
            bg_color=(0.10, 0.60, 0.85, 1.0),
            size_hint_y=None,
            height=46
        )
        btn_invoice.bind(on_press=self.open_invoice_modal)
        
        btn_sales = StyledButton(
            text="📜 SALES HISTORY",
            font_size="13sp",
            bg_color=(0.25, 0.45, 0.70, 1.0),
            size_hint_y=None,
            height=46
        )
        btn_sales.bind(on_press=self.open_sales_history_modal)

        btn_reset_menu = StyledButton(
            text="🔄 RE-SEED MENU",
            font_size="12sp",
            bg_color=(0.40, 0.35, 0.35, 1.0),
            size_hint_y=None,
            height=46
        )
        btn_reset_menu.bind(on_press=self.confirm_reset_menu)

        header_actions.add_widget(btn_inventory)
        header_actions.add_widget(btn_invoice)
        header_actions.add_widget(btn_sales)
        header_actions.add_widget(btn_reset_menu)
        header.add_widget(header_actions)

        root.add_widget(header)

        # 2. Main Content Body (Left: Food Menu Grid & Search, Right: Order Summary & Checkout)
        main_content = BoxLayout(orientation="horizontal", spacing=12)

        # --- LEFT PANEL: MENU SEARCH & CATALOG ---
        left_panel = BoxLayout(orientation="vertical", spacing=10, size_hint_x=0.62)

        # Search Bar & Category Filter Bar Card
        filter_card = ColorCard(
            bg_color=(0.16, 0.12, 0.11, 1.0),
            orientation="vertical",
            size_hint_y=None,
            height=95,
            padding=10,
            spacing=8
        )

        # Search Bar
        search_box = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=38)
        search_lbl = Label(text="🔍 Search:", font_size="15sp", bold=True, color=(0.96, 0.62, 0.04, 1.0), size_hint_x=None, width=85)
        self.search_input = TextInput(
            hint_text="Type food name (e.g. Eba, Amala, Suya, Beef, Rice...)",
            multiline=False,
            background_color=(0.26, 0.20, 0.19, 1.0),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.96, 0.62, 0.04, 1.0),
            font_size="14sp"
        )
        self.search_input.bind(text=self.on_search_text_change)
        search_box.add_widget(search_lbl)
        search_box.add_widget(self.search_input)
        filter_card.add_widget(search_box)

        # Category Bar
        cat_box = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height=36)
        categories = ["All", "Swallows & Soups", "Rice & Staples", "Proteins & Meat", "Drinks & Snacks"]
        self.cat_buttons = {}
        for cat in categories:
            btn = StyledButton(
                text=cat,
                font_size="12sp",
                bg_color=(0.96, 0.62, 0.04, 1.0) if cat == "All" else (0.26, 0.20, 0.19, 1.0),
                text_color=(0.1, 0.1, 0.1, 1.0) if cat == "All" else (0.90, 0.90, 0.90, 1.0),
                height=34
            )
            btn.bind(on_press=lambda inst, c=cat: self.select_category(c))
            self.cat_buttons[cat] = btn
            cat_box.add_widget(btn)

        filter_card.add_widget(cat_box)
        left_panel.add_widget(filter_card)

        # Food Catalog Grid ScrollView
        catalog_card = ColorCard(
            bg_color=(0.14, 0.10, 0.09, 1.0),
            orientation="vertical",
            padding=10,
            spacing=10
        )
        
        self.catalog_scroll = ScrollView(do_scroll_x=False)
        self.catalog_grid = GridLayout(cols=3, spacing=12, size_hint_y=None)
        self.catalog_grid.bind(minimum_height=self.catalog_grid.setter('height'))
        self.catalog_scroll.add_widget(self.catalog_grid)
        catalog_card.add_widget(self.catalog_scroll)

        left_panel.add_widget(catalog_card)
        main_content.add_widget(left_panel)

        # --- RIGHT PANEL: ORDER CART & BILLING ---
        right_panel = BoxLayout(orientation="vertical", spacing=10, size_hint_x=0.38)

        # Total Balance Card
        total_card = ColorCard(
            bg_color=(0.22, 0.14, 0.12, 1.0),
            border_color=(0.96, 0.62, 0.04, 1.0),
            orientation="vertical",
            size_hint_y=None,
            height=95,
            padding=10,
            spacing=3
        )
        total_title = Label(text="💳 CURRENT BILL TOTAL", font_size="14sp", bold=True, color=(0.90, 0.85, 0.80, 1.0))
        self.total_val_lbl = Label(text="₦0.00", font_size="32sp", bold=True, color=(0.96, 0.62, 0.04, 1.0))
        total_card.add_widget(total_title)
        total_card.add_widget(self.total_val_lbl)
        right_panel.add_widget(total_card)

        # Customer & Payment Info Card
        cust_card = ColorCard(
            bg_color=(0.16, 0.12, 0.11, 1.0),
            orientation="vertical",
            size_hint_y=None,
            height=100,
            padding=10,
            spacing=6
        )
        cust_row = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height=36)
        cust_row.add_widget(Label(text="Customer:", font_size="13sp", bold=True, color=(0.95, 0.95, 0.95, 1), size_hint_x=0.3))
        self.cust_input = TextInput(
            hint_text="e.g. Chief Adeleke",
            text="Walk-in Customer",
            multiline=False,
            font_size="13sp",
            background_color=(0.26, 0.20, 0.19, 1.0),
            foreground_color=(1, 1, 1, 1),
            size_hint_x=0.7
        )
        cust_row.add_widget(self.cust_input)
        cust_card.add_widget(cust_row)

        pay_row = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height=36)
        pay_row.add_widget(Label(text="Payment:", font_size="13sp", bold=True, color=(0.95, 0.95, 0.95, 1), size_hint_x=0.3))
        self.pay_spinner = Spinner(
            text="POS Card",
            values=("Cash", "POS Card", "Bank Transfer"),
            font_size="13sp",
            bold=True,
            background_normal="",
            background_color=(0.26, 0.20, 0.19, 1.0),
            color=(1, 1, 1, 1),
            size_hint_x=0.7
        )
        pay_row.add_widget(self.pay_spinner)
        cust_card.add_widget(pay_row)
        right_panel.add_widget(cust_card)

        # Order Items List Card
        order_list_card = ColorCard(
            bg_color=(0.16, 0.12, 0.11, 1.0),
            orientation="vertical",
            padding=10,
            spacing=8
        )
        
        cart_header = BoxLayout(orientation="horizontal", size_hint_y=None, height=28)
        cart_header.add_widget(Label(text="📋 ORDERED ITEMS", font_size="15sp", bold=True, color=(0.96, 0.62, 0.04, 1.0), halign="left"))
        self.cart_count_lbl = Label(text="0 Items", font_size="13sp", bold=True, color=(0.85, 0.85, 0.85, 1), halign="right")
        cart_header.add_widget(self.cart_count_lbl)
        order_list_card.add_widget(cart_header)

        # Order items ScrollView
        self.order_scroll = ScrollView(do_scroll_x=False)
        self.order_grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.order_grid.bind(minimum_height=self.order_grid.setter('height'))
        self.order_scroll.add_widget(self.order_grid)
        order_list_card.add_widget(self.order_scroll)

        # Action Buttons (Checkout & Print Receipt, Clear)
        action_box = BoxLayout(orientation="vertical", spacing=8, size_hint_y=None, height=96)
        
        btn_checkout = StyledButton(
            text="🖨️ CHECKOUT & PRINT RECEIPT",
            font_size="15sp",
            bg_color=(0.06, 0.72, 0.51, 1.0),
            size_hint_y=None,
            height=48
        )
        btn_checkout.bind(on_press=self.process_checkout)

        btn_clear = StyledButton(
            text="🗑️ CLEAR ALL ORDERS",
            font_size="13sp",
            bg_color=(0.75, 0.20, 0.20, 1.0),
            size_hint_y=None,
            height=38
        )
        btn_clear.bind(on_press=self.clear_orders)

        action_box.add_widget(btn_checkout)
        action_box.add_widget(btn_clear)
        order_list_card.add_widget(action_box)

        right_panel.add_widget(order_list_card)
        main_content.add_widget(right_panel)

        root.add_widget(main_content)

        # 3. Status Notification Bar
        self.status_bar = ColorCard(
            bg_color=(0.14, 0.10, 0.09, 1.0),
            orientation="horizontal",
            size_hint_y=None,
            height=40,
            padding=[12, 6]
        )
        self.status_lbl = Label(
            text="Ready. Select food items from the catalog or search to build order.",
            font_size="13sp",
            color=(0.06, 0.72, 0.51, 1.0),
            bold=True,
            halign="left",
            valign="middle"
        )
        self.status_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        self.status_bar.add_widget(self.status_lbl)
        root.add_widget(self.status_bar)

        # Initial Refresh
        self.refresh_catalog()
        self.refresh_order_display()

        return root

    def set_status(self, msg, msg_type="info"):
        colors = {
            "info": (0.06, 0.72, 0.51, 1.0),
            "success": (0.20, 0.85, 0.40, 1.0),
            "warning": (0.96, 0.62, 0.04, 1.0),
            "error": (0.94, 0.27, 0.27, 1.0),
        }
        self.status_lbl.text = msg
        self.status_lbl.color = colors.get(msg_type, (1, 1, 1, 1))

    def on_search_text_change(self, instance, value):
        self.search_query = value
        self.refresh_catalog()

    def select_category(self, category_name):
        self.current_category = category_name
        for cat, btn in self.cat_buttons.items():
            if cat == category_name:
                btn.bg_color = (0.96, 0.62, 0.04, 1.0)
                btn.color = (0.1, 0.1, 0.1, 1.0)
            else:
                btn.bg_color = (0.26, 0.20, 0.19, 1.0)
                btn.color = (0.90, 0.90, 0.90, 1.0)
            btn._update_rect(btn, None)
        self.refresh_catalog()

    def refresh_catalog(self):
        self.catalog_grid.clear_widgets()
        items = self.db.search_items(query=self.search_query, category=self.current_category)

        if not items:
            no_item_lbl = Label(
                text=f"No food items found matching '{self.search_query}' in category '{self.current_category}'.",
                color=(0.75, 0.75, 0.75, 1.0),
                font_size="14sp",
                size_hint_y=None,
                height=140,
                halign="center"
            )
            self.catalog_grid.add_widget(no_item_lbl)
            return

        for item in items:
            card = FoodCardWidget(item=item, on_add_callback=self.add_item_to_order, size_hint=(None, None), size=(230, 250))
            self.catalog_grid.add_widget(card)

    def add_item_to_order(self, item):
        item_id = item["id"]
        name = item["name"]
        price = float(item["price"])

        for order in self.orders:
            if order["item_id"] == item_id:
                order["quantity"] += 1
                order["cost"] = order["quantity"] * order["price"]
                self.set_status(f"Increased quantity of '{name}' to {order['quantity']}.", "success")
                break
        else:
            self.orders.append({
                "item_id": item_id,
                "name": name,
                "price": price,
                "quantity": 1,
                "cost": price
            })
            self.set_status(f"Added '{name}' (₦{price:,.2f}) to order.", "success")

        self.refresh_order_display()

    def adjust_order_quantity(self, order_item, delta):
        order_item["quantity"] += delta
        if order_item["quantity"] <= 0:
            self.orders.remove(order_item)
            self.set_status(f"Removed '{order_item['name']}' from order.", "warning")
        else:
            order_item["cost"] = order_item["quantity"] * order_item["price"]
            self.set_status(f"Updated '{order_item['name']}' quantity to {order_item['quantity']}.", "info")
        self.refresh_order_display()

    def remove_single_order_item(self, order_item):
        if order_item in self.orders:
            self.orders.remove(order_item)
            self.set_status(f"Removed '{order_item['name']}' from order.", "warning")
            self.refresh_order_display()

    def clear_orders(self, instance=None):
        if not self.orders:
            self.set_status("Order cart is already empty.", "info")
            return
        self.orders.clear()
        self.set_status("All order items have been cleared.", "warning")
        self.refresh_order_display()

    def refresh_order_display(self):
        self.order_grid.clear_widgets()
        total_balance = sum(o["cost"] for o in self.orders)
        self.total_val_lbl.text = f"₦{total_balance:,.2f}"
        self.cart_count_lbl.text = f"{sum(o['quantity'] for o in self.orders)} Item(s)"

        if not self.orders:
            empty_lbl = Label(
                text="Order cart is empty.\nClick '➕ ADD' on menu items to begin.",
                color=(0.7, 0.7, 0.7, 1.0),
                font_size="13sp",
                halign="center",
                size_hint_y=None,
                height=120
            )
            self.order_grid.add_widget(empty_lbl)
            return

        for order in self.orders:
            row = ColorCard(
                bg_color=(0.20, 0.16, 0.15, 1.0),
                border_color=(0.32, 0.25, 0.22, 1.0),
                orientation="horizontal",
                size_hint_y=None,
                height=54,
                padding=8,
                spacing=8
            )
            
            # Details column
            details = BoxLayout(orientation="vertical", spacing=2, size_hint_x=0.55)
            name_lbl = Label(
                text=order["name"],
                font_size="13sp",
                bold=True,
                color=(1, 1, 1, 1),
                halign="left",
                valign="middle"
            )
            name_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
            
            sub_lbl = Label(
                text=f"@ ₦{order['price']:,.2f} = ₦{order['cost']:,.2f}",
                font_size="12sp",
                color=(0.90, 0.80, 0.70, 1.0),
                halign="left",
                valign="middle"
            )
            sub_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
            details.add_widget(name_lbl)
            details.add_widget(sub_lbl)
            row.add_widget(details)

            # Quantity Adjustment Buttons (- Qty +)
            qty_box = BoxLayout(orientation="horizontal", spacing=4, size_hint_x=0.45)
            
            btn_minus = StyledButton(
                text="-",
                font_size="14sp",
                bg_color=(0.35, 0.25, 0.25, 1.0),
                size_hint=(None, None),
                size=(30, 30)
            )
            btn_minus.bind(on_press=lambda inst, o=order: self.adjust_order_quantity(o, -1))

            qty_lbl = Label(
                text=str(order["quantity"]),
                font_size="13sp",
                bold=True,
                color=(0.96, 0.62, 0.04, 1.0),
                size_hint_x=None,
                width=28,
                halign="center"
            )

            btn_plus = StyledButton(
                text="+",
                font_size="14sp",
                bg_color=(0.06, 0.72, 0.51, 1.0),
                size_hint=(None, None),
                size=(30, 30)
            )
            btn_plus.bind(on_press=lambda inst, o=order: self.adjust_order_quantity(o, 1))

            btn_del = StyledButton(
                text="✕",
                font_size="12sp",
                bg_color=(0.80, 0.20, 0.20, 1.0),
                size_hint=(None, None),
                size=(30, 30)
            )
            btn_del.bind(on_press=lambda inst, o=order: self.remove_single_order_item(o))

            qty_box.add_widget(btn_minus)
            qty_box.add_widget(qty_lbl)
            qty_box.add_widget(btn_plus)
            qty_box.add_widget(btn_del)
            row.add_widget(qty_box)

            self.order_grid.add_widget(row)

    def process_checkout(self, instance):
        if not self.orders:
            self.set_status("Cannot checkout with an empty cart!", "error")
            return

        customer_name = self.cust_input.text.strip() or "Walk-in Customer"
        payment_method = self.pay_spinner.text
        subtotal = sum(o["cost"] for o in self.orders)
        discount = 0.0
        total = subtotal - discount

        receipt_no = f"REC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Save receipt to SQLite database
        self.db.save_receipt(
            receipt_no=receipt_no,
            customer_name=customer_name,
            payment_method=payment_method,
            items=self.orders,
            subtotal=subtotal,
            discount=discount,
            total=total
        )

        # Open Receipt Modal Window
        self.show_receipt_popup(receipt_no, customer_name, payment_method, list(self.orders), subtotal, discount, total)
        self.set_status(f"Checkout completed! Receipt {receipt_no} generated.", "success")

    def show_receipt_popup(self, receipt_no, customer_name, payment_method, orders, subtotal, discount, total):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build Formatted Printable Receipt Text
        receipt_text = f"""
====================================================
               AKOMOLAFE FOOD CANTEEN
          Authentic Nigerian Delicacies
       12 Canteen Way, Victoria Island, Lagos
              Tel: +234 803 000 7788
====================================================
Receipt No: {receipt_no}
Date/Time : {now_str}
Customer  : {customer_name}
Payment   : {payment_method}
----------------------------------------------------
ITEM NAME                         QTY    TOTAL (NGN)
----------------------------------------------------
"""
        for o in orders:
            name_str = o["name"][:30].ljust(30)
            qty_str = f"x{o['quantity']}".rjust(5)
            cost_str = f"₦{o['cost']:,.2f}".rjust(12)
            receipt_text += f"{name_str} {qty_str} {cost_str}\n"

        receipt_text += f"""----------------------------------------------------
Subtotal  :                      ₦{subtotal:,.2f}
Discount  :                      ₦{discount:,.2f}
====================================================
TOTAL PAID:                      ₦{total:,.2f}
====================================================
     Thank you for dining at AKomolafe Canteen!
            Please visit us again soon!
====================================================
"""

        # Popup Content Window
        content = BoxLayout(orientation="vertical", padding=14, spacing=12)
        
        scroll = ScrollView()
        receipt_label = Label(
            text=receipt_text,
            font_size="14sp",
            color=(0.96, 0.62, 0.04, 1.0),
            size_hint_y=None,
            halign="left"
        )
        receipt_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(receipt_label)
        content.add_widget(scroll)

        btn_row = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=None, height=48)
        
        btn_print = StyledButton(
            text="🖨️ PRINT / SAVE RECEIPT FILE",
            font_size="14sp",
            bg_color=(0.06, 0.72, 0.51, 1.0)
        )
        
        btn_close = StyledButton(
            text="CLOSE & NEW ORDER",
            font_size="14sp",
            bg_color=(0.35, 0.35, 0.35, 1.0)
        )
        
        popup = Popup(
            title=f"📜 OFFICIAL RECEIPT - {receipt_no}",
            content=content,
            size_hint=(0.70, 0.88),
            auto_dismiss=False
        )

        def save_and_print(instance):
            receipts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            txt_file = os.path.join(receipts_dir, f"{receipt_no}.txt")
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(receipt_text)
            
            # HTML printable file
            html_file = os.path.join(receipts_dir, f"{receipt_no}.html")
            html_content = f"""<!DOCTYPE html>
<html>
<head>
<title>Receipt {receipt_no}</title>
<style>
body {{ font-family: 'Courier New', monospace; background: #fff; color: #000; padding: 20px; max-width: 400px; margin: auto; }}
h2, h4 {{ text-align: center; margin: 5px; }}
.line {{ border-top: 1px dashed #000; margin: 10px 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
td, th {{ text-align: left; padding: 5px 0; }}
.right {{ text-align: right; }}
</style>
</head>
<body>
<h2>AKOMOLAFE FOOD CANTEEN</h2>
<h4>Authentic Nigerian Delicacies</h4>
<p style="text-align:center; font-size: 12px;">12 Canteen Way, Victoria Island, Lagos<br>Tel: +234 803 000 7788</p>
<div class="line"></div>
<p><b>Receipt #:</b> {receipt_no}<br><b>Date:</b> {now_str}<br><b>Customer:</b> {customer_name}<br><b>Payment:</b> {payment_method}</p>
<div class="line"></div>
<table>
<tr><th>Item</th><th>Qty</th><th class="right">Total</th></tr>
"""
            for o in orders:
                html_content += f"<tr><td>{o['name']}</td><td>x{o['quantity']}</td><td class='right'>&#8358;{o['cost']:,.2f}</td></tr>\n"
            html_content += f"""</table>
<div class="line"></div>
<p>Subtotal: <span style="float:right;">&#8358;{subtotal:,.2f}</span></p>
<h3>TOTAL PAID: <span style="float:right;">&#8358;{total:,.2f}</span></h3>
<div class="line"></div>
<h4 style="text-align:center;">Thank you for dining with us!</h4>
</body>
</html>"""
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.set_status(f"Saved receipt file: receipts/{receipt_no}.txt", "success")
            popup.dismiss()
            self.orders.clear()
            self.refresh_order_display()

        btn_print.bind(on_press=save_and_print)
        btn_close.bind(on_press=lambda inst: (popup.dismiss(), self.orders.clear(), self.refresh_order_display()))

        btn_row.add_widget(btn_print)
        btn_row.add_widget(btn_close)
        content.add_widget(btn_row)

        popup.open()

    def open_inventory_modal(self, instance):
        """Open Inventory Box modal window with large legible inputs & controls."""
        content = BoxLayout(orientation="vertical", padding=14, spacing=12)

        # Title Label
        title_lbl = Label(
            text="📦 INVENTORY MANAGEMENT BOX",
            font_size="18sp",
            bold=True,
            color=(0.96, 0.62, 0.04, 1.0),
            size_hint_y=None,
            height=34
        )
        content.add_widget(title_lbl)

        # Form Card: Add New Item
        form_card = ColorCard(
            bg_color=(0.20, 0.15, 0.14, 1.0),
            orientation="vertical",
            padding=12,
            spacing=8,
            size_hint_y=None,
            height=240
        )
        form_card.add_widget(Label(text="➕ Add New Food Item to Database", font_size="15sp", bold=True, color=(0.06, 0.72, 0.51, 1.0), size_hint_y=None, height=24))

        # Row 1: Name & Category
        r1 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        name_in = TextInput(hint_text="Food Item Name (e.g. Ofada Rice)", multiline=False, size_hint_x=0.55, font_size="13sp", background_color=(0.28, 0.22, 0.21, 1), foreground_color=(1, 1, 1, 1))
        cat_spin = Spinner(text="Swallows & Soups", values=("Swallows & Soups", "Rice & Staples", "Proteins & Meat", "Drinks & Snacks"), size_hint_x=0.45, font_size="13sp", bold=True, background_color=(0.28, 0.22, 0.21, 1), color=(1, 1, 1, 1))
        r1.add_widget(name_in)
        r1.add_widget(cat_spin)
        form_card.add_widget(r1)

        # Row 2: Price & Image selector dropdown
        r2 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        price_in = TextInput(hint_text="Price in NGN (e.g. 1500)", multiline=False, input_filter="float", size_hint_x=0.35, font_size="13sp", background_color=(0.28, 0.22, 0.21, 1), foreground_color=(1, 1, 1, 1))
        
        # Get list of images in food-images directory
        available_images = ["No Image"]
        if os.path.exists(FOOD_IMAGES_DIR):
            img_files = sorted([f for f in os.listdir(FOOD_IMAGES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
            available_images.extend(img_files)

        img_spin = Spinner(text=available_images[1] if len(available_images) > 1 else "No Image", values=tuple(available_images), size_hint_x=0.65, font_size="12sp", background_color=(0.28, 0.22, 0.21, 1), color=(1, 1, 1, 1))
        r2.add_widget(price_in)
        r2.add_widget(img_spin)
        form_card.add_widget(r2)

        # Row 3: Description & Custom Image Path Input
        r3 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        desc_in = TextInput(hint_text="Short description...", multiline=False, size_hint_x=0.6, font_size="13sp", background_color=(0.28, 0.22, 0.21, 1), foreground_color=(1, 1, 1, 1))
        custom_img_in = TextInput(hint_text="Or enter custom image filepath", multiline=False, size_hint_x=0.4, font_size="12sp", background_color=(0.28, 0.22, 0.21, 1), foreground_color=(1, 1, 1, 1))
        r3.add_widget(desc_in)
        r3.add_widget(custom_img_in)
        form_card.add_widget(r3)

        # Row 4: Submit Button
        btn_save_item = StyledButton(
            text="💾 SAVE NEW FOOD ITEM TO DATABASE",
            font_size="13sp",
            bg_color=(0.06, 0.72, 0.51, 1.0),
            size_hint_y=None,
            height=40
        )
        form_card.add_widget(btn_save_item)
        content.add_widget(form_card)

        # Table of existing inventory items
        content.add_widget(Label(text="📋 Current Database Food Inventory", font_size="15sp", bold=True, color=(0.96, 0.62, 0.04, 1.0), size_hint_y=None, height=24))
        
        inv_scroll = ScrollView()
        inv_grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        inv_grid.bind(minimum_height=inv_grid.setter('height'))
        inv_scroll.add_widget(inv_grid)
        content.add_widget(inv_scroll)

        popup = Popup(
            title="📦 INVENTORY BOX - AKOMOLAFE CANTEEN",
            content=content,
            size_hint=(0.88, 0.92)
        )

        def refresh_inventory_list():
            inv_grid.clear_widgets()
            items = self.db.get_all_items()
            for it in items:
                row = ColorCard(
                    bg_color=(0.22, 0.17, 0.16, 1.0),
                    orientation="horizontal",
                    size_hint_y=None,
                    height=46,
                    padding=8,
                    spacing=8
                )
                
                # Image thumbnail if available
                img_path = it.get("image_path", "")
                if img_path and os.path.exists(img_path):
                    row.add_widget(Image(source=img_path, size_hint=(None, None), size=(40, 40)))
                else:
                    row.add_widget(Label(text="🖼️", font_size="16sp", size_hint=(None, None), size=(40, 40)))

                info_str = f"{it['name']}  |  {it['category']}  |  ₦{it['price']:,.2f}"
                item_lbl = Label(text=info_str, font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.75, halign="left")
                item_lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
                row.add_widget(item_lbl)

                btn_del_item = StyledButton(
                    text="🗑️ Delete",
                    font_size="12sp",
                    bg_color=(0.80, 0.20, 0.20, 1.0),
                    size_hint=(None, None),
                    size=(85, 34)
                )
                btn_del_item.bind(on_press=lambda inst, i_id=it['id']: (self.db.delete_food_item(i_id), refresh_inventory_list(), self.refresh_catalog()))
                row.add_widget(btn_del_item)

                inv_grid.add_widget(row)

        def save_item_action(instance):
            name = name_in.text.strip()
            cat = cat_spin.text
            price_text = price_in.text.strip()
            desc = desc_in.text.strip()
            
            if not name:
                self.set_status("Please enter a valid item name!", "error")
                return
            try:
                price = float(price_text)
                if price <= 0:
                    raise ValueError()
            except ValueError:
                self.set_status("Please enter a valid price greater than 0!", "error")
                return

            custom_path = custom_img_in.text.strip()
            if custom_path and os.path.exists(custom_path):
                img_path = custom_path
            elif img_spin.text != "No Image":
                img_path = os.path.join(FOOD_IMAGES_DIR, img_spin.text)
            else:
                img_path = ""

            self.db.add_food_item(name=name, category=cat, price=price, image_path=img_path, description=desc)
            name_in.text = ""
            price_in.text = ""
            desc_in.text = ""
            custom_img_in.text = ""
            
            refresh_inventory_list()
            self.refresh_catalog()
            self.set_status(f"Added new item '{name}' (₦{price:,.2f}) to inventory DB!", "success")

        btn_save_item.bind(on_press=save_item_action)
        refresh_inventory_list()

        btn_close_inv = StyledButton(text="CLOSE INVENTORY BOX", font_size="13sp", bg_color=(0.35, 0.35, 0.35, 1.0), size_hint_y=None, height=42)
        btn_close_inv.bind(on_press=popup.dismiss)
        content.add_widget(btn_close_inv)

        popup.open()

    def open_sales_history_modal(self, instance):
        """Open Sales Receipts History Popup."""
        content = BoxLayout(orientation="vertical", padding=14, spacing=12)
        content.add_widget(Label(text="📜 PAST SALES RECEIPTS LOG", font_size="18sp", bold=True, color=(0.96, 0.62, 0.04, 1.0), size_hint_y=None, height=34))

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        scroll.add_widget(grid)
        content.add_widget(scroll)

        receipts = self.db.get_all_receipts(limit=30)
        if not receipts:
            grid.add_widget(Label(text="No sales recorded yet.", font_size="14sp", color=(0.7, 0.7, 0.7, 1), size_hint_y=None, height=60))
        else:
            for r in receipts:
                row = ColorCard(bg_color=(0.20, 0.16, 0.15, 1.0), orientation="horizontal", size_hint_y=None, height=48, padding=8, spacing=8)
                txt = f"{r['receipt_no']}  |  {r['timestamp']}  |  Customer: {r['customer_name']}  |  Total: ₦{r['total']:,.2f}"
                lbl = Label(text=txt, font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.88, halign="left")
                lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
                row.add_widget(lbl)
                grid.add_widget(row)

        btn_close = StyledButton(text="CLOSE LOG", font_size="13sp", bg_color=(0.35, 0.35, 0.35, 1.0), size_hint_y=None, height=42)
        popup = Popup(title="📜 SALES HISTORY", content=content, size_hint=(0.85, 0.85))
        btn_close.bind(on_press=popup.dismiss)
        content.add_widget(btn_close)
        popup.open()

    def open_invoice_modal(self, instance):
        """Open Invoice Generation Modal Window."""
        content = BoxLayout(orientation="vertical", padding=14, spacing=12)
        
        # Title
        title_lbl = Label(
            text="📄 GENERATE PROFESSIONAL INVOICE",
            font_size="18sp",
            bold=True,
            color=(0.96, 0.62, 0.04, 1.0),
            size_hint_y=None,
            height=34
        )
        content.add_widget(title_lbl)

        # Invoice Form Card
        form_card = ColorCard(
            bg_color=(0.20, 0.15, 0.14, 1.0),
            orientation="vertical",
            padding=12,
            spacing=8,
            size_hint_y=None,
            height=300
        )
        form_card.add_widget(Label(text="📋 Invoice Details", font_size="15sp", bold=True, color=(0.06, 0.72, 0.51, 1.0), size_hint_y=None, height=24))

        # Customer Information Row
        r1 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        r1.add_widget(Label(text="Customer Name:", font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.3))
        invoice_customer_input = TextInput(
            hint_text="e.g. Acme Corporation",
            text=self.cust_input.text if self.cust_input.text != "Walk-in Customer" else "",
            multiline=False,
            font_size="13sp",
            background_color=(0.28, 0.22, 0.21, 1),
            foreground_color=(1, 1, 1, 1),
            size_hint_x=0.7
        )
        r1.add_widget(invoice_customer_input)
        form_card.add_widget(r1)

        # Email & Phone Row
        r2 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        r2.add_widget(Label(text="Email:", font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.3))
        invoice_email_input = TextInput(
            hint_text="customer@example.com",
            multiline=False,
            font_size="13sp",
            background_color=(0.28, 0.22, 0.21, 1),
            foreground_color=(1, 1, 1, 1),
            size_hint_x=0.7
        )
        r2.add_widget(invoice_email_input)
        form_card.add_widget(r2)

        # Phone & Tax Row
        r3 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        r3.add_widget(Label(text="Phone:", font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.3))
        invoice_phone_input = TextInput(
            hint_text="+234 803 000 0000",
            multiline=False,
            font_size="13sp",
            background_color=(0.28, 0.22, 0.21, 1),
            foreground_color=(1, 1, 1, 1),
            size_hint_x=0.7
        )
        r3.add_widget(invoice_phone_input)
        form_card.add_widget(r3)

        # Tax & Discount Row
        r4 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        r4.add_widget(Label(text="Tax (%):", font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.3))
        invoice_tax_input = TextInput(
            text="0",
            multiline=False,
            input_filter="float",
            font_size="13sp",
            background_color=(0.28, 0.22, 0.21, 1),
            foreground_color=(1, 1, 1, 1),
            size_hint_x=0.35
        )
        r4.add_widget(invoice_tax_input)
        r4.add_widget(Label(text="Discount (%):", font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.3))
        invoice_discount_input = TextInput(
            text="0",
            multiline=False,
            input_filter="float",
            font_size="13sp",
            background_color=(0.28, 0.22, 0.21, 1),
            foreground_color=(1, 1, 1, 1),
            size_hint_x=0.35
        )
        r4.add_widget(invoice_discount_input)
        form_card.add_widget(r4)

        # Due Date & Payment Row
        r5 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=38)
        r5.add_widget(Label(text="Due Date:", font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.3))
        invoice_due_date_input = TextInput(
            hint_text="YYYY-MM-DD",
            text=(datetime.now().strftime("%Y-%m-%d")),
            multiline=False,
            font_size="13sp",
            background_color=(0.28, 0.22, 0.21, 1),
            foreground_color=(1, 1, 1, 1),
            size_hint_x=0.35
        )
        r5.add_widget(invoice_due_date_input)
        r5.add_widget(Label(text="Status:", font_size="13sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.3))
        invoice_status_spinner = Spinner(
            text="Pending",
            values=("Pending", "Paid", "Overdue", "Cancelled"),
            font_size="13sp",
            bold=True,
            background_color=(0.28, 0.22, 0.21, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.35
        )
        r5.add_widget(invoice_status_spinner)
        form_card.add_widget(r5)

        content.add_widget(form_card)

        # Order Items Summary
        content.add_widget(Label(text="📋 Current Cart Items (will be included in invoice)", font_size="14sp", bold=True, color=(0.96, 0.62, 0.04, 1.0), size_hint_y=None, height=24))
        
        items_scroll = ScrollView()
        items_grid = GridLayout(cols=1, spacing=6, size_hint_y=None)
        items_grid.bind(minimum_height=items_grid.setter('height'))
        
        total_invoice_value = sum(o["cost"] for o in self.orders)
        
        if not self.orders:
            items_grid.add_widget(Label(text="No items in cart. Please add items first before generating invoice.", font_size="13sp", color=(0.75, 0.75, 0.75, 1), size_hint_y=None, height=60))
        else:
            for order in self.orders:
                item_row = Label(
                    text=f"• {order['name']} (x{order['quantity']}) = ₦{order['cost']:,.2f}",
                    font_size="13sp",
                    color=(1, 1, 1, 1),
                    size_hint_y=None,
                    height=28,
                    halign="left"
                )
                item_row.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
                items_grid.add_widget(item_row)

        items_scroll.add_widget(items_grid)
        content.add_widget(items_scroll)

        # Buttons
        btn_box = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=None, height=48)
        
        btn_generate = StyledButton(
            text="✅ GENERATE & SAVE INVOICE",
            font_size="14sp",
            bg_color=(0.06, 0.72, 0.51, 1.0)
        )
        
        btn_close_invoice = StyledButton(
            text="CLOSE",
            font_size="14sp",
            bg_color=(0.35, 0.35, 0.35, 1.0)
        )

        popup = Popup(
            title="📄 GENERATE INVOICE",
            content=content,
            size_hint=(0.82, 0.90),
            auto_dismiss=False
        )

        def generate_invoice_action(instance):
            if not self.orders:
                self.set_status("Cannot generate invoice with empty cart!", "error")
                return

            customer_name = invoice_customer_input.text.strip() or "Walk-in Customer"
            customer_email = invoice_email_input.text.strip()
            customer_phone = invoice_phone_input.text.strip()
            payment_method = self.pay_spinner.text
            
            try:
                tax_percent = float(invoice_tax_input.text.strip() or "0")
                discount_percent = float(invoice_discount_input.text.strip() or "0")
            except ValueError:
                self.set_status("Invalid tax or discount percentage!", "error")
                return

            due_date = invoice_due_date_input.text.strip() or (datetime.now().strftime("%Y-%m-%d"))
            status = invoice_status_spinner.text

            subtotal = sum(o["cost"] for o in self.orders)
            tax_amount = (subtotal * tax_percent) / 100
            discount_amount = (subtotal * discount_percent) / 100
            total = subtotal + tax_amount - discount_amount

            invoice_no = self.db.get_next_invoice_number()

            # Save to database
            self.db.save_invoice(
                invoice_no=invoice_no,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                payment_method=payment_method,
                items=list(self.orders),
                subtotal=subtotal,
                tax=tax_amount,
                discount=discount_amount,
                total=total,
                due_date=due_date,
                status=status
            )

            # Show Invoice Preview & Save
            self.show_invoice_popup(invoice_no, customer_name, customer_email, customer_phone, payment_method, list(self.orders), subtotal, tax_amount, discount_amount, total, due_date, status)
            
            popup.dismiss()
            self.set_status(f"Invoice {invoice_no} generated successfully!", "success")

        btn_generate.bind(on_press=generate_invoice_action)
        btn_close_invoice.bind(on_press=popup.dismiss)

        btn_box.add_widget(btn_generate)
        btn_box.add_widget(btn_close_invoice)
        content.add_widget(btn_box)

        popup.open()

    def show_invoice_popup(self, invoice_no, customer_name, customer_email, customer_phone, payment_method, orders, subtotal, tax, discount, total, due_date, status):
        """Display formatted invoice preview and save options."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build Formatted Invoice Text
        invoice_text = f"""
╔═══════════════════════════════════════════════════════════╗
║             AKOMOLAFE FOOD CANTEEN                         ║
║          Authentic Nigerian Delicacies                    ║
║       12 Canteen Way, Victoria Island, Lagos              ║
║              Tel: +234 803 000 7788                       ║
╚═══════════════════════════════════════════════════════════╝

PROFESSIONAL INVOICE

Invoice No    : {invoice_no}
Invoice Date  : {now_str}
Due Date      : {due_date}
Status        : {status}

─────────────────────────────────────────────────────────────
BILL TO:
─────────────────────────────────────────────────────────────
Customer Name : {customer_name}
Email         : {customer_email if customer_email else 'N/A'}
Phone         : {customer_phone if customer_phone else 'N/A'}
Payment Method: {payment_method}

─────────────────────────────────────────────────────────────
INVOICE ITEMS
─────────────────────────────────────────────────────────────
Item Description                    Qty      Unit Price    Total
─────────────────────────────────────────────────────────────
"""
        for o in orders:
            name_str = o["name"][:35].ljust(35)
            qty_str = f"x{o['quantity']}".rjust(5)
            price_str = f"₦{o['price']:,.2f}".rjust(12)
            cost_str = f"₦{o['cost']:,.2f}".rjust(12)
            invoice_text += f"{name_str} {qty_str} {price_str} {cost_str}\n"

        invoice_text += f"""─────────────────────────────────────────────────────────────
                                    Subtotal: ₦{subtotal:,.2f}
                                        Tax: ₦{tax:,.2f}
                                   Discount: ₦{discount:,.2f}
═════════════════════════════════════════════════════════════
                                  TOTAL DUE: ₦{total:,.2f}
═════════════════════════════════════════════════════════════

Payment Terms: Due by {due_date}
Invoice Status: {status}

Thank you for your business!
AKOMOLAFE FOOD CANTEEN
═════════════════════════════════════════════════════════════
"""

        # Popup Content
        content = BoxLayout(orientation="vertical", padding=14, spacing=12)
        
        scroll = ScrollView()
        invoice_label = Label(
            text=invoice_text,
            font_size="12sp",
            color=(0.96, 0.62, 0.04, 1.0),
            size_hint_y=None,
            halign="left"
        )
        invoice_label.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(invoice_label)
        content.add_widget(scroll)

        btn_row = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=None, height=48)
        
        btn_save = StyledButton(
            text="💾 SAVE INVOICE FILE",
            font_size="14sp",
            bg_color=(0.06, 0.72, 0.51, 1.0)
        )
        
        btn_close = StyledButton(
            text="DONE",
            font_size="14sp",
            bg_color=(0.35, 0.35, 0.35, 1.0)
        )
        
        popup = Popup(
            title=f"📄 PROFESSIONAL INVOICE - {invoice_no}",
            content=content,
            size_hint=(0.75, 0.90),
            auto_dismiss=False
        )

        def save_invoice_files(instance):
            invoices_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")
            os.makedirs(invoices_dir, exist_ok=True)
            
            # Save as TXT file
            txt_file = os.path.join(invoices_dir, f"{invoice_no}.txt")
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(invoice_text)
            
            # Save as HTML file
            html_file = os.path.join(invoices_dir, f"{invoice_no}.html")
            html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Invoice {invoice_no}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
.invoice-container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
.header {{ text-align: center; border-bottom: 3px solid #d4a574; padding-bottom: 20px; margin-bottom: 30px; }}
.header h1 {{ color: #c68642; font-size: 28px; margin-bottom: 5px; }}
.header p {{ color: #666; font-size: 14px; margin: 5px 0; }}
.invoice-details {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
.detail-box {{ border-left: 3px solid #d4a574; padding-left: 15px; }}
.detail-box .label {{ font-weight: bold; color: #333; font-size: 12px; text-transform: uppercase; margin-bottom: 5px; }}
.detail-box .value {{ color: #666; font-size: 14px; }}
.bill-to {{ grid-column: 1 / 2; }}
.invoice-meta {{ grid-column: 2 / 4; }}
.items-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; }}
.items-table th {{ background: #f0f0f0; border-top: 2px solid #d4a574; border-bottom: 2px solid #d4a574; padding: 12px; text-align: left; font-weight: bold; color: #333; font-size: 13px; }}
.items-table td {{ padding: 12px; border-bottom: 1px solid #eee; font-size: 14px; }}
.items-table tr:last-child td {{ border-bottom: 2px solid #d4a574; }}
.text-right {{ text-align: right; }}
.summary {{ display: grid; grid-template-columns: 1fr 200px; gap: 20px; margin: 30px 0; }}
.summary-items {{ grid-column: 2; }}
.summary-row {{ display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px; border-bottom: 1px solid #eee; }}
.summary-row.total {{ border-top: 2px solid #d4a574; border-bottom: 2px solid #d4a574; padding: 12px 0; font-size: 18px; font-weight: bold; color: #c68642; }}
.terms {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
.footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #999; }}
</style>
</head>
<body>
<div class="invoice-container">
    <div class="header">
        <h1>🍲 AKOMOLAFE FOOD CANTEEN</h1>
        <p>Authentic Nigerian Delicacies</p>
        <p>12 Canteen Way, Victoria Island, Lagos | Tel: +234 803 000 7788</p>
    </div>

    <div class="invoice-details">
        <div class="detail-box bill-to">
            <div class="label">Bill To:</div>
            <div class="value">
                <strong>{customer_name}</strong><br>
                {f'Email: {customer_email}<br>' if customer_email else ''}
                {f'Phone: {customer_phone}' if customer_phone else ''}
            </div>
        </div>
        <div class="detail-box invoice-meta">
            <div class="label">Invoice Number:</div>
            <div class="value"><strong>{invoice_no}</strong></div>
        </div>
        <div class="detail-box invoice-meta">
            <div class="label">Invoice Date:</div>
            <div class="value">{now_str}</div>
        </div>
        <div class="detail-box invoice-meta">
            <div class="label">Due Date:</div>
            <div class="value">{due_date}</div>
        </div>
        <div class="detail-box invoice-meta">
            <div class="label">Payment Method:</div>
            <div class="value">{payment_method}</div>
        </div>
        <div class="detail-box invoice-meta">
            <div class="label">Status:</div>
            <div class="value"><strong style="color: {'#c68642' if status == 'Pending' else '#06b833' if status == 'Paid' else '#d32f2f'};">{status}</strong></div>
        </div>
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th>Item Description</th>
                <th class="text-right">Quantity</th>
                <th class="text-right">Unit Price</th>
                <th class="text-right">Total</th>
            </tr>
        </thead>
        <tbody>
"""
            for o in orders:
                html_content += f"""            <tr>
                <td>{o['name']}</td>
                <td class="text-right">x{o['quantity']}</td>
                <td class="text-right">₦{o['price']:,.2f}</td>
                <td class="text-right">₦{o['cost']:,.2f}</td>
            </tr>
"""
            html_content += f"""        </tbody>
    </table>

    <div class="summary">
        <div></div>
        <div class="summary-items">
            <div class="summary-row">
                <span>Subtotal:</span>
                <span>₦{subtotal:,.2f}</span>
            </div>
            <div class="summary-row">
                <span>Tax ({(tax/(subtotal if subtotal > 0 else 1) * 100):.1f}%):</span>
                <span>₦{tax:,.2f}</span>
            </div>
            <div class="summary-row">
                <span>Discount ({(discount/(subtotal if subtotal > 0 else 1) * 100):.1f}%):</span>
                <span>-₦{discount:,.2f}</span>
            </div>
            <div class="summary-row total">
                <span>TOTAL DUE:</span>
                <span>₦{total:,.2f}</span>
            </div>
        </div>
    </div>

    <div class="terms">
        <p><strong>Payment Terms:</strong> Due by {due_date}</p>
        <p><strong>Invoice Status:</strong> {status}</p>
    </div>

    <div class="footer">
        <p>Thank you for your business at Akomolafe Food Canteen!</p>
        <p>This is a computer-generated invoice. No signature required.</p>
    </div>
</div>
</body>
</html>"""
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.set_status(f"Invoice {invoice_no} saved! Files: invoices/{invoice_no}.txt & .html", "success")
            popup.dismiss()

        btn_save.bind(on_press=save_invoice_files)
        btn_close.bind(on_press=popup.dismiss)

        btn_row.add_widget(btn_save)
        btn_row.add_widget(btn_close)
        content.add_widget(btn_row)

        popup.open()

    def confirm_reset_menu(self, instance):
        content = BoxLayout(orientation="vertical", padding=14, spacing=12)
        content.add_widget(Label(text="Are you sure you want to reset all food items in the database to the default Nigerian Menu?", font_size="14sp", bold=True, color=(1, 1, 1, 1), halign="center"))
        btn_box = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=None, height=42)
        btn_yes = StyledButton(text="YES, RESET MENU", font_size="13sp", bg_color=(0.80, 0.20, 0.20, 1.0))
        btn_no = StyledButton(text="NO, CANCEL", font_size="13sp", bg_color=(0.35, 0.35, 0.35, 1.0))
        btn_box.add_widget(btn_yes)
        btn_box.add_widget(btn_no)
        content.add_widget(btn_box)

        popup = Popup(title="⚠️ CONFIRM MENU RESET", content=content, size_hint=(0.55, 0.38))
        
        def do_reset(inst):
            self.db.reset_to_default_menu()
            self.refresh_catalog()
            self.set_status("Reset database menu to default Nigerian canteen items!", "success")
            popup.dismiss()

        btn_yes.bind(on_press=do_reset)
        btn_no.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    AKomolafeCanteenApp().run()
