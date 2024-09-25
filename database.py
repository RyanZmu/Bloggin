from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Float, exc, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_login import UserMixin

# DB classes
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email_hash: Mapped[str] = mapped_column(String(255), unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # This will act like a List of BlogPost objects attached to each User.
    # Every User class will have a posts list
    posts = relationship("BlogPosts", back_populates="author")
    comments = relationship("Comment", back_populates="author")

class BlogPosts(db.Model):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, user.id that refers to User table - ties the value of author_id to the User.id
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey(column="users.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    date: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String(255), nullable=False)
    img_url: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(255), nullable=False)
    # Create ref to the User object. the posts refers to the posts property of User class
    author = relationship("User", back_populates="posts")
    # Holds all comments for this post
    post_comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey(column="users.id"))
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_posts.id"))
    comment_body: Mapped[str] = mapped_column(String(255), nullable=False)
    author = relationship("User", back_populates="comments")
    parent_post = relationship("BlogPosts", back_populates="post_comments")
