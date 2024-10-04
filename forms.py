from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, URLField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, Email, Length
from flask_ckeditor import CKEditorField


class NewPost(FlaskForm):
    title = StringField(label="Blog Title", validators=[DataRequired()])
    subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    # author = StringField(label="Your Name", validators=[DataRequired()])
    body = CKEditorField(label="Blog Body", validators=[DataRequired()])
    img_url = URLField(label="Image URL", validators=[DataRequired()])
    submit = SubmitField(label="Submit")

class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=8)])
    # render_kw sets a keyword for the button, can be used to ID which button is primary if many are on a page
    submit = SubmitField(label="Log In", render_kw={'btn-primary': 'True'})

class RegisterForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=8)])
    username = StringField(label="Username", validators=[DataRequired()])
    # render_kw sets a keyword for the button, can be used to ID which button is primary if many are on a page
    submit = SubmitField(label="Sign Up!", render_kw={'btn-primary': 'True'})

class CommentForm(FlaskForm):
    comment = CKEditorField(label="Comment", validators=[DataRequired()])
    submit = SubmitField(label="Submit Comment!", render_kw={'btn-primary': 'True'})

class ContactForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    phone_num = StringField(label="Phone Number", validators=[DataRequired()])
    message = StringField(label="Message", validators=[DataRequired()])
    submit = SubmitField(label="Submit!", render_kw={'btn-primary': 'True'})

class LocationSubmit(FlaskForm):
    location = StringField(label="Enter your City, State (Finds nearest weather station)", validators=[DataRequired()])
    submit = SubmitField(label="Get Weather", render_kw={'btn-primary': 'True'})
