import csv
CSV_FILE = "contacts.csv"
class Contact:
    def __init__(self, name: str, phone: str, email: str, address: str):
        self.name = name.strip()
        self.phone = phone.strip()
        self.email = (email or "").strip()
        self.address = (address or "").strip()
        self.next = None
    def update(self, phone: str = None, email: str = None, address: str = None, name: str = None):
        if name is not None:
            self.name = name.strip()
        if phone is not None:
            self.phone = phone.strip()
        if email is not None:
            self.email = email.strip()
        if address is not None:
            self.address = address.strip()
    def to_csv_row(self):
        return [self.name, self.phone, self.email, self.address]
    def from_csv_row(self, row):
        name = row[0] if len(row) > 0 else ""
        phone = row[1] if len(row) > 1 else ""
        email = row[2] if len(row) > 2 else ""
        address = row[3] if len(row) > 3 else ""
        return Contact(name, phone, email, address)
    def __str__(self):
        return f"Name: {self.name}\nPhone: {self.phone}\nEmail: {self.email}\nAddress: {self.address}"
class ContactManager:
    def __init__(self):
        self.head = None
        self.load_from_csv()
    def add_contact(self, contact: Contact):
        if not contact.phone or self.find_by_phone(contact.phone):
            return False
        if self.head is None:
            self.head = contact
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = contact
        return True
    def find_by_phone(self, phone: str):
        phone = phone.strip()
        current = self.head
        while current:
            if current.phone == phone:
                return current
            current = current.next
        return None
    def find_by_name(self, name: str):
        name = name.lower()
        current = self.head
        while current:
            if current.name.lower() == name:
                return current
            current = current.next
        return None
    def delete_contact(self, phone: str):
        phone = phone.strip()
        prev = None
        current = self.head
        while current:
            if current.phone == phone:
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next
                return True
            prev = current
            current = current.next
        return False
    def update_contact_by_name(self, old_name: str, new_contact: Contact):
        current = self.head
        while current:
            if current.name.lower() == old_name.lower():
                if new_contact.phone != current.phone and self.find_by_phone(new_contact.phone):
                    return False
                current.name = new_contact.name
                current.phone = new_contact.phone
                current.email = new_contact.email
                current.address = new_contact.address
                return True
            current = current.next
        return False
    def save_to_csv(self, filename=CSV_FILE):
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Phone", "Email", "Address"])
                current = self.head
                while current:
                    writer.writerow(current.to_csv_row())
                    current = current.next
        except Exception as e:
            print("Failed to save CSV:", e)

    def load_from_csv(self, filename=CSV_FILE):
        self.head = None
        try:
            with open(filename, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if not rows:
                    return
                start = 0
                hdr = [h.strip().lower() for h in rows[0]]
                if len(hdr) >= 2 and ("name" in hdr[0] or "phone" in hdr[1]):
                    start = 1
                for r in rows[start:]:
                    if not r or len(r) < 2:
                        continue
                    contact = Contact(r[0], r[1], r[2] if len(r) > 2 else "", r[3] if len(r) > 3 else "")
                    self.add_contact(contact)
        except Exception as e:
            print("Failed to load CSV:", e)
    def get_all_contacts_sorted_by_name(self):
        contacts = []
        current = self.head
        while current:
            contacts.append(current)
            current = current.next
        contacts.sort(key=lambda c: c.name.lower())
        return contacts
    def get_all_contacts_sorted_by_phone_radix(self):
        contacts = []
        current = self.head
        while current:
            contacts.append(current)
            current = current.next
        contacts.sort(key=lambda c: "".join(ch for ch in c.phone if ch.isdigit()))
        return contacts
def input_phone(prompt: str, allow_empty=False, default=""):
    while True:
        phone = input(prompt).strip()
        if allow_empty and phone == "":
            return default
        if phone.isdigit():
            return phone
        print("Error: Phone number must contain digits only. Try again.")
def console_menu(manager: ContactManager):
    HELP_TEXT = (
        "\nContact Book Console Menu:\n"
        "1) Add Contact\n"
        "2) View All (sorted by name)\n"
        "3) View All (sorted by phone - radix)\n"
        "4) Search by phone\n"
        "5) Update contact\n"
        "6) Delete contact\n"
        "7) Save & Exit\n"
        "8) Exit without saving\n"
    )

    while True:
        print(HELP_TEXT)
        choice = input("Choose an option [1-8]: ").strip()
        if choice == "1":
            name = input("Name: ").strip()
            phone = input_phone("Phone: ")
            email = input("Email: ").strip()
            address = input("Address: ").strip()
            ok = manager.add_contact(Contact(name, phone, email, address))
            print("Added." if ok else "Phone already exists or invalid.")
        elif choice == "2":
            for c in manager.get_all_contacts_sorted_by_name():
                print("-" * 30)
                print(c)
        elif choice == "3":
            for c in manager.get_all_contacts_sorted_by_phone_radix():
                print("-" * 30)
                print(c)
        elif choice == "4":
            phone = input_phone("Phone to search: ")
            c = manager.find_by_phone(phone)
            print(c if c else "Not found.")
        elif choice == "5":
            name = input("Enter name to update: ").strip()
            c = manager.find_by_name(name)
            if not c:
                print("Not found.")
                continue
            new_name = input(f"Name [{c.name}]: ").strip() or c.name
            new_phone = input_phone(f"Phone [{c.phone}]: ", allow_empty=True, default=c.phone)
            email = input(f"Email [{c.email}]: ").strip() or c.email
            address = input(f"Address [{c.address}]: ").strip() or c.address
            ok = manager.update_contact_by_name(c.name, Contact(new_name, new_phone, email, address))
            print("Updated." if ok else "Failed to update.")
        elif choice == "6":
            phone = input_phone("Phone to delete: ")
            ok = manager.delete_contact(phone)
            print("Deleted." if ok else "Not found.")
        elif choice == "7":
            manager.save_to_csv()
            print("Saved. Exiting.")
            break
        elif choice == "8":
            print("Exiting without saving.")
            break
        else:
            print("Invalid choice.")
def main():
    manager = ContactManager()
    console_menu(manager)
if __name__ == "__main__":
    main()
