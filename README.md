# 🪡 Silk-Forum
Source Code of the Silk Forum Backend using Flask and SQLite3.

## ⚡️ Features
- Basic SQL Injection Protection
- Simple token system to keep the user logged in
- API routes to fetch all users or posts
- Passwords are hashed in the database
- Error handling and redirections
- E-Mail code verification at registration
- Easily extensible code

## ⚙️ Usage

### Requirements
- `python3`
- `flask`

### Running the app
To run the app, type in the following command:
```
flask run
```

Next, it will ask you to enter an admin password which will be added to the `accounts.db` database.

## 🗺️ Routes
- `GET /` : Returns a welcome message
- `GET /validate/` : Checks if a user is logged in using a token, returns a status if it is valid or not
- `GET /accounts/` : Returns every user in the `accounts.db` database
- `GET /post/` : Returns every post in the `posts.db` database
- `GET /post/<id>` : Returns a post with a specific id
- `POST /post/` : Adds a post to the database using a username, title and body
- `POST /register/`, `POST /register/auth` : Registers a new user using a username and password
- `POST /login/` : Log in a user and return a token if it doesn't exist or expires
