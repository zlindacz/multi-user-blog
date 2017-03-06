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
        blogs = db.GqlQuery("SELECT * FROM Blog "
                            "ORDER BY date DESC LIMIT 10")

        self.render("main.html",
                    form=form,
                    title=title,
                    blog=blog,
                    error=error,
                    blogs=blogs)

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

class Greet(BaseHandler):
    def get(self):
        self.render("greet.html")

class MainPage(BaseHandler):
    def get(self):
        self.redirect_if_not_logged_in()
        self.render_front()

class NewPost(BaseHandler):
    def get(self):
        self.redirect_if_not_logged_in()
        self.render("main.html",
                    form=True,
                    action="/blog/newpost",
                    submit="Publish")

    def post(self):
        title = self.request.get("subject")
        blog = self.request.get("content")
        name_cookie = self.get_cookie("name")

        if title and blog and name_cookie:
            username=name_cookie.split("|")[0]
            author = User.gql("WHERE username=:1", username).get()
            b = Blog(title=title, blog=blog, author=author)
            b.put()
            self.redirect("/blog/%s" % b.key().id())
        else:
            error = "We need both a title and a blog in order to publish this entry."
            self.render_front(True, title, blog, error)

class ShowPost(BaseHandler):
    def get(self, number):
        self.redirect_if_not_logged_in()
        post = Blog.get_by_id(int(number))

        if not post:
            self.error(404)
            return

        if self.get_current_user() == post.author.username:
            self.render("permalink.html", post=post, user_is_author=True)
        else:
            self.render("permalink.html", post=post, user_is_author=False)

class EditPost(BaseHandler):
    def get(self, number):
        self.redirect_if_not_logged_in()
        post = Blog.get_by_id(int(number))

        self.render("main.html",
                    form=True,
                    action="/blog/%s/edit" % number,
                    title=post.title,
                    blog=post.blog,
                    submit="Update")

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

        self.render("permalink.html",
                    post=post,
                    user_is_author=True,
                    modal=True)

    def post(self, number):
        post = Blog.get_by_id(int(number))
        post.delete()
        self.render("permalink.html", post=post, user_is_author=False)

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
                               ('/blog/logout', Logout)],
                              debug=True)
