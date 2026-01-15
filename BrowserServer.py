from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

USERS_FILE = "users.json"
SITES_FILE = "sites.json"


# -------------------------
# Helpers
# -------------------------
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# -------------------------
# Login
# -------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    users = load_json(USERS_FILE)

    username = data.get("username")
    password = data.get("password")

    if username not in users:
        return jsonify({"success": False, "error": "User not found"})

    user = users[username]

    if user["banned"]:
        return jsonify({"success": False, "error": "User is banned"})

    if user["password"] != password:
        return jsonify({"success": False, "error": "Wrong password"})

    return jsonify({
        "success": True,
        "username": username,
        "is_admin": user["is_admin"]
    })


# -------------------------
# Register
# -------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    users = load_json(USERS_FILE)

    username = data.get("username")
    password = data.get("password")

    if username in users:
        return jsonify({"success": False, "error": "Username exists"})

    users[username] = {
        "password": password,
        "is_admin": False,
        "banned": False
    }

    save_json(USERS_FILE, users)
    return jsonify({"success": True})


# -------------------------
# Create Website
# -------------------------
@app.route("/create_site", methods=["POST"])
def create_site():
    data = request.json
    sites = load_json(SITES_FILE)

    owner = data.get("owner")
    title = data.get("title")
    content = data.get("content")

    site_id = f"{owner}/{title}"

    sites[site_id] = {
        "owner": owner,
        "title": title,
        "content": content
    }

    save_json(SITES_FILE, sites)
    return jsonify({"success": True, "url": site_id})


# -------------------------
# Search
# -------------------------
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").lower()
    sites = load_json(SITES_FILE)

    results = []

    for site_id, site in sites.items():
        if query in site["title"].lower() or query in site["content"].lower():
            results.append(site_id)

    return jsonify({"results": results})


# -------------------------
# Get Site
# -------------------------
@app.route("/site/<path:site_id>", methods=["GET"])
def get_site(site_id):
    sites = load_json(SITES_FILE)

    if site_id not in sites:
        return jsonify({"error": "Not found"}), 404

    return jsonify(sites[site_id])


# -------------------------
# Admin: List Users
# -------------------------
@app.route("/admin/users", methods=["GET"])
def admin_users():
    admin_key = request.args.get("admin")

    users = load_json(USERS_FILE)

    if admin_key not in users or not users[admin_key]["is_admin"]:
        return jsonify({"error": "Admin only"}), 403

    return jsonify(users)


# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
