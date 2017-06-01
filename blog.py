#######################################################
# The blog.py module contains the back end logic
# for the blog, using webapp2 on Google App Engine.
# jinja 2 is the template engine used
#######################################################

import os
import jinja2
import webapp2
import signup_helper
import re
import logging
import time
import models

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

# Rendering handler and rendering methods

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
        username = self.get_current_user()

        self.render("main.html",
                    form=form,
                    username=username,
                    title=title,
                    blog=blog,
                    error=error,
                    blogs=blogs)

    def redirect_if_not_logged_in(self):
        cookie = self.get_cookie("name")
        if not cookie:
            self.redirect('/blog/login')
        else:
            username = cookie.split("|")[0]
            cookie_hash = cookie.split("|")[1]
            user_digest = models.User.get_by("username", username).password_digest.split("|")[1]
            if cookie_hash != user_digest:
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
        cookie = self.get_cookie("name")
        if cookie:
            username = cookie.split("|")[0]
            cookie_hash = cookie.split("|")[1]
            user_digest = models.User.get_by("username", username).password_digest.split("|")[1]
            if username and (cookie_hash == user_digest):
                return username
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
        self.redirect_if_not_logged_in()
        username = self.get_current_user()

        self.render("main.html",
                    form=True,
                    action="/blog/newpost",
                    cancel="/blog",
                    submit="Publish",
                    username=username)

    def post(self):
        self.redirect_if_not_logged_in()
        title = self.request.get("subject")
        blog = self.request.get("content")
        username = self.get_current_user()
        user = models.User.get_by("username", username)
        if title and blog and username:
            b = models.Blog(title=title, blog=blog, author=user)
            b.put()
            self.redirect("/blog/%s" % b.key().id())
        else:
            error = "We need both a title and a blog in order to publish this entry."
            self.render("main.html",
                        form=True,
                        action="/blog/newpost",
                        cancel="/blog",
                        username=username,
                        title=title,
                        blog=blog,
                        error=error,
                        submit="Publish")

class ShowPost(BaseHandler):
    def get(self, number):
        self.redirect_if_not_logged_in()
        post = models.Blog.get_by_id(int(number))
        if not post:
            self.render("error.html")
        else:
            comments = models.Comment.by_post(int(number))
            error = self.request.get("error")
            username = self.get_current_user()
            current_user = models.User.get_by("username", username)
            votes = models.Like.count_likes(post.key().id())
            has_voted_up = ""
            has_voted_down = ""


            if models.Like.vote_of_post(post, current_user) == True:
                has_voted_up = "voted"
            elif models.Like.vote_of_post(post, current_user) == False:
                has_voted_down = "voted"

            if error:
                error = "Cannot submit empty comment."
            else:
                error = ""

            if post and self.get_current_user() == post.author.username:
                self.render("permalink.html",
                            username=username,
                            post=post,
                            comments=comments,
                            error=error,
                            user_is_author=True,
                            votes=votes,
                            has_voted_up="",
                            has_voted_down="")
            elif post:
                self.render("permalink.html",
                            username=username,
                            post=post,
                            comments=comments,
                            error=error,
                            user_is_author=False,
                            votes=votes,
                            has_voted_up=has_voted_up,
                            has_voted_down=has_voted_down)


class EditPost(BaseHandler):
    def get(self, number):
        self.redirect_if_not_logged_in()
        username = self.get_current_user()
        post = models.Blog.get_by_id(int(number))

        if not post or post.author.username != username:
            self.render("error.html")
        else:
            self.render("main.html",
                    form=True,
                    action="/blog/%s/edit" % number,
                    cancel="/blog/%s" % number,
                    username=username,
                    title=post.title,
                    blog=post.blog,
                    submit="Update")

    def post(self, number):
        self.redirect_if_not_logged_in()
        username = self.get_current_user()
        title = self.request.get("subject")
        blog = self.request.get("content")
        post = models.Blog.get_by_id(int(number))

        if not post or post.author.username != username:
            self.render("error.html")
        elif title and blog:
            post.title = title
            post.blog = blog
            post.put()
            self.redirect("/blog/%s" % number)
        else:
            error = "We need both a title and a blog in order to update this entry."
            self.render("main.html",
                    form=True,
                    username=username,
                    action="/blog/%s/edit" % number,
                    cancel="/blog/%s" % number,
                    error=error,
                    submit="Update")

