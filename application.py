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

        # Setting up variable and pulling up from the database
        portfolio_holdings = db.execute("SELECT * FROM users WHERE username = :username ORDER BY symbol ASC", user_id = session["user_id"])
        user = db.execute("SELECT * FROM users WHERE id = :id", id = session["user_id"])

        # Amount of shares the user owns - need to set it at 0 so that it can turn into a counter
        amount_shares = 0

        for i in range(len(portfolio_holdings)):
            stock = lookup(portfolio_holdings[i]["symbol"])
            portfolio_holdings[i]["co_name"] = stock["name"]
            portfolio_holdings[i]["current_price"] = "%.2f"%(stock["price"])
            portfolio_holdings[i]["current_total"] = "%.2f"%(stock["price"]) * float(portfolio_holdings[i]["shares_held"])
            portfolio_holdings[i]["profit"] = "%.2f"%(portfolio_holdings[i]["current_total"]) - float(portfolio_holdings[i]["total"])
            cash_bal += portfolio_holdings[i]["total"]
            portfolio_holdings[i]["total"] = "%.2f"%(portfolio_holdings[i]["total"])

        cash_bal += float(user[0]["cash"])

    return render_template("index.html", portfolio_holdingsg = portfolio_holdings, cash = usd(user[0]["cash"], cash_bal = usd(cash_bal)))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
