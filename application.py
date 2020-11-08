# PSET9: FINANCE
# https://cs50.harvard.edu/extension/2020/fall/psets/9/finance/
import os
import re


from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

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

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Will need to display an HTML table summarising, for the user currently logged in, which stocks the user owns, the number of shares owend, the current price of each stock and the total value of each holding (i.e. shares time price). Also display the user's current cash balance along with the grand total
    # Odds are you’ll want to execute multiple SELECTs. Depending on how you implement your table(s), you might find GROUP BY HAVING SUM and/or WHERE of interest.
    # Odds are you’ll want to execute multiple SELECTs. Depending on how you implement your table(s), you might find GROUP BY HAVING SUM and/or WHERE of interest.

    # Need to connect to the db
    with sqlite3.connect("finance.db") as connection:
        # User balance
        user_connection_db = users_db(connection)
        user_connection.db.set_id(session["user_id"])

        # Getting the user's balance
        user_balance = int(user_connection.get_balance()[0])

        # Amount of shares the user owns - need to set it at 0 so that it can turn into a counter
        amount_shares = 0

        # Portfolio Holdings
        portfolio_holding = portfolio_db(session["user_id"], connection)

        for portfolio in portfolio_holding:
            portfolio["price"] = lookup(portfolio["symbol"]["price"])
            portfolio["total"] = portfolio["price"] * int(portfolio["shares"])
            portfolio["name"] = lookup(portfolio["name"])

            amount_shares += portfolio["total"]

        # Need to create a dictionary for the user
        user = {}
        user["balance"] = users_balance
        user["grand_total"] = users_balance + share_total

    return render_template("index.html", portfolio_holding = portfolio_holding, user = user)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # Require that a user input a stock’s symbol, implemented as a text field whose name is symbol. Render an apology if the input is blank or the symbol does not exist (as per the return value of lookup).
    if request.method == "POST":
    # Need to define symbol and price
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        price = request.form.get("price")

        # Need to ensure that the customer can not buy a non-integer of a share nor a negative number
        if not request.form.get("shares").isdigit():
            return apology("Are you trying to troll us? You can't buy a negative stock. You can not buy a fraction of a stock.")

        # So the customer know that s/he is not a broke ass
        cash_balance = db.execute("SELECT cash FROM users WHERE id = :id", id = session["user_id"])

        # Need to ensure that the stock ticker exists
        if quote is None:
            return apology("Please input in the correct stock ticker.")

        # Calculating the price of the number of stocks the customer would like to purchase
        purchasing_share =  quote["price"] * int(request.form.get("shares"))

        # No broke-ass
        if cash_balance[0]["cash_balance"] < purchasing_share:
            return apology("Yo, broke-ass. You can't afford it. Decrease the amount of shares you want to buy.", 400)
        # In the event that the sales go thru
        else:
            # Subtract the amount of cash you have left from the balance and append the newly purchased shares to the db
            db.execute("UPDATE users SET cash = :cash_balance - :purchasing_share WHERE username = :user_id", cash_balance = cash_balance[0]["cash_balance"], purchasing_share = purchasing_share, user_id = session[user_id])

            # Updating the transactions onto the table
            db.execute("INSERT INTO transaction_history(user_id, stock_name, stock_symbol, action, brought_shares, price VALUES(:user, :stock_name, :stock_symbol, :action, :brought_shares, :price)",
            user_id=session["username"], stock_name = quote["name"], stock_symbol = quote["symbol"], action = "Purchased", brought_shares = int(request.form.get("shares")), price = purchasing_share)

            # Send the customer back to his/her portfolio
            return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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
    # Require that a user input a stock's symbol, implemented as a text field whose name is symbol
    # Submit the user's input via POST to /quote
    if request.method == "POST":
        # Stock is a dictionary where the keys are "name", "price", and "symbol"
        stock = lookup(request.form.get("symbol"))
        if not request.form.get("symbol"):
            return apology("Please input in the stock symbol")
        else:
            return redirect("/quoted.html", stock = stock)
    return render_template("/quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Require that a user input in a username, implemented as a text field whose name is username./ Render an apology if the user's input is blank or the username already exists
    # Validate submission
    if request.method == "POST":
        # Ask for the username
        if not request.form.get("username"):
            return apology("Please input in your username, puta", 403)
        # Please submit the password
        elif not request.form.get("password"):
            return apology("Please input in your password", 403)
        # Check50 requires you to include a confirm your password section
        elif not request.form.get("password") != request.form.get("confirmation"):
            return apology("Are you sure you aren't trying to steal someone's funds? Please input the correct password. Remember, we are always watching.", 403)

    ## Creation of variables
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

    # Ensuring that the username is unique
        unique = db.execute("SELECT username FROM users WHERE username = :username", username = username.request.form.get("username"))

        if len(unique) != 0:
            return render_template("login.html", error = "Sorry but thec username already exists! Please enter in a new one")
        else:
            encrypted = check_password_hash.encrypt(request.form.get("password"))
            rows = db.execute("INSERT INTO users (username, password) VALUES(:username, :password)", username = username.form.get("username"), password = encrypted)

    # Remembering session
        #rows = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
            session["user_id"] = rows[0]["id"]
    # Confirmation that the user has registered
        flash("Congrats on joining C$50 Finance. Please do not go bankrupt playing with stocks.")
    # Redirect to home page
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
