# 🪡 Silk-Forum
Source Code of the Silk Forum Backend using Flask and SQLite3.

## ⚡️ Features
- Basic SQL Injection Protection
- Simple token system to keep the user logged in
- API routes to fetch all users or posts
- Passwords are hashed in the database
- Error handling and redirections
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

Next, it will ask you to enter an admin password which will be added to the database.

## 🗺️ Routes
- `GET /` : Returns a welcome message
- `GET /accounts/` : Returns every user in the database
- `GET /post/` : Returns every post in the database
- `GET /post/<id>` : Returns a post with a specific id
- `POST /post/` : Adds a post to the database using a username, title and body
- `POST /register/` : Registers a new user using a username and password
- `POST /login/` : Log in a user and return a token if it doesn't exist or expires
