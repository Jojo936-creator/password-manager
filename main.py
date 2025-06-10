import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk
try:
    from ttkthemes import ThemedTk
    THEMES_AVAILABLE = True
except ImportError:
    THEMES_AVAILABLE = False
import os
import base64
import secrets
from cryptography.fernet import Fernet, InvalidToken

DATA_FILE = "vault.dat"
KEY_FILE = "vault.key"

# --- Encryption helpers ---
def generate_key_from_file(key_path):
    with open(key_path, 'rb') as f:
        return base64.urlsafe_b64encode(f.read().ljust(32, b'0'))

def get_fernet_from_file(key_path):
    key = generate_key_from_file(key_path)
    return Fernet(key)

def encrypt_data(data, key_path):
    f = get_fernet_from_file(key_path)
    return f.encrypt(data.encode('utf-8'))

def decrypt_data(token, key_path):
    f = get_fernet_from_file(key_path)
    return f.decrypt(token).decode('utf-8')

# --- Vault logic ---
def load_vault(key_path):
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'rb') as f:
        encrypted = f.read()
    try:
        decrypted = decrypt_data(encrypted, key_path)
        return eval(decrypted) if decrypted else {}
    except InvalidToken:
        raise ValueError("Invalid key file!")

def save_vault(vault, key_path):
    encrypted = encrypt_data(str(vault), key_path)
    with open(DATA_FILE, 'wb') as f:
        f.write(encrypted)

# --- GUI ---
class PasswordManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Manager")
        self.key_path = None
        self.vault = {}
        self.style = ttk.Style()
        if THEMES_AVAILABLE:
            self.root.set_theme("arc")
        else:
            self.style.theme_use("clam")
        self.style.configure('TButton', font=('Segoe UI', 11), padding=6)
        self.style.configure('TLabel', font=('Segoe UI', 11))
        self.style.configure('Header.TLabel', font=('Segoe UI', 14, 'bold'))
        self.setup_key()

    def setup_key(self):
        self.clear()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)
        if not os.path.exists(KEY_FILE):
            # First run: generate key file
            token = secrets.token_bytes(16)
            with open(KEY_FILE, 'wb') as f:
                f.write(token)
            messagebox.showinfo("Key Created", f"A new key file has been created: {KEY_FILE}\nKeep it safe!")
        ttk.Label(frame, text="Select your key file to unlock vault:", style='Header.TLabel').pack(pady=10)
        ttk.Button(frame, text="Select Key File", command=self.select_key).pack(pady=10)

    def select_key(self):
        path = filedialog.askopenfilename(title="Select Key File", filetypes=[("Key Files", "*.key"), ("All Files", "*")])
        if path:
            try:
                self.vault = load_vault(path)
                self.key_path = path
                self.show_main()
            except Exception:
                messagebox.showerror("Error", "Invalid or wrong key file!")

    def show_main(self):
        self.clear()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)
        ttk.Label(frame, text="Password Manager", style='Header.TLabel').pack(pady=10)
        ttk.Button(frame, text="Add Password", command=self.add_password).pack(pady=5, fill='x')
        ttk.Button(frame, text="View Passwords", command=self.view_passwords).pack(pady=5, fill='x')
        ttk.Button(frame, text="Search Password", command=self.search_password).pack(pady=5, fill='x')
        ttk.Button(frame, text="Remove Password", command=self.remove_password).pack(pady=5, fill='x')
        ttk.Button(frame, text="Lock", command=self.setup_key).pack(pady=5, fill='x')

    def add_password(self):
        site = simpledialog.askstring("Add", "Site/Service:")
        user = simpledialog.askstring("Add", "Username:")
        pwd = simpledialog.askstring("Add", "Password:")
        if site and user and pwd:
            self.vault[site] = (user, pwd)
            save_vault(self.vault, self.key_path)
            messagebox.showinfo("Saved", f"Password for {site} saved.")

    def view_passwords(self):
        self.clear()
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True, fill='both')
        ttk.Label(frame, text="All Passwords:", style='Header.TLabel').pack(pady=5)
        canvas = tk.Canvas(frame, borderwidth=0, background="#f7f7f7", height=180)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for site, (user, pwd) in self.vault.items():
            ttk.Label(scrollable_frame, text=f"{site}: {user} / {pwd}").pack(anchor='w', padx=5, pady=2)
        ttk.Button(frame, text="Back", command=self.show_main).pack(pady=10)

    def search_password(self):
        site = simpledialog.askstring("Search", "Site/Service:")
        if site in self.vault:
            user, pwd = self.vault[site]
            messagebox.showinfo("Found", f"{site}: {user} / {pwd}")
        else:
            messagebox.showwarning("Not found", f"No password for {site}")

    def remove_password(self):
        site = simpledialog.askstring("Remove", "Site/Service to remove:")
        if site in self.vault:
            confirm = messagebox.askyesno("Confirm", f"Remove password for {site}?")
            if confirm:
                del self.vault[site]
                save_vault(self.vault, self.key_path)
                messagebox.showinfo("Removed", f"Password for {site} removed.")
        else:
            messagebox.showwarning("Not found", f"No password for {site}")

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    if THEMES_AVAILABLE:
        root = ThemedTk(theme="arc")
    else:
        root = tk.Tk()
    root.geometry("400x420")
    app = PasswordManager(root)
    root.mainloop()
