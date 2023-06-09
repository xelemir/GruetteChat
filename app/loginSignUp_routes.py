from flask import render_template, request, redirect, session, Blueprint
import random

from pythonHelper import EncryptionHelper, SQLHelper, MailHelper
from config import url_prefix, templates_path
    
loginSignUp_route = Blueprint("LoginSignUp", "LoginSignUp", template_folder=templates_path)

eh = EncryptionHelper.EncryptionHelper()

@loginSignUp_route.route('/login', methods=['POST', 'GET'])
def login():
    if "signup" in request.form:
        return redirect(f'{url_prefix}/signup')
    elif request.method == "GET":
        return redirect(f'{url_prefix}/')
    
    sql = SQLHelper.SQLHelper()
    username = str(request.form['username'])
    password = str(request.form['password'])
    
    # Check if input is valid
    if username == '' or password == '':
        return render_template('login.html', error='Please enter a username and password', url_prefix = url_prefix)
    
    # Search for user in database
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
    
    # If user exists, check if password is correct
    if user != []:
        decrypted_password = eh.decrypt_message(user[0]["password"])
        
        # If username and password are correct
        if user[0]["username"] == username and decrypted_password == password:
            
            # Check if the user has verified their account
            if bool(user[0]["is_verified"]) == False:
                return redirect(f'{url_prefix}/verify/{username}')
            
            # Log the user in
            else:
                session['username'] = username
                response = redirect(f'{url_prefix}/chat')
                response.set_cookie('username', username)
                return response

        # If password is or username is incorrect
        else:
            return render_template('login.html', error='Invalid login credentials', url_prefix = url_prefix)
        
    # If user does not exist
    else:
        return render_template('login.html', error='Invalid login credentials', url_prefix = url_prefix)

@loginSignUp_route.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'username' in session:
        return redirect(f'{url_prefix}/chat')
    
    # If Method is POST
    if request.method == 'POST':
        
        mail = MailHelper.MailHelper()
        sql = SQLHelper.SQLHelper()
        username = str(request.form['username'])
        email = str(request.form['email'])
        password = str(request.form['password'])
        password_confirm = str(request.form['password2'])
        
        # Check if input is valid
        if password != password_confirm:
            return render_template('signup.html', error='Passwords do not match', url_prefix = url_prefix)
        elif username == '' or password == '':
            return render_template('signup.html', error='Please enter a username and password', url_prefix = url_prefix)
        elif len(username) > 20:
            return render_template('signup.html', error='Username must be less than 20 characters', url_prefix = url_prefix)
        elif len(password) > 40 or len(password) < 8:
            return render_template('signup.html', error='Password must be between 8 and 40 characters', url_prefix = url_prefix)
        elif '@' not in email or '.' not in email:
            return render_template('signup.html', error='Please enter a valid email address', url_prefix = url_prefix)
        
        # Check if the username already exists
        search_username = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{username}'")
        if search_username != []:
            return render_template('signup.html', error='Username already exists', url_prefix = url_prefix)
        
        # Else create new user
        else:
            encrypted_password = str(eh.encrypt_message(str(password)))        
            verification_code = str(random.randint(100000, 999999))

            # Insert the user into the database
            sql.writeSQL(f"INSERT INTO gruttechat_users (username, password, email, verification_code, is_verified, has_premium, ai_personality, premium_chat, balance) VALUES ('{username}', '{encrypted_password}', '{email}', '{verification_code}', {False}, {False}, 'Default', {False}, 0)")
            
            # Send the email
            mail.send_verification_email(email, username, verification_code)
            
            # Redirect to verification page
            return redirect(f"{url_prefix}/verify/{username}")

    # If Method is GET, render the signup page
    return render_template('signup.html', url_prefix = url_prefix)

@loginSignUp_route.route('/verify/<username>' , methods=['GET', 'POST'])
def verify(username):
    if "username" in session or username is None:
        return redirect(f'{url_prefix}/')
    
    error = None
    sql = SQLHelper.SQLHelper()
    user = sql.readSQL(f"SELECT * FROM gruttechat_users WHERE username = '{str(username)}'")
    
    # User does not exist
    if user == []:
        return redirect(f'{url_prefix}/')
    
    # User exists
    else:
        # Get email and verification code from database 
        email = user[0]["email"]
        verification_code = user[0]["verification_code"]
        already_verified = user[0]["is_verified"]

        # If post request, check if the verification code is correct
        if request.method == 'POST':
            
            # Create code from input
            create_entered_code = str(request.form['code0']) + str(request.form['code1']) + str(request.form['code2']) + str(request.form['code3']) + str(request.form['code4']) + str(request.form['code5'])
            
            # Check if the code is correct, if so, verify the user and log them in
            if create_entered_code == verification_code:
                sql.writeSQL(f"UPDATE gruttechat_users SET is_verified = {True} WHERE username = '{str(username)}'")
                session['username'] = username
                return redirect(f'{url_prefix}/chat')
            
            # If the code is incorrect, display an error
            else:
                error = "The code you entered is incorrect"
    
    # Render the verification page
    return render_template('verify.html', username=username, error=error, email=email, already_verified=already_verified, url_prefix = url_prefix)