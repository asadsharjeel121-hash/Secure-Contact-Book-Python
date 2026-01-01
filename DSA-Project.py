"""Contact Book Application"""

import csv
import os
import base64
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List
CSV_FILE = "contacts.csv"
XOR_KEY = "my_secret_key_123"
def xor_encrypt_to_b64(data: str, key: str = XOR_KEY) -> str:
    if data is None:
        return ""
    encoded = data.encode("utf-8")
    key_bytes = key.encode("utf-8")
    cipher = bytearray()
    for i, v in enumerate(encoded):
        cipher.append(v ^ key_bytes[i % len(key_bytes)])
    return base64.b64encode(bytes(cipher)).decode("utf-8")
def xor_decrypt_from_b64(b64text: str, key: str = XOR_KEY) -> str:
    if not b64text:
        return ""
    try:
        cipher = base64.b64decode(b64text)
    except Exception:
        return ""
    key_bytes = key.encode("utf-8")
    data = bytearray()
    for i, b in enumerate(cipher):
        data.append(b ^ key_bytes[i % len(key_bytes)])
    try:
        return data.decode("utf-8")
    except Exception:
        return ""

class Contact:
    def __init__(self, name: str, phone: str, email: str, address: str):
        self.name = name.strip()
        self.phone = phone.strip()
        self._enc_email = xor_encrypt_to_b64(email or "")
        self._enc_address = xor_encrypt_to_b64(address or "")

    @property
    def email(self):
        return xor_decrypt_from_b64(self._enc_email)

    @email.setter
    def email(self, new_email: str):
        self._enc_email = xor_encrypt_to_b64(new_email or "")

    @property
    def address(self):
        return xor_decrypt_from_b64(self._enc_address)

    @address.setter
    def address(self, new_address: str):
        self._enc_address = xor_encrypt_to_b64(new_address or "")

    def update(self, phone=None, email=None, address=None, name=None):
        if name is not None:
            self.name = name.strip()
        if phone is not None:
            self.phone = phone.strip()
        if email is not None:
            self.email = email
        if address is not None:
            self.address = address

    def to_csv_row(self):
        return [self.name, self.phone, self._enc_email, self._enc_address]

    @staticmethod
    def from_csv_row(row: List[str]):
        name, phone = row[0], row[1]
        c = Contact(name, phone, "", "")
        c._enc_email = row[2] if len(row) > 2 else xor_encrypt_to_b64("")
        c._enc_address = row[3] if len(row) > 3 else xor_encrypt_to_b64("")
        return c

    def __str__(self):
        return (
            f"Name: {self.name}\nPhone: {self.phone}\n"
            f"Email: {self.email}\nAddress: {self.address}"
        )

