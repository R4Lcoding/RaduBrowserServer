import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

USERS_FILE = "users.db"
SITES_FILE = "sites.db"

current_user = None

# -------------------------------
# LOAD / SAVE
# -------------------------------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

users = load_json(USERS_FILE)
sites = load_json(SITES_FILE)

# -------------------------------
# LOGIN / REGISTER
# -------------------------------
def login_window():
    win = tk.Toplevel(root)
    win.title("Login")
    win.geometry("300x260")

    tk.Label(win, text="Username").pack(pady=5)
    u_entry = tk.Entry(win)
    u_entry.pack()

    tk.Label(win, text="Password").pack(pady=5)
    p_entry = tk.Entry(win, show="*")
    p_entry.pack()

    def login():
        global current_user
        u = u_entry.get()
        p = p_entry.get()

        if u not in users:
            messagebox.showerror("Error", "User not found")
            return
        if users[u]["banned"]:
            messagebox.showerror("Banned", "This account is banned")
            return
        if users[u]["password"] != p:
            messagebox.showerror("Error", "Wrong password")
            return

        current_user = u
        status.config(text=f"Logged in as {u}")
        win.destroy()
        refresh_buttons()

    def register():
        u = u_entry.get()
        p = p_entry.get()

        if not u or not p:
            messagebox.showerror("Error", "Fill all fields")
            return

        if u in users:
            messagebox.showerror("Error", "User already exists")
            return

        users[u] = {
            "password": p,
            "admin": False,
            "banned": False
        }
        save_json(USERS_FILE, users)
        messagebox.showinfo("Success", "Account created")

    tk.Button(win, text="Login", command=login).pack(pady=5)
    tk.Button(win, text="Register", command=register).pack()

# -------------------------------
# CHANGE PASSWORD
# -------------------------------
def change_password():
    if not current_user:
        messagebox.showwarning("Login required", "You must be logged in.")
        return

    win = tk.Toplevel(root)
    win.title("Change Password")
    win.geometry("300x260")

    tk.Label(win, text="Old Password").pack(pady=5)
    old = tk.Entry(win, show="*")
    old.pack()

    tk.Label(win, text="New Password").pack(pady=5)
    new = tk.Entry(win, show="*")
    new.pack()

    tk.Label(win, text="Confirm New Password").pack(pady=5)
    conf = tk.Entry(win, show="*")
    conf.pack()

    def apply():
        if users[current_user]["password"] != old.get():
            messagebox.showerror("Error", "Old password incorrect")
            return
        if not new.get() or new.get() != conf.get():
            messagebox.showerror("Error", "Passwords do not match")
            return

        users[current_user]["password"] = new.get()
        save_json(USERS_FILE, users)
        messagebox.showinfo("Success", "Password changed")
        win.destroy()

    tk.Button(win, text="Change Password", command=apply).pack(pady=10)

# -------------------------------
# ADMIN ACCOUNT MANAGER
# -------------------------------
def account_manager():
    if not current_user or not users[current_user]["admin"]:
        return

    win = tk.Toplevel(root)
    win.title("Account Manager")
    win.geometry("400x500")

    search = tk.Entry(win)
    search.pack(fill="x", padx=10, pady=5)

    box = tk.Listbox(win, font=("Arial", 12))
    box.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh(filter_text=""):
        box.delete(0, tk.END)
        for u, d in users.items():
            if filter_text.lower() in u.lower():
                flags = []
                if d["admin"]:
                    flags.append("ADMIN")
                if d["banned"]:
                    flags.append("BANNED")
                label = u + (" [" + ", ".join(flags) + "]" if flags else "")
                box.insert(tk.END, label)

    def toggle_ban():
        sel = box.curselection()
        if not sel:
            return

        name = box.get(sel[0]).split()[0]
        if name == current_user:
            return

        users[name]["banned"] = not users[name]["banned"]
        save_json(USERS_FILE, users)
        refresh(search.get())

    search.bind("<KeyRelease>", lambda e: refresh(search.get()))
    tk.Button(win, text="Ban / Unban", command=toggle_ban).pack(pady=5)
    refresh()

# -------------------------------
# TABS
# -------------------------------
def sync_tabs():
    tab_list.delete(0, tk.END)
    for t in notebook.tabs():
        tab_list.insert(tk.END, notebook.tab(t, "text"))

