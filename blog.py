#######################################################
# The blog.py module contains the back end logic
# for the blog, using the Google App Engine.
# Docs: https://cloud.google.com/appengine/docs/python/
# jinja 2 is the template engine used
# Docs: http://jinja.pocoo.org/docs/2.9/
# To view the blog during development,
# run in terminal from outside directory:
# `dev_appserver.py <dirname>` and access at
# http://localhost:8080/
# To deploy, run in terminal:
# `gcloud app deploy <path for yaml file>`
# Access at `unique-name.appspot.com/path`
# To see the datastore locally, once the server is up
# go to: http://localhost:8000/datastore
#######################################################

import os
import jinja2
import webapp2
import signup_helper
import re
import logging
import time
import pdb

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

# Models

class User(db.Model):
    username = db.StringProperty(required=True)
    password_digest = db.StringProperty(required=True)

class Blog(db.Model):
    title = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    blog = db.TextProperty(required=True)
    author = db.ReferenceProperty(User, collection_name="blogs")

class Comment(db.Model):
    body = db.TextProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    author = db.ReferenceProperty(User, collection_name="comments")
    post = db.ReferenceProperty(Blog, collection_name="comments")

    @classmethod
    def by_post(cls, post_id):
        unsorted = filter(lambda x: x.post.key().id() == int(post_id), cls.all())
        if unsorted == []:
            return unsorted
        else:
            return sorted(unsorted, key=lambda x: x.date, reverse=True)

    @classmethod
    def by_author(cls, user_id):
        return filter(lambda x: x.user.key().id() == int(user_id), cls.all())

class Like(db.Model):
    user = db.ReferenceProperty(User, collection_name="likes")
    post = db.ReferenceProperty(Blog, collection_name="likes")

    @classmethod
    def count_likes(cls, post_id):
        return filter(lambda x: x.post.key().id() == int(post_id), cls.all()).count()

# Rendering hdndler and rendering methods

class BaseHandler(webapp2.RequestHandler):
    def write(self, output):
        self.response.write(output)

    def render_str(self, template, **kwargs):
        # fetch template with the {{variables}}
        t = jinja_env.get_template(template)
        # fill in variables according to kwargs
        return t.render(**kwargs)

    def render(self, template, **kwargs):
        # display template with variables filled in
        self.write(self.render_str(template, **kwargs))

    def render_front(self, form=False, title="", blog="", error="", blogs=""):
        username = self.get_current_user()
        blogs = db.GqlQuery("SELECT * FROM Blog "
                            "ORDER BY date DESC LIMIT 10")

        self.render("main.html",
                    form=form,
                    title=title,
                    blog=blog,
                    error=error,
                    blogs=blogs,
                    username=username)

    def redirect_if_not_logged_in(self):
        cookie = self.request.cookies.get("name")
        if not cookie:
            self.redirect('/blog/login')

    def get_cookie(self, name):
        raw_cookies = self.request.headers.get("Cookie")
        if raw_cookies:
            for cookie in raw_cookies.split(";"):
                cookie = cookie.split("=")
                if cookie[0] == name:
                    return cookie[1]
        return None

    def get_current_user(self):
        user = self.get_cookie("name")
        if user:
            return user.split("|")[0]
        else:
            return None

# handling routes

class Greet(BaseHandler):
    def get(self):
        self.render("greet.html")

class MainPage(BaseHandler):
    def get(self):
        self.redirect_if_not_logged_in()
        self.render_front()

class NewPost(BaseHandler):
    def get(self):
        username = self.get_current_user()
        self.redirect_if_not_logged_in()
        self.render("main.html",
                    form=True,
                    action="/blog/newpost",
                    submit="Publish",
                    username=username)

    def post(self):
        title = self.request.get("subject")
        blog = self.request.get("content")
        # name_cookie = self.get_cookie("name")
        username = self.get_current_user()

        if title and blog and name_cookie:
            author = User.gql("WHERE username=:1", username).get()
            b = Blog(title=title, blog=blog, author=author)
            b.put()
            self.redirect("/blog/%s" % b.key().id())
        else:
            error = "We need both a title and a blog in order to publish this entry."
            self.render("main.html",
                        title=title,
                        blog=blog,
                        error=error,
                        submit="Publish",
                        username=username)

