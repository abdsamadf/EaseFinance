import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from pytz import timezone
from time import gmtime, strftime


from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    total_balance = 0;
    # Select all data from portfolio table for login user
    stocks = db.execute("SELECT * FROM portfolios WHERE users_id = :users_id", users_id=session['user_id'] )

    # Select cash from users table
    cash = db.execute("SELECT cash FROM users WHERE id = :users_id", users_id=session['user_id'])
    cash = cash[0]['cash']

    # if stocks data doesn't already exist
    if not stocks and cash == 10000:
        # New user reached route via (as by clicking a link or via redirect)
        return render_template("index.html", cash_balance=usd(cash), total_balance=usd(10000))

    # Format stock price and price of shares
    for stock in stocks:
        total_balance += stock['shares'] * stock['price']
        stock["price"] = usd(stock["price"])
        stock["price_of_shares"] = usd(stock["price_of_shares"])

    # total balance is grand total of cash + stock total value
    total_balance += cash;

    # User reached route via (as by clicking a link or via redirect)
    return render_template("index.html", stocks=stocks, cash_balance=usd(cash), total_balance=usd(total_balance))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST(as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure symbol was submitted
        if not symbol:
            return apology("missing symbol", 400)

        # Ensure shares was submitted
        if not shares:
            return apology("missing shares", 400)

        # Cast shares to integer
        shares = int(shares)

        # Ensure shares was valid
        if shares < 0:
            return apology("invalid shares")

        # Retrieve stock quote
        quote = lookup(request.form.get("symbol"))

        # Ensure stock quote is valid
        if not quote:
            return apology("invalid symbol", 400)

        # Select cash from users table
        cash = db.execute("SELECT cash from users WHERE id = :users_id", users_id = session['user_id'])

        cash = cash[0]['cash']

        # total price of shares
        price_of_shares = quote['price'] * shares

        # Ensure user afford the stock
        if price_of_shares > cash:
            return apology("can't afford", 400)

        # Select user shares of symbol
        user_shares = db.execute("SELECT shares FROM portfolios \
                WHERE users_id = :users_id AND symbol = :symbol",
                                users_id=session["user_id"],
                                symbol=quote["symbol"])

        # Insert transaction data in history table
        history = db.execute("INSERT INTO history (users_id, shares, symbol, price, transacted) \
                    VALUES(:users_id, :shares, :symbol, :price, :transacted)",
                    users_id=session['user_id'],
                    shares=shares,
                    symbol=quote["symbol"],
                    price=quote["price"],
                    transacted=strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        # If user doesn't already have that stock --> create a new object
        if not user_shares:
            db.execute("INSERT INTO portfolios (shares, symbol, users_id, price, price_of_shares, name) \
                        VALUES(:shares, :symbol, :users_id, :price, :price_of_shares, :name)",
                    shares=shares,
                    symbol=quote["symbol"],
                    users_id=session["user_id"],
                    price=quote["price"],
                    price_of_shares=price_of_shares,
                    name=quote["name"])

        # buying the same stock
        # If user already has it --> increase number of shares and price of shares
        else:
            shares_total = int(user_shares[0]["shares"]) + shares
            price_of_shares_total = quote["price"] * shares_total
            db.execute("UPDATE portfolios SET shares=:shares, \
                        price_of_shares=:price_of_shares, \
                        price=:price \
                        WHERE users_id=:users_id AND symbol=:symbol",
                    shares=shares_total,
                    users_id=session["user_id"],
                    symbol=quote["symbol"],
                    price=quote["price"],
                    price_of_shares=price_of_shares_total)

        # update cash
        db.execute("UPDATE users SET cash = cash  - :price_of_shares WHERE id = :users_id", price_of_shares = price_of_shares, users_id = session['user_id'])

        # Redirect user to home page
        return redirect('/')

        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Select all data from history table for login user
    transactions = db.execute("SELECT * FROM history WHERE users_id = :users_id", users_id=session['user_id'])

    # Format price
    for transaction in transactions:
        transaction["price"] = usd(transaction["price"])

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("history.html", transactions = transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        # Retrieve stock quote
        quote = lookup(request.form.get("symbol"))

        # Ensure stock quote is valid
        if not quote:
            return apology("invalid symbol", 400)

        return render_template("quoted.html", name=quote["name"], price=usd(quote["price"]), symbol=quote["symbol"])

    # User reached route via GET (as by clicking a link)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST(as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation password", 403)

        # Check password match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Hash the password
        hash_password = generate_password_hash(request.form.get("password"), )

        # Insert username and hash in database
        new_user_id = db.execute("INSERT INTO users(username, hash) VALUES(:username, :hash)",
                    username=request.form.get("username"), hash=hash_password)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exist
        if not new_user_id:
            return apology("usename already exists")

        # Remember which user has logged in
        session["user_id"] = new_user_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Select all data from portfolio table for login user
    stocks = db.execute(
        "SELECT * FROM portfolios WHERE users_id = :users_id", users_id=session['user_id'])

    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure symbol was submitted
        if not symbol:
            return apology("missing symbol", 400)

        # Ensure shares was submitted
        if not shares:
            return apology("missing shares", 400)

        # Cast shares to integer
        shares = int(shares)

        # Ensure shares was valid
        if shares < 0:
            return apology("invalid shares")

        # Ensure user has that many shares
        if shares > stocks[0]["shares"]:
            return apology("too many shares", 400)

        quote = lookup(symbol)

        price_of_shares = quote["price"] * shares

        # Insert transaction data in history table
        history = db.execute("INSERT INTO history (users_id, shares, symbol, price, transacted) \
                    VALUES(:users_id, :shares, :symbol, :price, :transacted)",
                             users_id = session['user_id'],
                             shares = -shares,
                             symbol = quote["symbol"],
                             price = quote["price"],
                             transacted = strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        # Select user shares of symbol
        user_shares = db.execute("SELECT shares FROM portfolios \
                WHERE users_id = :users_id AND symbol = :symbol",
                                 users_id=session["user_id"],
                                 symbol=quote["symbol"])

        # update stock user portfolio if user have enough stock to sell
        if user_shares[0]["shares"] > shares:
            shares_diff = int(user_shares[0]["shares"]) - shares
            price_of_shares_diff = quote["price"] * shares_diff
            db.execute("UPDATE portfolios SET shares=:shares, \
                        price_of_shares=:price_of_shares \
                        WHERE users_id=:users_id AND symbol=:symbol",
                       shares=shares_diff,
                       users_id=session["user_id"],
                       symbol=quote["symbol"],
                       price_of_shares=price_of_shares_diff)

        elif user_shares[0]["shares"] < shares:
            return apology("too many shares", 400)

        # remove stock from user portfolio if user shares == shares
        else:
            db.execute("DELETE FROM portfolios WHERE users_id = :users_id AND symbol = :symbol", users_id = session['user_id'], symbol = symbol)


        # update cash
        db.execute("UPDATE users SET cash = cash + :price_of_shares WHERE id = :users_id",
                   price_of_shares=price_of_shares, users_id=session['user_id'])

        # Redirect user to home page
        return redirect("/")
    else:
        # User reached route via GET (as by clicking a link or via redirect)
        return render_template("sell.html", stocks = stocks)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