class ContactManager:
    def __init__(self):
        self.contacts: Dict[str, Contact] = {}
        self.load_from_csv()

    def add_contact(self, contact: Contact):
        if contact.phone in self.contacts:
            return False
        self.contacts[contact.phone] = contact
        return True

    def get_all_contacts_sorted_by_name(self):
        return sorted(self.contacts.values(), key=lambda c: c.name.lower())

    def get_all_contacts_sorted_by_phone_radix(self):
        phones = list(self.contacts.keys())
        sorted_phones = radix_sort_phone_strings(phones)
        return [self.contacts[p] for p in sorted_phones]

    def find_by_phone(self, phone):
        return self.contacts.get(phone)

    def update_contact(self, old_phone, new_contact: Contact):
        if old_phone not in self.contacts:
            return False
        if new_contact.phone != old_phone and new_contact.phone in self.contacts:
            return False
        del self.contacts[old_phone]
        self.contacts[new_contact.phone] = new_contact
        return True

    def delete_contact(self, phone):
        return self.contacts.pop(phone, None) is not None

    def load_from_csv(self, filename=CSV_FILE):
        self.contacts.clear()
        if not os.path.exists(filename):
            return
        try:
            with open(filename, encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    return
                start = 1 if rows[0][0].strip().lower() == "name" else 0
                for r in rows[start:]:
                    if len(r) >= 2:
                        c = Contact.from_csv_row(r)
                        self.contacts[c.phone] = c
        except Exception as e:
            print("Failed to load CSV:", e)

    def save_to_csv(self, filename=CSV_FILE):
        try:
            with open(filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Phone", "EncEmail", "EncAddress"])
                for c in self.contacts.values():
                    writer.writerow(c.to_csv_row())
        except Exception as e:
            print("Failed to save CSV:", e)


def sanitize_phone_for_sort(phone: str):
    return "".join(ch for ch in phone if ch.isdigit())


def radix_sort_phone_strings(phones: List[str]):
    if not phones:
        return []
    keyed = [(p, sanitize_phone_for_sort(p)) for p in phones]
    if all(k == "" for _, k in keyed):
        return [p for p, _ in keyed]

    max_len = max(len(k) for _, k in keyed)
    padded = [(orig, k.zfill(max_len)) for orig, k in keyed]

    for i in range(max_len - 1, -1, -1):
        buckets = {str(d): [] for d in range(10)}
        for orig, pstr in padded:
            buckets[pstr[i]].append((orig, pstr))
        padded = [pair for d in range(10) for pair in buckets[str(d)]]

    return [orig for orig, _ in padded]

class ContactApp:
    def __init__(self, root, manager: ContactManager):
        self.root = root
        self.manager = manager
        self.root.title("Contact Book")
        self.create_widgets()
        self.refresh_treeview()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add Contact", command=self.gui_add_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update Selected", command=self.gui_update_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.gui_delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Search by Phone", command=self.gui_search_by_phone).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="View Sorted (Name)", command=self.refresh_treeview).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="View Sorted (Phone Radix)", command=lambda: self.refresh_treeview(True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save & Exit", command=self.on_exit).pack(side=tk.RIGHT, padx=5)

        cols = ("Name", "Phone", "Email", "Address")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_treeview(self, by_phone=False):
        for row in self.tree.get_children():
            self.tree.delete(row)
        contacts = (
            self.manager.get_all_contacts_sorted_by_phone_radix()
            if by_phone else
            self.manager.get_all_contacts_sorted_by_name()
        )
        for c in contacts:
            self.tree.insert("", tk.END, values=(c.name, c.phone, c.email, c.address))

    def gui_add_contact(self):
        dialog = ContactDialog(self.root, "Add Contact")
        if dialog.result:
            name, phone, email, address = dialog.result
            ok = self.manager.add_contact(Contact(name, phone, email, address))
            if ok:
                self.refresh_treeview()
            else:
                messagebox.showerror("Error", f"Phone {phone} already exists.")

    def gui_update_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a contact to update.")
            return
        vals = self.tree.item(sel[0], "values")
        phone = vals[1]
        contact = self.manager.find_by_phone(phone)
        if not contact:
            messagebox.showerror("Error", "Contact not found.")
            self.refresh_treeview()
            return

        dialog = ContactDialog(self.root, "Update Contact", (contact.name, contact.phone, contact.email, contact.address))
        if dialog.result:
            new_name, new_phone, new_email, new_address = dialog.result
            new_contact = Contact(new_name, new_phone, new_email, new_address)
            ok = self.manager.update_contact(phone, new_contact)
            if ok:
                self.refresh_treeview()
            else:
                messagebox.showerror("Error", "Failed to update.")

    def gui_delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        name, phone = vals[0], vals[1]
        if messagebox.askyesno("Confirm", f"Delete {name} ({phone})?"):
            self.manager.delete_contact(phone)
            self.refresh_treeview()

    def gui_search_by_phone(self):
        phone = simpledialog.askstring("Search", "Enter phone:")
        if not phone:
            return
        contact = self.manager.find_by_phone(phone.strip())
        if contact:
            messagebox.showinfo("Result", str(contact))
        else:
            messagebox.showinfo("Not Found", "No contact found.")

    def on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        phone = vals[1]
        c = self.manager.find_by_phone(phone)
        if c:
            messagebox.showinfo("Contact", str(c))

    def on_exit(self):
        self.manager.save_to_csv()
        self.root.quit()


class ContactDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, initial=None):
        self.initial = initial
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Name:").grid(row=0, column=0)
        ttk.Label(master, text="Phone:").grid(row=1, column=0)
        ttk.Label(master, text="Email:").grid(row=2, column=0)
        ttk.Label(master, text="Address:").grid(row=3, column=0)

        self.e_name = ttk.Entry(master, width=40)
        self.e_phone = ttk.Entry(master, width=40)
        self.e_email = ttk.Entry(master, width=40)
        self.e_address = ttk.Entry(master, width=40)

        self.e_name.grid(row=0, column=1, pady=2)
        self.e_phone.grid(row=1, column=1, pady=2)
        self.e_email.grid(row=2, column=1, pady=2)
        self.e_address.grid(row=3, column=1, pady=2)

        if self.initial:
            n, p, e, a = self.initial
            self.e_name.insert(0, n)
            self.e_phone.insert(0, p)
            self.e_email.insert(0, e)
            self.e_address.insert(0, a)

        return self.e_name

    def validate(self):
        name = self.e_name.get().strip()
        phone = self.e_phone.get().strip()
        if not name or not phone:
            messagebox.showerror("Error", "Name and Phone required.")
            return False
        if not phone.isdigit():
            messagebox.showerror("Error", "Phone must be digits only.")
            return False
        return True

    def apply(self):
        self.result = (
            self.e_name.get().strip(),
            self.e_phone.get().strip(),
            self.e_email.get().strip(),
            self.e_address.get().strip()
        )


