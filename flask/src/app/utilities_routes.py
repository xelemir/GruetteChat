from flask import render_template, request, redirect, session, make_response, Blueprint
from pythonHelper import MongoDBHelper, EncryptionHelper, MailHelper
from credentials import url_suffix

if url_suffix == "/gruettechat":
    path_template = "/application/templates"
else:
    path_template = "/application/templates"

db = MongoDBHelper.MongoDBHelper()
eh = EncryptionHelper.EncryptionHelper()
utilities_route = Blueprint("Utilities", "Utilities", template_folder=path_template)

@utilities_route.route('/chat/delete/<recipient>')
def delete_chat(recipient):
    if 'username' not in session:
        return redirect(f'{url_suffix}/')

    username = str(session['username'])
    db.delete('messages', {'$or': [{'username_send': username, 'username_receive': recipient}, {'username_send': recipient, 'username_receive': username}]})
    return redirect(f'{url_suffix}/')

@utilities_route.route('/logout')
def logout():
    session.pop('username', None)
    response = redirect(f'{url_suffix}/')
    response.delete_cookie('username')
    return response

@utilities_route.route("/settings", methods=["GET", "POST"])
def settings(error=None):

    if "username" not in session:
        return redirect(f"{url_suffix}/")
    
    user = db.read('users', {"username": session['username']})

    if not user:
        error="Something went wrong on our end :/"
        selected_personality="Default"
        has_premium = False
    else:
        selected_personality = user[0]["ai_personality"]
        has_premium = bool(user[0]["has_premium"])

    return render_template("settings.html", error=error, selected_personality=selected_personality, has_premium=has_premium, url_suffix=url_suffix)

@utilities_route.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    if request.method == "GET":
        return redirect(f"{url_suffix}/settings")
    
    selected_personality = "Default"
    new_password = str(request.form["new_password"])
    old_password = str(request.form["old_password"])
    user = db.read('users', {"username": str(session['username'])})
    
    if not user:
        return render_template("settings.html", error="Something went wrong on our end :/", selected_personality=selected_personality, has_premium=False, url_suffix=url_suffix)
    else:
        selected_personality = user[0]["ai_personality"]
        
    if len(new_password) > 40 or len(new_password) < 8:
        return render_template('settings.html', error='Password must be between 8 and 40 characters', selected_personality=selected_personality, has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)
    
    password = eh.decrypt_message(str(user[0]["password"]))
    if password != old_password:
        return render_template("settings.html", error="Passwords aren't matching!", selected_personality=selected_personality, has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)
    else:
        encrypt_new_password = eh.encrypt_message(str(new_password))
        db.update('users', {"username": str(session['username'])}, {"$set": {"password": str(encrypt_new_password)}})

    return render_template("settings.html", error="Password changed successfully!", selected_personality=selected_personality, has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)


@utilities_route.route("/change_email", methods=["GET", "POST"])
def change_email():
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    if request.method == "GET":
        return redirect(f"{url_suffix}/settings")
    
    new_email = str(request.form["new_email"])
    password_form = str(request.form["password"])
    user = db.read('users', {"username": str(session['username'])})

    if not user:
        return render_template("settings.html", error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_suffix=url_suffix)
    else:
        if "@" not in new_email or "." not in new_email:
            return render_template("settings.html", error="Please enter a valid email address!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)
        password = eh.decrypt_message(str(user[0]["password"]))
        if password_form != password:
            return render_template("settings.html", error="Passwords aren't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)
        else:
            db.update('users', {"username": str(session['username'])}, {"$set": {"email": str(new_email)}})

        return render_template("settings.html", error="Email changed successfully!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)
                               
@utilities_route.route("/change_ai_personality/<ai_personality>", methods=["GET"])
def change_ai_personality(ai_personality):
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    user = db.read('users', {"username": str(session['username'])})
        
    if not user:
        return render_template("settings.html", error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_suffix=url_suffix)
    elif bool(user[0]["has_premium"]) == True:
        db.update('users', {"username": str(session['username'])}, {"$set": {"ai_personality": str(ai_personality)}})
        return render_template("settings.html", error=f"MyAI is set to {ai_personality}", selected_personality=ai_personality, has_premium=True, display_back_to_ai=True, url_suffix=url_suffix)
    else:
        return render_template("settings.html", error="Please purchase GrütteChat PLUS to change your MyAI personality!", selected_personality="Default", has_premium=False, url_suffix=url_suffix)
        
@utilities_route.route("/ai-preferences", methods=["GET"])
def ai_preferences():
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    
    user = db.read('users', {"username": str(session['username'])})
    
    if not user:
        return render_template("settings.html", error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_suffix=url_suffix)
    else:
        return render_template("settings.html", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), display_back_to_ai=True, url_suffix=url_suffix)
        
@utilities_route.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    if request.method == "GET":
        return redirect(f"{url_suffix}/settings")

    username_session = str(session["username"])
    username_form = str(request.form["username"])
    password_form = str(request.form["password"])
    email_form = str(request.form["email"])
    user = db.read('users', {"username": str(session['username'])})
    
    if not user:
        return render_template("settings.html", error="Something went wrong on our end :/", selected_personality="Default", has_premium=False, url_suffix=url_suffix)
    
    username_db = user[0]["username"]
    password_db = eh.decrypt_message(str(user[0]["password"]))
    email_db = user[0]["email"]
    
    if username_db == username_form and password_db == password_form and email_db == email_form:
        db.delete('users', {"username": str(username_session)})
        session.pop('username', None)
        response = redirect(f'{url_suffix}/')
        response.delete_cookie('username')
        return response
    elif username_db != username_form:
        return render_template("settings.html", error="Username isn't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)
    elif password_db != password_form:
        return render_template("settings.html", error="Password isn't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)
    elif email_db != email_form:
        return render_template("settings.html", error="Email isn't matching!", selected_personality=user[0]["ai_personality"], has_premium=bool(user[0]["has_premium"]), url_suffix=url_suffix)


@utilities_route.route("/help", methods=["GET"])
def help():
    return render_template("help.html", url_suffix=url_suffix)
        
@utilities_route.route("/about", methods=["GET"])
def about():
    return redirect(f"{url_suffix}/help")

@utilities_route.route("/privacy", methods=["GET"])
def privacy():
    return redirect(f"{url_suffix}/help")

@utilities_route.route("/support", methods=["GET"])
def support():
    return render_template("support.html", url_suffix=url_suffix)

@utilities_route.route("/support", methods=["POST"])
def send_support():
    if "username" not in session:
        return redirect(f"{url_suffix}/")
    
    name = str(request.form["name"])
    username = str(request.form["username"])
    email = str(request.form["mail"])
    message = str(request.form["message"])
    
    mail = MailHelper.MailHelper()
    mail.send_support_mail(name, username, email, message)
    
    return render_template("support.html", error="Your message has been sent!", url_suffix=url_suffix)
    
    
    
    