def select_tab(event):
    if tab_list.curselection():
        notebook.select(tab_list.curselection()[0])

def new_tab():
    tab = ttk.Frame(notebook)
    notebook.add(tab, text="New Tab")
    notebook.select(tab)
    tk.Label(tab, text="New Tab", font=("Arial", 14)).pack(expand=True)
    sync_tabs()

def close_tab():
    if tab_list.curselection() and len(notebook.tabs()) > 1:
        notebook.forget(tab_list.curselection()[0])
        sync_tabs()

# -------------------------------
# SEARCH
# -------------------------------
def search():
    q = search_entry.get().lower()
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=f"Search: {q}")
    notebook.select(tab)

    text = tk.Text(tab, wrap="word", font=("Arial", 12))
    text.pack(fill="both", expand=True)

    found = False
    for title, data in sites.items():
        if q in title.lower() or q in data["content"].lower():
            found = True
            url = f"{data['owner']}://{title.replace(' ', '_')}"
            text.insert(tk.END, title + "\n", ("title", title))
            text.insert(tk.END, url + "\n", "url")
            text.insert(tk.END, data["content"][:120] + "...\n\n", "snippet")
            text.tag_bind(title, "<Button-1>",
                          lambda e, t=title: open_site(t))

    if not found:
        text.insert(tk.END, "No results found.")

    text.tag_config("title", foreground="blue", underline=1)
    text.tag_config("url", foreground="green")
    text.tag_config("snippet", foreground="black")
    text.config(state="disabled")
    sync_tabs()

def open_site(title):
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=title)
    notebook.select(tab)

    text = tk.Text(tab, wrap="word", font=("Arial", 12))
    text.pack(fill="both", expand=True)
    text.insert(tk.END, sites[title]["content"])
    text.config(state="disabled")
    sync_tabs()

# -------------------------------
# CREATE SITE (LOGIN REQUIRED)
# -------------------------------
def create_site():
    if not current_user:
        messagebox.showwarning(
            "Login Required",
            "You need to log in to create a website."
        )
        return

    win = tk.Toplevel(root)
    win.title("Create Website")
    win.geometry("400x400")

    tk.Label(win, text="Website Title").pack(pady=5)
    title = tk.Entry(win)
    title.pack(pady=5)

    tk.Label(win, text="Website Content").pack(pady=5)
    content = tk.Text(win, height=10)
    content.pack(pady=5)

    def save():
        t = title.get().strip()
        c = content.get("1.0", tk.END).strip()

        if t and c:
            sites[t] = {
                "owner": current_user,
                "content": c
            }
            save_json(SITES_FILE, sites)
            win.destroy()

    tk.Button(win, text="Publish Website", command=save).pack(pady=10)

# -------------------------------
# UI
# -------------------------------
root = tk.Tk()
root.title("Radu's Browser")
root.geometry("1000x600")

top = tk.Frame(root)
top.pack(fill="x")

tk.Label(top, text="Radu's Browser", font=("Arial", 18)).pack(side="left", padx=10)

search_entry = tk.Entry(top, font=("Arial", 14))
search_entry.pack(side="left", padx=5)

tk.Button(top, text="Search", command=search).pack(side="left", padx=5)

status = tk.Label(top, text="Not logged in")
status.pack(side="right", padx=10)

tk.Button(top, text="Login", command=login_window).pack(side="right")
tk.Button(top, text="Change Password", command=change_password).pack(side="right")
tk.Button(top, text="Accounts", command=account_manager).pack(side="right")
tk.Button(top, text="Create Site", command=create_site).pack(side="right")

main = tk.Frame(root)
main.pack(fill="both", expand=True)

sidebar = tk.Frame(main, width=180)
sidebar.pack(side="left", fill="y")

tab_list = tk.Listbox(sidebar, font=("Arial", 12))
tab_list.pack(fill="both", expand=True)
tab_list.bind("<<ListboxSelect>>", select_tab)

tk.Button(sidebar, text="+", command=new_tab).pack(fill="x")
tk.Button(sidebar, text="X", command=close_tab).pack(fill="x")

notebook = ttk.Notebook(main)
notebook.pack(fill="both", expand=True)

new_tab()
sync_tabs()
root.mainloop()