# Require that a user input a stock’s symbol, implemented as a text field whose name is symbol. Render an apology if the input is blank or the symbol does not exist (as per the return value of lookup).
    if request.method == "POST":
    # Need to define symbol and price
    # Stock symbol
        symbol = request.form.get("symbol")
    # Amount of shares owned
        shares = request.form.get("shares")
    # Price per share
        price = request.form.get("price")
    # Company name
        name = request.form.get("name")
        user_id = session["user_id"]

        # Need to ensure that the symbol and the amount of shares are submitted
        if not request.form.get("symbol") or not request.form.get("shares") or int(request.form.get("shares")) < 1:
            return render_template(url_for("buy"))
        # Need to look up the stock
        stock = lookup(symbol)

        # Need to ensure that the symbol exists
        if not stock:
            return apology("Symbol could not be found")

        # Calculating the total price
        total_price = float(stock["price"]) * int(shares)

        # Inserting them into the database
        row = db.execute("SELECT * FROM users WHERE username: ?", username = user_id)
        cash_inhand = float(user[0]["cash"])

        # Checking to see if the user can even afford it
        if cash_inhand < total_price:
            return apology("Sorry but you can not afford it. You only have this much: " + str("%.2f"%cash_inhand))
        # New balance
        new_balance = total_price - cash_inhand

        # If the stock is already owned, the database will need to be updated
        # Check
        transaction_db = db.execute("SELECT * FROM stocks WHERE user_id = ? and symbol = ?", username=user_id, symbol=symbol)

        # Updating with new price and amount if it is already owned
        if len(transaction_db) == 1:
            new_amount = int(transaction_db[0]["shares"] + int(shares))
            new_total = float(transaction_db[0]["total"] + total_price)
            new_price_per_share = "%.2f"%(new_total / float(new_amount))

            db.execute("UPDATE transactions SET amount=:amount, total=:total, price_per_share=:price_per_share WHERE username=:user_id AND symbol=:symbol, amount=:new_amount, total=:new_total, price_per_share=:new_price_per_share")

            # Otherwise create a new entry
        else:
            db.execute("INSERT INTO transactions (user_id, action, symbol, shares,  total, price_per_share) VALUES (?, ?, ?, ?, ?, ?)", username=user_id, action=1, symbol=symbol, shares=shares, total=total, price_per_share=stock["price"])
            return render_template(url_for("history"))
    else:
        return render_template("buy.html")
    

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Complete the implementation of history in such a way that it displays an HTML table summarizing all of a user’s transactions ever, listing row by row each and every buy and every sell.
    # For each row, make clear whether a stock was bought or sold and include the stock’s symbol, the (purchase or sale) price, the number of shares bought or sold, and the date and time at which the transaction occurred.
    # You might need to alter the table you created for buy or supplement it with an additional table. Try to minimize redundancies.

    # Need to connect to the database
    with sqlite3.connect("finance.db") as connection:
        # Pull up the records for the transactions
        transactions = db.execute("SELECT * FROM transaction_history WHERE username = :username ORDER BY date DESC", username = session["user_id"])
        # Calculating the total transactions
        for row in range(len(transactions)):
            transactions[i]["total_shares"] = "%.2f"%(float(transactions[i]["amount"]) * float(transactions[i]["price"]))
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
            return apology("must provide username", 200)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 200)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 200)

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
        symbol = request.form.get("symbol")
        if not symbol:
        # Stock is a dictionary where the keys are "name", "price", and "symbol"
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Sorry but the stock symbol you input in is incorrect. Try again")
        return render_template("quoted.html", name = stock["name"] symbol = stock["symbol"], price = stock["price"])
    # Need to redirect in the event that they arrive via link. They will still need to input in the stock quote 
    else: 
        return redirect(url_for(quote))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Require that a user input in a username, implemented as a text field whose name is username./ Render an apology if the user's input is blank or the username already exists
    # Validate submission
    # Require that a user input in a username, implemented as a text field whose name is username./ Render an apology if the user's input is blank or the username already exists
    # Validate submission
            if request.method == "POST":
        # Ask for the username
        username = request.form.get("username")
        if not username:
            return apology("Please input in a username, puta")
        # Confirm username matches
        re_enter_username = request.form.get("re_enter_username")
        if username != re_enter_username:
            return apology("Please make sure the username matches one another")
        # Email confirmmation
        email = request.form.get("email")
        if not email:
            return apology("Please input in your email")
        # Confirmation of email
        re_enter_email = request.form.get("re_enter_email")
        if email != re_enter_email:
            return apology("Mis-matching email")
        # Please submit the password
        password = request.form.get("password")
        if not password:
            return apology("Please input in a password")
        # Check50 requires you to include a confirm your password section
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return apology("Please make sure the passwords match one another.")

    # Ensuring that the username is unique
        unique = db.execute("SELECT * FROM users WHERE username = ?, email = ?", username, email)

        if len(unique) >= 1:
            return render_template("login.html", error="Sorry but the username already exists! Please enter in a new one.")
        else:
            hash = generate_password_hash(password)
            rows = db.execute("INSERT INTO users (username, password, email) VALUES(?, ?, ?)", (username, hash, email))

    # Remembering session
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

    # Redirect to home page
        return redirect(url_for("index"))
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Complete the implementation of sell in such a way that it enables a user to sell shares of a stock (that he or she owns).
    # Require that a user input a stock’s symbol, implemented as a select menu whose name is symbol. Render an apology if the user fails to select a stock or if (somehow, once submitted) the user does not own any shares of that stock.
    # Require that a user input a number of shares, implemented as a text field whose name is shares. Render an apology if the input is not a positive integer or if the user does not own that many shares of the stock.
    if request.method == "POST":
        # Need to connect with the database so that we know what is available to be sold
        with sqlite3.connect("finance.db") as connection:
            user_id = session["user_id"]
            symbol = request.form.get("symbol")
            shares_to_sell = int(request.form.get("shares"))

            # Portfolio holdings
            user_connection_db = portfolio_db(user_id, connection)
            portfolio_holdings = user_connection_db.get_holdings()

            # If the user wishes to be troll and input in a fraction or doesn't own any of that stock
            if shares_to_sell <= 0:
                return apology("Are you an idiot? Why are you trying to sell a share in which the share is 0?")
            if user_connection_db.number_of_shares_owned(symbol) == None:
                return apology("Are you an idiot? Why are you trying to sell a share when you don't own that share?")
            # If the user does not have enough shares to sell

            current_amount_of_shares_owned = int(user_connection_db.get_number_of_shares(symbol)[0])

            if current_amount_of_shares_owned < shares_to_sell:
                return apology("Please decrease the amount of shares you wish to sell. You aren't going to steal money from us")

            # In the event that the user has enough to sell - you'll need the current price
            current_share_price = lookup(symbol)["price"]

            # Getting the user's current USD balance
            cash_db = users_db(connection)
            cash_db.set_id(session["user_id"])
            current_used_balance = cash_db.get_balance()[0]

            # New balance
            new_balance = current_usd_balance + (current_share_price * shares_to_sell)

            # Updating balance
            cash_db(new_balance)

            # Need to remember to subtract from the shares
            user_connect_db.update_shares((current_amount_of_shares_owned - shares_to_sell), symbol)

            # Updating transaction history
            transaction_db = transactions_db(user_id, connection)
            transaction_db.insert(("sold", symbol, share_price, str(shares_to_sell), get_time()))

        return redirect("/history")

    return render_template("sell.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
