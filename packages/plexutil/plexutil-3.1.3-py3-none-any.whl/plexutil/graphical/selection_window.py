import tkinter as tk
from tkinter import StringVar, ttk

from ttkthemes import ThemedTk

from plexutil.dto.dropdown_item_dto import DropdownItemDTO


class SelectionWindow:
    def __init__(
        self,
        items: list[DropdownItemDTO],
        items_label: str = "items",
        recipient_label: str = "recipient",
        list_title: str = "Available",
        command: str = "Add",
        default_width: int = 500,
        default_height: int = 750,
    ) -> None:
        self.root = ThemedTk(theme="arc")
        self.items = [x.display_name for x in items]
        self.original_items = items
        self.items_label = items_label
        self.recipient_label = recipient_label
        self.list_title = list_title
        self.command = command
        self.root.title(f"Select {self.items_label}")
        self.root.geometry(f"{default_width!s}x{default_height!s}")

        self.all_items = self.items[:]
        self.filtered_items = self.items[:]
        self.added_items = []  # Track added items

        # Variables
        self.search_var = StringVar()
        self.selected_var = StringVar(value=f"0 {self.items_label} selected")
        self.added_var = StringVar(value=f"0 {self.items_label} added")

        # Create styles
        style = ttk.Style()
        style.configure("Selected.TLabel", foreground="green")

        # Create widgets
        self.create_widgets()

        # Populate initial list
        self.update_listbox()

        # Bind events
        self.search_var.trace("w", lambda *args: self.filter_list())  # noqa: ARG005
        self.tree.bind("<<TreeviewSelect>>", self.update_status)
        self.added_tree.bind("<<TreeviewSelect>>", self.update_added_status)

        # Focus
        self.search_entry.focus()

    def start(self) -> None:
        self.root.mainloop()

    def create_widgets(self) -> None:
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(
            main_frame,
            text=f"Search and Select {self.items_label}",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor=tk.W, pady=(0, 10))

        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(
            search_frame, textvariable=self.search_var, width=40
        )
        self.search_entry.pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        ttk.Button(
            search_frame, text="Clear", command=self.clear_search, width=8
        ).pack(side=tk.RIGHT)

        # Available items section
        available_label = ttk.Label(
            main_frame,
            text=f"{self.list_title} {self.items_label}",
            font=("Segoe UI", 11, "bold"),
        )
        available_label.pack(anchor=tk.W, pady=(0, 5))

        # Treeview with scrollbars (top)
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame, selectmode="extended", height=10, show="tree"
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree.yview
        )
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        # Button frame for available items
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="Select All", command=self.select_all).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(
            btn_frame, text="Clear Selection", command=self.clear_selection
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            btn_frame,
            text="Select →",
            command=self.add_selected,
            style="Accent.TButton",
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # Status bar for available items
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 15))

        self.status_label = ttk.Label(
            status_frame, textvariable=self.selected_var
        )
        self.status_label.pack(side=tk.LEFT)
        self.total_label = ttk.Label(
            status_frame,
            text=f"Total: {len(self.all_items)} {self.items_label}",
        )
        self.total_label.pack(side=tk.RIGHT)

        # Separator
        ttk.Separator(main_frame, orient="horizontal").pack(
            fill=tk.X, pady=(0, 15)
        )

        # Added items section
        added_label = ttk.Label(
            main_frame,
            text=f"Selected {self.items_label} | {self.recipient_label}",
            font=("Segoe UI", 11, "bold"),
        )
        added_label.pack(anchor=tk.W, pady=(0, 5))

        # Added items treeview
        added_tree_frame = ttk.Frame(main_frame)
        added_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.added_tree = ttk.Treeview(
            added_tree_frame, selectmode="extended", height=8, show="tree"
        )
        self.added_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar for added items
        added_v_scrollbar = ttk.Scrollbar(
            added_tree_frame, orient="vertical", command=self.added_tree.yview
        )
        added_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.added_tree.configure(yscrollcommand=added_v_scrollbar.set)

        # Button frame for added items
        added_btn_frame = ttk.Frame(main_frame)
        added_btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            added_btn_frame,
            text="Remove Selected",
            command=self.remove_selected,
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            added_btn_frame, text="Clear All", command=self.clear_added
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            added_btn_frame,
            text=f"{self.command} {self.items_label}",
            command=self.root.destroy,
            style="Accent.TButton",
        ).pack(side=tk.RIGHT, ipadx=20)

        # Status bar for added items
        added_status_frame = ttk.Frame(main_frame)
        added_status_frame.pack(fill=tk.X, pady=(0, 15))

        self.added_status_label = ttk.Label(
            added_status_frame, textvariable=self.added_var
        )
        self.added_status_label.pack(side=tk.LEFT)

    def filter_list(self) -> None:
        search_text = self.search_var.get().lower()
        if not search_text:
            self.filtered_items = [
                item for item in self.all_items if item not in self.added_items
            ]
        else:
            self.filtered_items = [
                item
                for item in self.all_items
                if search_text in item.lower() and item not in self.added_items
            ]
        self.update_listbox()

    def update_listbox(self) -> None:
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add items (excluding added items)
        for i, item in enumerate(self.filtered_items, 1):
            self.tree.insert("", "end", iid=str(i), text=item, values=(item,))

        self.update_status()
        self.update_total_label()

    def update_added_listbox(self) -> None:
        # Clear added tree
        for item in self.added_tree.get_children():
            self.added_tree.delete(item)

        # Add items to added list
        for i, item in enumerate(self.added_items, 1):
            self.added_tree.insert(
                "", "end", iid=f"added_{i}", text=item, values=(item,)
            )

        self.update_added_status()

    def add_selected(self) -> None:
        selected_items = [
            self.tree.item(i)["text"] for i in self.tree.selection()
        ]

        if not selected_items:
            return

        # Add to added_items list
        for item in selected_items:
            if item not in self.added_items:
                self.added_items.append(item)

        # Update both lists
        self.filter_list()
        self.update_added_listbox()

    def remove_selected(self) -> None:
        selected_items = [
            self.added_tree.item(i)["text"]
            for i in self.added_tree.selection()
        ]

        if not selected_items:
            return

        # Remove from added_items list
        for item in selected_items:
            if item in self.added_items:
                self.added_items.remove(item)

        # Update both lists
        self.filter_list()
        self.update_added_listbox()

    def clear_added(self) -> None:
        self.added_items.clear()
        self.filter_list()
        self.update_added_listbox()

    def clear_search(self) -> None:
        self.search_var.set("")
        self.search_entry.focus()

    def select_all(self) -> None:
        self.tree.selection_set(self.tree.get_children())

    def clear_selection(self) -> None:
        self.tree.selection_remove(self.tree.get_children())

    def get_selections(self) -> list[DropdownItemDTO]:
        added_items = []
        for item in self.original_items:
            for added_item in self.added_items:
                if added_item.lower() == item.display_name.lower():
                    added_items.append(item)  # noqa: PERF401
        return added_items

    def update_status(self, event: tk.Event | None = None) -> None:  # noqa: ARG002
        selected_count = len(self.tree.selection())
        total_count = len(self.filtered_items)
        self.selected_var.set(
            f"{selected_count} of {total_count} {self.items_label} selected"
        )

    def update_added_status(self, event: tk.Event | None = None) -> None:  # noqa: ARG002
        selected_count = len(self.added_tree.selection())
        total_count = len(self.added_items)
        self.added_var.set(
            f"{selected_count} of {total_count} {self.items_label} selected"
        )

    def update_total_label(self) -> None:
        available_count = len(
            [item for item in self.all_items if item not in self.added_items]
        )
        self.total_label.config(
            text=f"Total: {available_count} {self.items_label}"
        )
