# PSET9: FINANCE
# https://cs50.harvard.edu/extension/2020/fall/psets/9/finance/
import os
import re


from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)
app.secret_key = "abc" 

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
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        price = request.form.get("price")
        name = request.form.get("name")
        user_id = session["user_id"]

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
        # Stock is a dictionary where the keys are "name", "price", and "symbol"
        stock = lookup(request.form.get("symbol"))
        if not request.form.get("symbol"):
            return apology("Please input in the stock symbol")
        else:
            return redirect("/quoted.html", symbol=symbol)
    return render_template("/quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Require that a user input in a username, implemented as a text field whose name is username./ Render an apology if the user's input is blank or the username already exists
    # Validate submission
    if request.method == "POST":
        # Ask for the username
        username = request.form.get("username")
        if not username:
            return apology("Please input in your username, puta.", 403)

        # CHECK: Username and re-entered username match
        re_enter_username = request.form.get("re_enter_username")
        if username != re_enter_username:
            return apology("Usernames do not match.", 403)

        # CHECK: Email entered
        email = request.form.get("email")
        if not email:
            return apology("No email entered", 403)

        # CHECK: Email entered
        re_enter_email = request.form.get("re_enter_email")
        if username != re_enter_email:
            return apology("Emails do not match.", 403)

        # Please submit the password
        password = request.form.get("password")
        if not password:
            return apology("Please input in your password.", 403)
        
        # CHECK: If new user check the password and 2nd confirmation password match before saving
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return apology("Passwords do not match.", 403)

        # Check50 requires you to include a confirm your password section
        # CHECK: Check if user name already exists
        # Ensuring that the username is unique
        unique = db.execute("SELECT username FROM users WHERE username = ?", username)
        if len(unique) >= 1:
            return render_template("login.html", error="Sorry but the username already exists! Please enter in a new one.")
        else:
            # CALCULATE: Encrypt password
            hash = generate_password_hash(password)
            # hash = check_password_hash.encrypt(password)

            # ACTION: Insert new username and encrypted password into database
            rows = db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", (username, hash))

        # Remembering session
        rows               = db.execute("SELECT * FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        # Confirmation that the user has registered
        # TODO this message should be on index.html flash("Congrats on joining C$50 Finance. Please do not go bankrupt playing with stocks.")

        # Redirect to home page
        return redirect(url_for(index), 200)
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