class DeletePost(BaseHandler):
    def get(self, number):
        self.redirect_if_not_logged_in()
        title = self.request.get("subject")
        username = self.get_current_user()
        blog = self.request.get("content")
        post = models.Blog.get_by_id(int(number))

        if not post or post.author.username != username:
            self.render("error.html")
        else:
            self.render("permalink.html",
                    username=username,
                    post=post,
                    user_is_author=True,
                    modal=True)

    def post(self, number):
        self.redirect_if_not_logged_in()
        post = models.Blog.get_by_id(int(number))
        username = self.get_current_user()

        if not post or post.author.username != username:
            self.render("error.html")
        else:
            post.delete()
            comments = post.comments
            likes = post.likes
            username = self.get_current_user()
            for comment in comments:
                comment.delete()
            for like in likes:
                like.delete()
            self.render("permalink.html",
                        username=username,
                        post=post,
                        user_is_author=False)

class NewVote(BaseHandler):
    def post(self, number, voted):
        self.redirect_if_not_logged_in()
        current_user = models.User.get_by("username", self.get_current_user())
        post = models.Blog.get_by_id(int(number))
        comments = post.comments
        votes = models.Like.count_likes(post.key().id())
        vote_error = ""
        has_voted_up = ""
        has_voted_down = ""

        if post.author.username == current_user.username:
            vote_error = "You cannot vote on your own post."
            self.render("permalink.html",
                        username=current_user.username,
                        post=post,
                        comments=comments,
                        vote_error=vote_error,
                        user_is_author=True,
                        votes=votes,
                        has_voted_up=has_voted_up,
                        has_voted_down=has_voted_down)
        else:
            if voted == "like":
                if models.Like.vote_of_post(post, current_user) == True:
                    vote_error = "Already voted up. Cannot vote twice."
                    has_voted_up = "voted"
                elif models.Like.vote_of_post(post, current_user) == False:
                    vote = models.Like.gql("WHERE post=:1 AND user=:2", post, current_user).get()
                    vote.delete()
                    time.sleep(0.2)
                    self.redirect("/blog/%s" % post.key().id())
                else:
                    like = models.Like(user=current_user, post=post, status=True)
                    like.put()
                    time.sleep(0.2)
                    has_voted_up = "voted"
                    self.redirect("/blog/%s" % post.key().id())

            elif voted == "dislike":
                if models.Like.vote_of_post(post, current_user) == True:
                    vote = models.Like.gql("WHERE post=:1 AND user=:2", post, current_user).get()
                    vote.delete()
                    time.sleep(0.2)
                    self.redirect("/blog/%s" % post.key().id())
                elif models.Like.vote_of_post(post, current_user) == False:
                    vote_error = "Already voted down. Cannot vote twice."
                    has_voted_down = "voted"
                else:
                    like = models.Like(user=current_user, post=post, status=False)
                    like.put()
                    time.sleep(0.2)
                    has_voted_down = "voted"
                    self.redirect("/blog/%s" % post.key().id())


            self.render("permalink.html",
                username=current_user.username,
                post=post,
                comments=comments,
                vote_error=vote_error,
                user_is_author=False,
                votes=votes,
                has_voted_up=has_voted_up,
                has_voted_down=has_voted_down)

class NewComment(BaseHandler):
    def post(self, number):
        self.redirect_if_not_logged_in()
        body = self.request.get("content")
        author = models.User.gql("WHERE username=:1", self.get_current_user()).get()
        post = models.Blog.get_by_id(int(number))
        comments = models.Comment.by_post(number)
        if body == "":
            self.redirect("/blog/%s?error=True" % number)
        else:
            c = models.Comment(body=body, author=author, post=post)
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
        if models.User.gql("WHERE username=:1", username).get():
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
            user = models.User(username=username, password_digest=password_digest)
            user.put()
            cookie = signup_helper.secure_str(username, password)
            self.response.headers.add_header('Set-Cookie',
                                             'name={0};Path=/'
                                             .format(cookie))
            time.sleep(0.2)
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
        user = models.User.gql("WHERE username=:1", username).get()
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
                               ('/blog/(\d+)/vote/(.+)', NewVote),
                               ('/blog/(\d+)/comment', NewComment),
                               ('/blog/logout', Logout)],
                              debug=True)