def console_menu(manager: ContactManager):
    HELP = """
1) Add Contact
2) View All (by name)
3) View All (by phone - radix)
4) Search
5) Update
6) Delete
7) Save & Exit
8) Exit
"""

    while True:
        print(HELP)
        choice = input("Choice: ").strip()

        if choice == "1":
            name = input("Name: ").strip()
            phone = input("Phone: ").strip()
            if not phone.isdigit():
                print("Digits only.")
                continue
            email = input("Email: ").strip()
            address = input("Address: ").strip()
            ok = manager.add_contact(Contact(name, phone, email, address))
            print("Added" if ok else "Phone exists")

        elif choice == "2":
            for c in manager.get_all_contacts_sorted_by_name():
                print("-" * 25)
                print(c)

        elif choice == "3":
            for c in manager.get_all_contacts_sorted_by_phone_radix():
                print("-" * 25)
                print(c)

        elif choice == "4":
            phone = input("Phone: ").strip()
            c = manager.find_by_phone(phone)
            print(c if c else "Not found")

        elif choice == "5":
            phone = input("Phone to update: ").strip()
            c = manager.find_by_phone(phone)
            if not c:
                print("Not found")
                continue
            name = input(f"Name [{c.name}]: ").strip() or c.name
            new_phone = input(f"Phone [{c.phone}]: ").strip() or c.phone
            if not new_phone.isdigit():
                print("Digits only")
                continue
            email = input(f"Email [{c.email}]: ").strip() or c.email
            address = input(f"Address [{c.address}]: ").strip() or c.address
            ok = manager.update_contact(phone, Contact(name, new_phone, email, address))
            print("Updated" if ok else "Failed")

        elif choice == "6":
            phone = input("Phone: ")
            print("Deleted" if manager.delete_contact(phone) else "Not found")

        elif choice == "7":
            manager.save_to_csv()
            print("Saved.")
            break

        elif choice == "8":
            break


def main():
    manager = ContactManager()
    root = tk.Tk()
    app = ContactApp(root, manager)

    def ask_mode():
        res = messagebox.askquestion("Mode", "Open console menu too?")
        if res == "yes":
            import threading
            threading.Thread(target=console_menu, args=(manager,), daemon=True).start()

    root.after(100, ask_mode)
    root.mainloop()
    manager.save_to_csv()

if __name__ == "__main__":
    main()
