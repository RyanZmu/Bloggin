from __future__ import annotations
import hashlib
from urllib.parse import urlencode
from os import environ
from typing import List
from datetime import datetime, timedelta

import geocoder
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
import os
import smtplib
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_ckeditor import CKEditor
from jwt.utils import force_bytes
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from forms import NewPost, LoginForm, RegisterForm, CommentForm, ContactForm, LocationSubmit
from database import db, User, BlogPosts, Comment
import requests
from random import randint
import geopy

# Load environment vars
load_dotenv()

PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL = os.environ.get("EMAIL")
SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
OW_API_KEY = os.environ.get("OW_API_KEY")
HOST = "smtp.gmail.com"

app = Flask(__name__)

# Load ckeditor
ckeditor = CKEditor(app)

# Load DB
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI", "sqlite:///posts.db")
# init app with extension
db.init_app(app)

# Create the db tables
with app.app_context():
    db.create_all()

# Enable CSRF for flask forms
csrf = CSRFProtect(app)
# Config app for CSFR with a secret key
app.config["SECRET_KEY"] = SECRET_KEY
app.secret_key = os.environ.get("APP_SECRET_KEY")

# Load bootstrap
bootstrap = Bootstrap5(app)

# Load login manager
login_manager = LoginManager()
login_manager.init_app(app)

# # Admin decorator - make a decorator instead of adding or current_user.id == 1 to functions
# def admin_only():
#     def inner():
#         if current_user.id == 1:
#     return inner

def api_calls(location):
    # TODO: Periodically call the News and Weather API for updates, cache the updates instead of calling on routes
    # Call news API for current headlines
    news_endpoint = "https://newsapi.org/v2/top-headlines"
    news_params = {
        "apiKey": NEWS_API_KEY,
        "pageSize": 10,
        "country": "us"
    }

    news_request = requests.get(news_endpoint, params=news_params)
    news_data = news_request.json()

    print(news_data)
    news_articles = news_data["articles"]

    # Call Weather API for current weather
    # First get user location - lat and long to find forecast
    # TODO: DRY up the weather logic and make it flow better

    weather_endpoint = ""

    if request.method == "GET":
        # Initially grab weather based on server's location
        user_coords = geocoder.ip("me")
        # Weather based on server
        weather_endpoint = f"https://api.weather.gov/points/{user_coords.lat},{user_coords.lng}"

    if location.validate_on_submit():
        # Allow user to enter a city/state after initial load
        try:
            # Geolocation - NOM API Call
            nom = geopy.geocoders.Nominatim(user_agent="blogger_app")
            user_coords = nom.geocode(
                query=f"{location.data.get('location')}",
                addressdetails=True,
                geometry="geojson",
                extratags=True
            )
        except requests.exceptions.MissingSchema:
            # If API call failed - default back to server's location
            user_coords = geocoder.ip("me")
            # Weather based on server
            weather_endpoint = f"https://api.weather.gov/points/{user_coords.lat},{user_coords.lng}"
        else:
            if user_coords is not None:
                print("Location found")
                weather_endpoint = f"https://api.weather.gov/points/{user_coords.latitude},{user_coords.longitude}"
            else:
                # If API call is successful but location is invalid - default back to server's location
                user_coords = geocoder.ip("me")
                # Weather based on server
                weather_endpoint = f"https://api.weather.gov/points/{user_coords.lat},{user_coords.lng}"

    # Make Weather API request and output the data
    weather_request = requests.get(weather_endpoint)
    weather_data = weather_request.json()
    print(weather_data)

    location_details = weather_data["properties"]["relativeLocation"]["properties"]
    city = location_details["city"]
    state = location_details["state"]

    # Endpoint for forecast based on previous call for weather location
    forecast_endpoint = weather_data["properties"]["forecast"]

    forecast_request = requests.get(forecast_endpoint)
    forecast_data = forecast_request.json()

    print(location_details)

    forecast_data_by_day = forecast_data["properties"]["periods"]

    # Combine data from both api calls
    # TODO: Consider breaking these API calls out into separate function calls possibly
    api_data = {
        "news": news_articles,
        "weather": forecast_data_by_day,
        "location": {
            "city": city,
            "state": state
        },
        "updated_at": datetime.now()
    }

    print(api_data)
    return api_data

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# Post Routes
@app.route("/", methods=["GET", "POST"])
def get_blog():
    all_blog_posts = db.session.execute(db.select(BlogPosts)).scalars().all()

    location_form = LocationSubmit()

    api_results = api_calls(location_form)

    print(api_results)

    return render_template(
        template_name_or_list="index.html",
        posts=all_blog_posts,
        news=api_results["news"],
        forecast=api_results["weather"],
        location=api_results["location"],
        form=location_form
    )


