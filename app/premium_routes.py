from flask import render_template, request, redirect, session, make_response, Blueprint
from paypalrestsdk import Payment, set_config

from pythonHelper import SQLHelper, MailHelper
import credentials


premium_route = Blueprint("Premium", "Premium", template_folder='templates')

# Configure PayPal SDK
set_config({
    'mode': 'live',
    'client_id': credentials.paypal_client_id,
    'client_secret': credentials.paypal_client_secret
})

def pay_with_PayPal(success_url="http://127.0.0.1:5000/success", cancel_url="http://127.0.0.1:5000/cancel", amount=2.99, description="GrütteChat PLUS"):
    """ Pay with PayPal

    Args:
        amount (float): The amount to pay
    """
    amount = round(float(amount), 2)
    
        # Create PayPal payment object
    payment = Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": f"{success_url}",
            "cancel_url": f"{cancel_url}"
        },
        "transactions": [{
            "amount": {
                "total": f"{amount}",
                "currency": "EUR"
            },
            "description": f"{description}"
        }]
    })
    
    # Create payment
    if payment.create():
        for link in payment.links:
            if link.method == "REDIRECT":
                return redirect(link.href)
    else:
        return "Something went wrong on our end :/"

@premium_route.route("/premium", methods=["GET"])
def premium():
    """ Premium route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect("/")
    
    # Get user from database
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")

    # If empty, something went wrong, most likely sql connection issue
    if user == []:
        return render_template("settings.html", error="Something went wrong on our end :/", selected_personality="Default", has_premium=False)
    
    # If good to go, check if user has premium
    else:

        # If user has premium, redirect to settings page
        if bool(user[0]["has_premium"]) == True:
            return render_template("settings.html", error="You already have GrütteChat PLUS!", selected_personality=user[0]["ai_personality"], has_premium=True)
        
        # If user does not have premium, render premium ad page
        else:
            return render_template("premium.html")
        
@premium_route.route('/payment', methods=['POST'])
def payment():
    """ PayPal payment route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect("/")

    # Get user from database
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
    
    # If empty, something went wrong, most likely sql connection issue
    if user == []:
        return render_template("settings.html", error="Something went wrong on our end :/", selected_personality="Default", has_premium=False)
    
    # If everything looks good, check if user has premium
    else:
        
        # If user has premium, redirect to settings page
        if bool(user[0]["has_premium"]) == True:
            return render_template("settings.html", error="You already have GrütteChat PLUS!", selected_personality=user[0]["ai_personality"], has_premium=True)
        
        # Else, create payment and redirect user to PayPal
        else:

            paypal_response = pay_with_PayPal(amount=2.99, description="GrütteChat PLUS")
            
            if paypal_response != "Something went wrong on our end :/":
                return paypal_response
            
            # Payment creation failed
            else:
                return render_template("premium.html", error="Payment error, please try again." )

@premium_route.route('/success')
def success():
    """ Success payment route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect("/")
    
    # Get user from database
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(session['username'])}'")
   
    # If empty, something went wrong, most likely sql connection issue
    if user == []:
        return render_template("settings.html", error="Something went wrong. Please contact customer support.", selected_personality="Default", has_premium=False)
    
    # If good to go, check if user has premium
    if bool(user[0]["has_premium"]) == True:
        return render_template("settings.html", error="You already have GrütteChat PLUS!", selected_personality=user[0]["ai_personality"], has_premium=True)
    
    try:

        # Retrieve payment details from PayPal
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        payment = Payment.find(payment_id)
        
        # If successful, update user in database
        if payment.execute({"payer_id": payer_id}):
            sql.writeSQL(f"UPDATE gruttechat_users SET has_premium = {True} WHERE username = '{str(session['username'])}'")
            return render_template("settings.html", error="You now have GrütteChat PLUS!", selected_personality="Default", has_premium=True)
        
        # Else if payment failed, return error
        else:
            return render_template("premium.html", error="Payment execution failed, please try again." )
        
    # Something went wrong
    except:
        return render_template("settings.html", error="Something went wrong.", selected_personality="Default", has_premium=False)

@premium_route.route('/cancel')
def cancel():
    """ Cancel payment route

    Returns:
        str: Rendered template
    """    
    if "username" not in session:
        return redirect("/")

    # Payment cancelled error
    return render_template("settings.html", error="Payment cancelled.", selected_personality="Default", has_premium=False)


@premium_route.route("/tip/<recipient>", methods=["GET"])
def tip(recipient):
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    
    recipient_database = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(recipient)}'")
    if recipient_database == []:
        return redirect("/")
    
    return render_template("tip.html", recipient=str(recipient))

@premium_route.route("/tip/<recipient>/<value>", methods=["GET"])
def tip_amount(recipient, value):
    if "username" not in session:
        return redirect("/")
    
    sql = SQLHelper.SQLHelper()
    email = MailHelper.MailHelper()
    
    if value == "success":
    
        # Retrieve payment details from PayPal
        payment_id = request.args.get('paymentId')
        payer_id = request.args.get('PayerID')
        payment = Payment.find(payment_id)
        
        # If successful, update user in database
        if payment.execute({"payer_id": payer_id}):
            transactions = payment.transactions
            if transactions:
                amount = transactions[0].amount
                paid_amount = amount.total
                
                recipient_database = sql.readSQL(f"SELECT username, balance, email FROM gruttechat_users WHERE username = '{str(recipient)}'")
                if recipient_database == []:
                    return redirect("/")
    
                new_balance = int(recipient_database[0]["balance"]) + int(float(str((paid_amount))))
                
                sql.writeSQL(f"UPDATE gruttechat_users SET balance = {new_balance} WHERE username = '{str(recipient)}'")
                email.send_tip_email(recipient_email=recipient_database[0]["email"], username_received=recipient_database[0]["username"], username_send=session["username"], paid_amount=paid_amount)

            return render_template("tip.html", recipient=recipient, error="Payment successful! Thank you.")
        
        # Else if payment failed, return error
        else:
            return render_template("tip.html", recipient=recipient, error="Payment execution failed, please try again." )

    elif value == "cancel":
        return render_template("tip.html", recipient=recipient, error="Payment cancelled.")

    elif not value.isnumeric():
        return redirect("/")
    elif int(value) not in [1, 2, 5, 10]:
        return redirect("/")
        
    recipient_database = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(recipient)}'")
    if recipient_database == []:
        return redirect("/")
    
    paypal_response = pay_with_PayPal(amount=int(value), description=f"Tipping {recipient} on GrütteChat", success_url=f"http://127.0.0.1:5000/tip/{str(recipient)}/success", cancel_url=f"http://127.0.0.1:5000/tip/{str(recipient)}/cancel")
            
    if paypal_response != "Something went wrong on our end :/":
        return paypal_response
    
    # Payment creation failed
    else:
        return render_template("tip.html", recipient=recipient, error="Payment error, please try again.")