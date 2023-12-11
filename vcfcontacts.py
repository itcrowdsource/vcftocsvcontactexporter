import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import vobject
import csv
import os
import subprocess
import sys
import datetime

class ContactManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Contact Manager")

        # Check and install required modules
        self.check_and_install_modules(['vobject'])

        self.contacts = {}  # {phone: (firstname, lastname, status)}
        self.selected_contacts = set()
        self.load_saved_selections()

        self.create_widgets()
        self.refresh_treeview()

    def check_and_install_modules(self, modules):
        for module in modules:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            except subprocess.CalledProcessError as e:
                print(f"Error installing module {module}: {e}")

    def create_widgets(self):
        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(pady=20)

        self.tree_scroll = tk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Voornaam", "Achternaam", "Telefoonnummer", "Status"), selectmode="extended", yscrollcommand=self.tree_scroll.set)
        self.tree.heading("Voornaam", text="Voornaam")
        self.tree.heading("Achternaam", text="Achternaam")
        self.tree.heading("Telefoonnummer", text="Telefoonnummer")
        self.tree.heading("Status", text="Status")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree_scroll.config(command=self.tree.yview)

        self.load_button = tk.Button(self.root, text="VCF Laden", command=self.load_vcf)
        self.load_button.pack(pady=10)

        self.save_button = tk.Button(self.root, text="Selecties Opslaan", command=self.save_selections)
        self.save_button.pack(pady=10)

        self.deselect_button = tk.Button(self.root, text="Selecties Deselecteren", command=self.deselect_selections)
        self.deselect_button.pack(pady=10)

        self.export_csv_button = tk.Button(self.root, text="Exporteren naar CSV", command=self.export_csv)
        self.export_csv_button.pack(pady=10)

        # Nieuwe knop voor het exporteren naar TXT
        self.export_txt_button = tk.Button(self.root, text="Exporteren naar TXT", command=self.export_txt)
        self.export_txt_button.pack(pady=10)

        self.filter_var = tk.StringVar()
        self.filter_dropdown = ttk.Combobox(self.root, textvariable=self.filter_var, values=["Alle", "Nieuw", "Bestaand", "Geselecteerd"], state="readonly")
        self.filter_dropdown.set("Alle")
        self.filter_dropdown.bind("<<ComboboxSelected>>", self.filter_contacts)
        self.filter_dropdown.pack(pady=10)

        search_label = tk.Label(self.root, text="Zoeken:")
        search_label.pack(pady=10)
        self.search_entry = tk.Entry(self.root)
        self.search_entry.pack(pady=10)
        self.search_entry.bind('<KeyRelease>', lambda event: self.search_and_filter(self.search_entry.get()))

        # Handleiding Button
        self.help_button = tk.Button(self.root, text="Handleiding", command=self.open_help_document)
        self.help_button.pack(pady=10)

        # Info Text
        info_text = "Omschrijving: Toepassing voor het inlezen en markeren van telefooncontacten die uitgezonderd moeten worden van veiligstelling of archivering van chatberichten.\nAuteur: R.H. Roos / Ministerie van Financiën\nContact: r.h.roos@minfin.nl \nVersie: v1.1"
        self.info_label = tk.Label(self.root, text=info_text, justify=tk.LEFT, bg="white")
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X)

    def open_help_document(self):
        os.startfile("leesmij.docx")

    def load_vcf(self):
        filepath = filedialog.askopenfilename(filetypes=[("VCF Files", "*.vcf")])
        if not filepath:
            return

        # Backup current saved selections
        self.backup_saved_selections()

        with open(filepath, 'r', encoding='utf-8') as file:
            vcf_content = file.read()
        vcards = vobject.readComponents(vcf_content)
        new_contacts = {}
        for vcard in vcards:
            try:
                if hasattr(vcard, "fn"):
                    name_parts = str(vcard.fn.value).split(' ')
                    firstname = name_parts[0]
                    lastname = ' '.join(name_parts[1:])
                else:
                    firstname = "Onbekend"
                    lastname = "Onbekend"
                phone = vcard.tel.value if hasattr(vcard, "tel") else "Onbekend"
                # Check if the contact is new or existing
                if phone not in self.contacts:
                    status = "Nieuw"
                else:
                    status = self.contacts[phone][2]
                new_contacts[phone] = (firstname, lastname, status)
            except Exception as e:
                print(f"Fout bij het verwerken van vcard: {e}")
        # Update the contacts dictionary with new contacts
        self.contacts.update(new_contacts)
        self.refresh_treeview()
        # Save the updated contacts to the saved_selections.csv
        self.save_contacts_to_file()
    
    def manage_backups(self, backup_folder="backups", max_backups=10):
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        # Verplaats alle bestaande backups naar de backup map
        for file in os.listdir():
            if file.startswith("saved_selections_backup_") and file.endswith(".csv"):
                os.rename(file, os.path.join(backup_folder, file))

        # Verwijder de oudste backups als het maximum is overschreden
        backups = sorted([f for f in os.listdir(backup_folder) if f.startswith("saved_selections_backup_") and f.endswith(".csv")])
        while len(backups) > max_backups:
            os.remove(os.path.join(backup_folder, backups.pop(0)))


    def backup_saved_selections(self):
        backup_folder = "backups"
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        backup_file = os.path.join(backup_folder, f"saved_selections_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(backup_file, "w", encoding="utf-8", newline='') as file:
            writer = csv.writer(file, delimiter=';')
            for phone, (firstname, lastname, status) in self.contacts.items():
                writer.writerow([firstname, lastname, phone, status])

        # Beheer de backups
        self.manage_backups()


    def save_selections(self):
        selected_items = self.tree.selection()
        for item in self.tree.get_children():
            phone = self.tree.item(item, "values")[2]
            if item in selected_items:
                self.selected_contacts.add(phone)
                self.contacts[phone] = (self.contacts[phone][0], self.contacts[phone][1], "Geselecteerd")
            elif phone not in self.selected_contacts:
                # Update de status naar 'Bestaand' voor niet-geselecteerde contacten
                self.contacts[phone] = (self.contacts[phone][0], self.contacts[phone][1], "Bestaand")

            # Update de TreeView met de nieuwe status
            self.tree.item(item, values=(self.contacts[phone][0], self.contacts[phone][1], phone, self.contacts[phone][2]))

        self.save_contacts_to_file()
        messagebox.showinfo("Info", "Selecties zijn opgeslagen. De status van de contacten is bijgewerkt.")


    def deselect_selections(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            phone = self.tree.item(item, "values")[2]
            self.selected_contacts.remove(phone)
            self.contacts[phone] = (self.contacts[phone][0], self.contacts[phone][1], "Bestaand")
            self.tree.item(item, values=(self.contacts[phone][0], self.contacts[phone][1], phone, "Bestaand"))
        self.save_contacts_to_file()
        messagebox.showinfo("Info", "Selecties zijn gedeselecteerd. De status van de contacten is bijgewerkt naar 'Bestaand'.")

    def load_saved_selections(self):
        if os.path.exists("saved_selections.csv"):
            with open("saved_selections.csv", "r", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter=';')
                for row in reader:
                    if len(row) == 4:
                        firstname, lastname, phone, status = row
                        self.contacts[phone] = (firstname, lastname, status)
                        if status == "Geselecteerd":
                            self.selected_contacts.add(phone)
                    else:
                        print(f"Ongeldige rij in CSV-bestand: {row}")


    def update_status_from_saved_selections(self):
        for phone, (firstname, lastname, status) in self.contacts.items():
            if phone in self.selected_contacts:
                self.contacts[phone] = (firstname, lastname, "Geselecteerd")
            else:
                self.contacts[phone] = (firstname, lastname, "Bestaand")
        self.refresh_treeview()

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8", newline='') as file:
            writer = csv.writer(file, delimiter=';')
            for phone, (firstname, lastname, status) in self.contacts.items():
                if status == "Geselecteerd":
                    writer.writerow([firstname, lastname, phone])

    def filter_contacts(self, event):
        self.refresh_treeview()

    def search_and_filter(self, search_term):
        self.tree.delete(*self.tree.get_children())
        for phone, (firstname, lastname, status) in self.contacts.items():
            if search_term.lower() in f"{firstname} {lastname} {phone}".lower():
                self.tree.insert('', 'end', values=(firstname, lastname, phone, status))

    def refresh_treeview(self):
        self.tree.delete(*self.tree.get_children())
        for phone, (firstname, lastname, status) in self.contacts.items():
            if self.filter_var.get() == "Alle" or status == self.filter_var.get():
                self.tree.insert('', 'end', values=(firstname, lastname, phone, status))

    def save_contacts_to_file(self):
        with open("saved_selections.csv", "w", encoding="utf-8", newline='') as file:
            writer = csv.writer(file, delimiter=';')
            for phone, (firstname, lastname, status) in self.contacts.items():
                writer.writerow([firstname, lastname, phone, status])
                
    def export_txt(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as file:
            for phone, (firstname, lastname, status) in self.contacts.items():
                if status == "Geselecteerd":
                    file.write(f"{firstname} {lastname}\n")

if __name__ == "__main__":
    app = ContactManager()
    app.root.mainloop()