@app.route(rule="/posts/<post_id>", methods=["GET", "POST"])
def get_blog_post(post_id):
    # Get post
    post_to_display = db.get_or_404(BlogPosts, post_id)

    # Add Comments to post
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        if current_user.is_active:
            new_comment = Comment(
                author_id=current_user.id,
                post_id=post_id,
                comment_body=comment_form.data.get("comment")
            )

            db.session.add(new_comment)
            db.session.commit()
            flash("Comment added!")
            return redirect(url_for("get_blog_post", post_id=post_id))
        else:
            flash("Please Login to comment!")
            return redirect(url_for("login_form"))

    return render_template(
        template_name_or_list="post.html",
        post=post_to_display,
        comment_form=comment_form,
    )


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def new_post():
    form = NewPost()

    if form.validate_on_submit():
        post = BlogPosts(
            author_id=current_user.id,
            title=form.data.get("title"),
            date=datetime.now().strftime("%B %w, %Y"),
            body=form.data.get("body"),
            img_url=form.data.get("img_url"),
            subtitle=form.data.get("subtitle")
        )

        try:
            db.session.add(post)
            db.session.commit()
        except db.exc.IntegrityError:
            # Add flash
            flash("Post with this title Exists")
            return redirect(url_for("get_blog"))
        else:
            return redirect(url_for("get_blog"))

    return render_template("forms.html", form=form)


@app.route("/edit-post/<post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post_to_edit = db.get_or_404(BlogPosts, post_id)

    # Confirm user is the post's author before edit
    if current_user.is_authenticated and current_user.id == post_to_edit.author.id or current_user.id == 1:
        edit_form = NewPost(
            title=post_to_edit.title,
            date=post_to_edit.date,
            body=post_to_edit.body,
            img_url=post_to_edit.img_url,
            subtitle=post_to_edit.subtitle,
        )

        if edit_form.validate_on_submit():
            post_to_edit.title = edit_form.data.get("title")
            post_to_edit.body = edit_form.data.get("body")
            post_to_edit.img_url = edit_form.data.get("img_url")
            post_to_edit.subtitle = edit_form.data.get("subtitle")

            db.session.commit()
            return redirect(url_for("get_blog_post", post_id=post_to_edit.id))

        return render_template("forms.html", form=edit_form, post_id=post_to_edit.id)
    else:
        # If user is not the post's author, return forbidden
        abort(403)


@app.route("/delete/<post_id>", methods=["GET"])
@login_required
def delete_post(post_id):
    # Delete the blogpost AND comments associated with blogpost
    # Get post author id and confirm logged-in user is the author before deleting
    post = db.get_or_404(BlogPosts, post_id)
    if current_user.is_authenticated and current_user.id == post.author.id or current_user.id == 1:
        db.session.execute(db.delete(Comment).where(Comment.post_id == post_id))
        db.session.execute(db.delete(BlogPosts).where(BlogPosts.id == post_id))
        db.session.commit()
    else:
        # If user is not the post's author, return forbidden
        abort(403)
    return redirect(url_for("get_blog"))


# Login Routes
@app.route(rule="/login", methods=["GET", "POST"])
def login_form():
    form = LoginForm()

    user_email = form.data.get("email")
    user_password = form.data.get("password")

    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == user_email)).scalar()
        if user is not None:
            if check_password_hash(user.password, user_password):
                login_user(user)
                return redirect(url_for("get_blog"))
        else:
            flash("Invalid email or Password!")

    return render_template(template_name_or_list="forms.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("get_blog"))

@app.route("/register", methods=["GET", "POST"])
def register_user():
    form = RegisterForm()

    if form.validate_on_submit():
        email_encoded = form.data.get("email").lower().encode('utf-8')
        # Email hash to request an Avatar from Gravatar
        # noinspection PyArgumentList
        new_user = User(
            email=form.data.get("email"),
            email_hash=hashlib.sha256(email_encoded).hexdigest(),
            password=generate_password_hash(form.data.get("password"), method="scrypt", salt_length=10),
            username=form.data.get("username")
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except exc.IntegrityError:
            # Add flash
            flash("User exists with this email!")
        else:
            login_user(new_user)
            return redirect(url_for("get_blog"))

    return render_template(template_name_or_list="forms.html", form=form)


# Misc routes
@app.route(rule="/about")
def get_about():
    return render_template("about.html")

@app.route(rule="/contact", methods=["POST", "GET"])
def contact_page():
    contact_form = ContactForm()

    if contact_form.validate_on_submit():
        connection = smtplib.SMTP(host=HOST, port=587)
        connection.starttls()
        connection.login(EMAIL, PASSWORD)
        connection.sendmail(
            from_addr=EMAIL,
            to_addrs=EMAIL,
            msg=f"Subject:Blog Message\n\n "
                f"Name: {contact_form.data.get('name')}\n "
                f"Email: {contact_form.data.get('email')}\n "
                f"Phone: {contact_form.data.get('phone_num')}\n "
                f"Message: {contact_form.data.get('message')}"
        )
        connection.quit()
        flash("Message Submitted! Thank You!")
        return redirect(url_for("contact_page"))

    return render_template("contact.html", form=contact_form)


if __name__ == '__main__':
    app.run(debug=True)
