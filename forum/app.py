from flask import Flask, request, redirect, abort, url_for, render_template
import sqlite3
import hashlib
import time

# Define Functions
def hash_string(passwd):
    return hashlib.sha256(passwd.encode('utf-8')).hexdigest()

def gen_Token(user, time):
    return f"{hash_string(user)}/{str(int(time))}"

def get_Amount_of_Posts():
    posts = sqlite3.connect("posts.db")
    cur = posts.cursor()
    res = cur.execute("SELECT * FROM posts")
    final = res.fetchall()
    cur.close()
    return len(final)

def get_posts():
    posts = sqlite3.connect("posts.db")
    cur = posts.cursor()
    res = cur.execute("SELECT * FROM posts")
    final = res.fetchall()
    cur.close()
    return final

def get_accounts():
    accounts = sqlite3.connect("accounts.db")
    cur = accounts.cursor()
    res = cur.execute("SELECT * FROM accounts")
    final = res.fetchall()
    cur.close()
    return final

def user_exists(user):
    accounts = sqlite3.connect("accounts.db")
    cur = accounts.cursor()
    res = cur.execute("SELECT user FROM accounts")
    final = res.fetchall()
    for x in final:
        if user in x:
            cur.close()
            return True
    cur.close()
    return False

# Initialize the accounts database
acc_db = sqlite3.connect("accounts.db")
acc_cur = acc_db.cursor()
acc_cur.execute("CREATE TABLE IF NOT EXISTS accounts(user, password)")
acc_cur.execute("CREATE TABLE IF NOT EXISTS sessions(user, token, expires)")

res = acc_cur.execute("SELECT * FROM accounts")

if len(res.fetchall()) == 0:
    admin_password = hash_string(input("Admin Password: "))
    acc_cur.execute(f"""
        INSERT INTO accounts VALUES
        ("admin", "{admin_password}")
    """)
    acc_db.commit()

acc_db.close()

# Initialize the posts database
p_db = sqlite3.connect("posts.db")
p_cur = p_db.cursor()
p_cur.execute("CREATE TABLE IF NOT EXISTS posts(id, user, title, body)")
p_cur.close()

# Initialize Flask App
app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def default():
    return "Welcome to the Silk Forum Root"

@app.route("/validate/", methods=['GET'])
def validate():
    data = request.json
    token = data["token"]

    db = sqlite3.connect("accounts.db")
    cur = db.cursor()
    res = cur.execute("SELECT * FROM sessions WHERE token=?", token)
    final = res.fetchone()

    if final[1] == token and time.time() < final[2]:
        return {
            "status":"Success",
            "username":final[0]
        }
    else:
        return {
            "status":"Invalid Token"
        }, 403

@app.route("/accounts/", methods=['GET'])
def accounts():
    return get_accounts()

@app.route("/post/", methods=['POST', 'GET'])
def post():
    if request.method == "POST":
        data = request.json
        title = data["title"]
        body = data["body"]
        token = data["token"]

        if not token:
            return {
                "status":"Token is missing"
            }, 400

        # Check if the user is logged in
        db = sqlite3.connect("accounts.db")
        cur = db.cursor()
        res = cur.execute("SELECT * FROM sessions WHERE token=?", (token))
        final = res.fetchone()

        if final != None:
            if final[1] == token and time.time() < final[2]:
                db = sqlite3.connect("posts.db")
                cur = db.cursor()
                res = cur.execute("INSERT INTO posts VALUES (?,?,?,?)", (get_Amount_of_Posts()+1, final[0], title, body))
                db.commit()
                res.close()
                print(f"{final[0]} created a post")
                return {
                    "status":"Success"
                }
            else:
                return {
                    "status":"Invalid Token"
                }, 403
        else:
            return {
                "status":"No Token found"
            }, 404
        
    else:
        post_id = request.args.get("id")
        if post_id != None:
            try:
                post_id = int(post_id)
            except:
                return {
                    "status":"Post ID is in an invalid format"
                }, 400
            
            db = sqlite3.connect("posts.db")
            cur = db.cursor()
            res = cur.execute("SELECT * FROM posts WHERE id=?", (post_id,))
            post = res.fetchone()

            if post != None:
                return {
                    "status":"Success",
                    "post":post
                }
            else:
                return {
                    "status":"Post not found"
                }, 404

        else:
            return get_posts()
        
@app.route("/login/", methods=['POST'])
def login():
    data = request.form
    username = data["user"]
    password = data["password"]

    if user_exists(username):
        db = sqlite3.connect("accounts.db")
        cur = db.cursor()
        res = cur.execute("SELECT password FROM accounts WHERE user=?", (username,))
        final = res.fetchone()
        print(f"Request from {username} at Login")

        if final[0] == hash_string(password):
            res = cur.execute("SELECT * FROM sessions WHERE user=?", (username,))
            final = res.fetchone()

            print(final)

            current_time = time.time()
            expires = current_time + 3600
            token = gen_Token(username, current_time)

            if final == None or time.time() > final[2]:
                cur.execute("DELETE FROM sessions WHERE user=?", (username,))
                cur.execute("INSERT INTO sessions VALUES (?,?,?)", (username, token, expires))
                db.commit()
                print(f"Generated token for {username}")

            cur.close()
            print(f"{username} logged in.")
            return {
                "status":"Success",
                "token":token
            }
        else:
            return {
                "status":"Wrong Login credentials"
            }, 403
    else:
        return {
            "status":"No such account"
        }, 404

@app.route("/register/", methods=['POST'])
def register():
    data = request.form
    username = data["user"]
    password = data["password"]

    if username and password:
        if user_exists(username):
            return "Bad Request, Exists", 400

        print(f"Request from {username} at Register")
        print(hash_string(password))
        db = sqlite3.connect("accounts.db")
        cur = db.cursor()
        cur.execute("INSERT INTO accounts VALUES (?, ?)", (username, hash_string(password)))
        db.commit()
        print("Account Added.")
        return redirect(url_for("accounts")) # Placeholder
    else:
        return {
            "status":"Login credentials are missing"
        }, 400
    
@app.errorhandler(404)
def page_not_found(error):
    return {
        "status":"Not Found",
    }, 404
