from flask import Flask, request, redirect, abort, url_for, render_template
from flask_cors import CORS
import sqlite3
import hashlib
import smtplib
import ssl
import getpass
from email.message import EmailMessage
import time
import os
import re
import random

# Define Functions
def hash_string(passwd):
    return hashlib.sha256(passwd.encode('utf-8')).hexdigest()

def gen_Token(user, time):
    return hash_string(f"{hash_string(user)}{str(int(time))}")

def delete_expired():
    accounts = sqlite3.connect("accounts.db")
    cur = accounts.cursor()
    cur.execute("DELETE FROM sessions WHERE expires<?", (time.time(),))
    cur.execute("DELETE FROM auth WHERE expires<?", (time.time(),))
    accounts.commit()
    cur.close()

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

def get_Amount_of_Users():
    accounts = sqlite3.connect("accounts.db")
    cur = accounts.cursor()
    res = cur.execute("SELECT * FROM accounts")
    final = res.fetchall()
    cur.close()
    return len(final)

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
acc_cur.execute("CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, password TEXT NOT NULL, email TEXT NOT NULL)")
acc_cur.execute("CREATE TABLE IF NOT EXISTS sessions(user TEXT NOT NULL, token TEXT NOT NULL, expires)")
acc_cur.execute("CREATE TABLE IF NOT EXISTS auth(user TEXT NOT NULL, password_hash TEXT NOT NULL, email TEXT NOT NULL, code INTEGER, expires)")

res = acc_cur.execute("SELECT * FROM accounts")

if len(res.fetchall()) == 0:
    admin_password = hash_string(getpass.getpass("Admin Password: "))
    acc_cur.execute(f"""
        INSERT INTO accounts (user, password, email) VALUES
        ("admin", "{admin_password}", "silkprojectdev@gmail.com")
    """)
    acc_db.commit()

acc_db.close()

# Initialize the posts database
p_db = sqlite3.connect("posts.db")
p_cur = p_db.cursor()
p_cur.execute("CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL)")
p_cur.close()

# Define Email Variables
email_port = 465
email_sender = "silkprojectdev@gmail.com"
email_password = "kwptszhbpvwdfhyn"
subject = "Silk Forum - Verify your account"

# Initialize Flask App
app = Flask(__name__)
CORS(app)

@app.route("/", methods=['POST', 'GET'])
def default():
    return "Welcome to the Silk Forum Root"

@app.route("/validate/", methods=['POST'])
def validate():
    data = request.json
    token = data["token"]
    print(token)

    if not token:
        return {
            "status":"No Token Requested"
        }, 400

    db = sqlite3.connect("accounts.db")
    cur = db.cursor()
    res = cur.execute("SELECT * FROM sessions WHERE token=?", (token,))
    final = res.fetchone()
    db.close()

    if final == None:
        return {
            "status":"Invalid Token"
        }, 403

    if final[1] == token and time.time() < final[2]:
        return {
            "status":"Success",
            "username":final[0]
        }
    else:
        return {
            "status":"Expired Token"
        }, 403

@app.route("/accounts/", methods=['GET'])
def accounts():
    account_id = request.args.get("id")
    if account_id != None:
        try:
            account_id = int(account_id)
        except:
            return {
                "status":"Account ID is in an invalid format"
            }, 400
        
        db = sqlite3.connect("accounts.db")
        cur = db.cursor()
        res = cur.execute("SELECT * FROM accounts WHERE id=?", (account_id,))
        account = res.fetchone()

        if account != None:
            return {
                "status":"Success",
                "account":account
            }
        else:
            return {
                "status":"User not found"
            }, 404
    else:
        return {
            "status":"Success",
            "account":get_accounts()
        }
    
@app.route("/accounts/len", methods=['GET'])
def accounts_len():
    db = sqlite3.connect("accounts.db")
    cur = db.cursor()
    res = cur.execute("SELECT COUNT(*) FROM accounts")
    accountslen = res.fetchone()

    print(accountslen)

    return {
        "status":"Success",
        "accountslen":accountslen[0]
    }

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
                res = cur.execute("INSERT INTO posts (user, title, body) VALUES (?,?,?)", (final[0], title, body))
                db.commit()
                res.close()
                print(f"{final[0]} created a post")
                return {
                    "status":"Success"
                }
            else:
                return {
                    "status":"Invalid token"
                }, 403
        else:
            return {
                "status":"No token found"
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
            return {
                "status":"Success",
                "post":get_posts()
            }
        
@app.route("/login/", methods=['POST'])
def login():
    delete_expired()
    data = request.json
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
                "status":"Wrong login credentials"
            }, 403
    else:
        return {
            "status":"No such account"
        }, 404

@app.route("/register/", methods=['POST'])
def register():
    delete_expired()
    data = request.json
    username = data["user"]
    password = data["password"]
    email = data["email"]

    if username and password and email:
        if user_exists(username):
            return {
                "status":"Account already exists"
            }, 400
        elif len(password) < 5:
            return {
                "status":"Password should include at least 5 characters"
            }, 400
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {
                "status":"E-Mail is in an invalid E-Mail format"
            }, 400

        print(f"Request from {username} at Register")

        current_time = time.time()
        expires = current_time + 600
        code = random.randint(10000, 99999)

        # Save authentication code and info into database
        db = sqlite3.connect("accounts.db")
        cur = db.cursor()
        res = cur.execute("SELECT * FROM auth WHERE user=?", (username,))

        cur.execute("INSERT INTO auth (user, password_hash, email, code, expires) VALUES (?,?,?,?,?)", (username, hash_string(password), email, code, expires))
        db.commit()

        # Send verification code via E-Mail
        body = f"""
        Here is your authentication code:
        {code}

        Please don't share this code to anyone to avoid people getting into your account.

        This is an automated E-Mail. Any E-Mails that get sent to this account will get ignored. 
        If you get spammed by this account, please report this activity to https://silk-project.github.io/contact
        """

        em = EmailMessage()
        em["From"] = email_sender
        em["To"] = email_sender
        em["Subject"] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", email_port, context=context) as server:
                server.login(email_sender, email_password)
                server.sendmail(email_sender, email, em.as_string())
                print("Success sending E-Mail!")
        except:
                print("An error occured while trying to send an authentication E-Mail.")

        print("Account Authentication Active.")

        return {
            "status":"Success"
        }
    else:
        return {
            "status":"Login credentials are missing"
        }, 400
    
@app.route("/register/auth", methods=['POST'])
def auth():
    delete_expired()
    data = request.json
    username = data["user"]
    code = int(data["code"])

    if username and code:
        db = sqlite3.connect("accounts.db")
        cur = db.cursor()
        res = cur.execute("SELECT * FROM auth WHERE user=?", (username,))
        auth_info = res.fetchone()

        print(f"Request from {username} at Authentication")

        if auth_info == None:
            return {
                "status":"Authentication did not happen"
            }, 400
        
        if auth_info[3] == code and time.time() < auth_info[4]:
            cur.execute("INSERT INTO accounts (user, password, email) VALUES (?,?,?)", (auth_info[0], auth_info[1], auth_info[2]))
            db.commit()
            print("Account added")
            return {
                "status":"Success"
            }
        else:
            return {
                "status":"Invalid Code"
            }, 400
    else:
        return {
            "status":"Code or / and Username is missing"
        }, 400

@app.errorhandler(404)
def page_not_found(error):
    return {
        "status":"Not found"
    }, 404