class ShowPost(BaseHandler):
    def get(self, number):
        self.redirect_if_not_logged_in()
        post = Blog.get_by_id(int(number))
        comments = Comment.by_post(int(number))
        error = self.request.get("error")
        username = self.get_current_user()

        if error:
            error = "Cannot submit empty comment."
        else:
            error = ""

        if not post:
            self.error(404)
            return

        if self.get_current_user() == post.author.username:
            self.render("permalink.html",
                        username=username,
                        post=post,
                        comments=comments,
                        error=error,
                        user_is_author=True)
        else:
            self.render("permalink.html",
                        username=username,
                        post=post,
                        comments=comments,
                        error=error,
                        user_is_author=False)


class EditPost(BaseHandler):

    def get(self, number):
        self.redirect_if_not_logged_in()
        post = Blog.get_by_id(int(number))
        username = self.get_current_user()

        self.render("main.html",
                    form=True,
                    action="/blog/%s/edit" % number,
                    title=post.title,
                    blog=post.blog,
                    submit="Update",
                    username=username)

    def post(self, number):
        title = self.request.get("subject")
        blog = self.request.get("content")
        post = Blog.get_by_id(int(number))

        if title and blog:
            post.title = title
            post.blog = blog
            post.put()
            self.redirect("/blog/%s" % number)
        else:
            error = "We need both a title and a blog in order to publish this entry."
            self.render_front(True, title, blog, error)

class DeletePost(BaseHandler):
    def get(self, number):
        self.redirect_if_not_logged_in()
        title = self.request.get("subject")
        blog = self.request.get("content")
        post = Blog.get_by_id(int(number))
        username = self.get_current_user()

        self.render("permalink.html",
                    username=username,
                    post=post,
                    user_is_author=True,
                    modal=True)

    def post(self, number):
        post = Blog.get_by_id(int(number))
        post.delete()
        comments = post.comments
        username = self.get_current_user()
        for comment in comments:
            comment.delete()
        self.render("permalink.html",
                    username=username,
                    post=post,
                    user_is_author=False)

class NewComment(BaseHandler):
    def post(self, number):
        body = self.request.get("content")
        author = User.gql("WHERE username=:1", self.get_current_user()).get()
        post = Blog.get_by_id(int(number))
        comments = Comment.by_post(number)
        if body == "":
            self.redirect("/blog/%s?error=True" % number)
        else:
            c = Comment(body=body, author=author, post=post)
            c.put()
            time.sleep(0.1)
            self.redirect("/blog/%s" % number)

class SignUp(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect('/blog')
        else:
            self.render('signup_form.html')

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")
        username_error = ""
        password_error = ""
        verify_error = ""
        email_error = ""
        no_errors = True

        if not signup_helper.validate_username(username):
            username_error = "Username must have 3-20 alphanumeric characters"
            no_errors = False
        if User.gql("WHERE username=:1", username).get():
            username_error = "Username has already been taken."
            no_errors = False
        if not signup_helper.validate_password(password):
            password_error = "Password must have 3-20 characters"
            no_errors = False
        if not signup_helper.password_match(password, verify):
            verify_error = "Passwords don't match"
            no_errors = False
        if not signup_helper.validate_email(email):
            email_error = "That's not a valid email address"
            no_errors = False

        if no_errors:
            password_digest = signup_helper.secure_str(username, password)
            user = User(username=username, password_digest=password_digest)
            user.put()
            cookie = signup_helper.secure_str(username, password)
            self.response.headers.add_header('Set-Cookie',
                                             'name={0};Path=/'
                                             .format(cookie))
            self.redirect('/blog')
        else:
            self.render('signup_form.html',
                        username=username,
                        email=email,
                        username_error=username_error,
                        password_error=password_error,
                        verify_error=verify_error,
                        email_error=email_error)

class Login(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.redirect('/blog')
        else:
            self.render('login.html')

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        user = User.gql("WHERE username=:1", username).get()
        cookie = signup_helper.secure_str(username, password)
        if user and signup_helper.validate_credentials(username,
                                                  password,
                                                  user.password_digest):
            self.response.headers.add_header('Set-Cookie',
                                             'name={0};Path=/'
                                             .format(cookie))
            self.redirect('/blog')
        else:
            error = "Invalid Login"
            self.render('login.html', error=error)

class Logout(BaseHandler):
    def post(self):
        self.response.headers.add_header('Set-Cookie',
                                         'name=;Path=/')
        self.redirect('/blog/login')

app = webapp2.WSGIApplication([('/?', Greet),
                               ('/blog/signup', SignUp),
                               ('/blog/login', Login),
                               ('/blog', MainPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/(\d+)', ShowPost),
                               ('/blog/(\d+)/edit', EditPost),
                               ('/blog/(\d+)/delete', DeletePost),
                               ('/blog/(\d+)/comment', NewComment),
                               ('/blog/logout', Logout)],
                              debug=True)
