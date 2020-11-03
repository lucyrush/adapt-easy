import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_adaptions")
def get_adaptions():
    adaptions = list(mongo.db.adaptions.find())
    return render_template("listings.html", adaptions=adaptions)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    adaptions = mongo.db.adaptions.find()
    user = mongo.db.users.find_one({'_id': username})

    if username == session["user"]:
        return render_template("profile.html", username=username,
            adaptions=adaptions, user=user)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/new_listing", methods=["GET", "POST"])
def new_listing():
    if request.method == "POST":
        mask_mandatory = "on" if request.form.get("mask_mandatory") else "off"
        adaption = {
            "category_name": request.form.get("category_name"),
            "business_name": request.form.get("business_name"),
            "business_description": request.form.get("business_description"),
            "adaption_description": request.form.get("adaption_description"),
            "mask_mandatory": mask_mandatory,
            "valid_until": request.form.get("valid_until"),
            "image_url": request.form.get("image_url"),
            "website_url": request.form.get("website_url"),
            "created_by": session["user"]
        }
        mongo.db.adaptions.insert_one(adaption)
        flash("New Listing Successfully Added")
        return redirect(url_for("get_adaptions"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("new_listing.html", categories=categories)


@app.route("/edit_adaption/<adaption_id>", methods=["GET", "POST"])
def edit_adaption(adaption_id):
    if request.method == "POST":
        mask_mandatory = "on" if request.form.get("mask_mandatory") else "off"
        submit = {
            "category_name": request.form.get("category_name"),
            "business_name": request.form.get("business_name"),
            "business_description": request.form.get("business_description"),
            "adaption_description": request.form.get("adaption_description"),
            "mask_mandatory": mask_mandatory,
            "valid_until": request.form.get("valid_until"),
            "image_url": request.form.get("image_url"),
            "website_url": request.form.get("website_url"),
            "created_by": session["user"]
        }
        mongo.db.adaptions.update({"_id": ObjectId(adaption_id)}, submit)
        flash("New Listing Successfully Updated")
        return redirect(url_for("get_adaptions"))

    adaption = mongo.db.adaptions.find_one({"_id": ObjectId(adaption_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_adaption.html",
        adaption=adaption, categories=categories)


@app.route("/delete_adaption/<adaption_id>")
def delete_adaption(adaption_id):
    mongo.db.adaptions.remove({"_id": ObjectId(adaption_id)})
    flash("Listing Successfully Deleted")
    return redirect(url_for("get_adaptions"))


@app.route("/home")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)