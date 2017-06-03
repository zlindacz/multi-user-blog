[Live Link](https://test-146823.appspot.com/)

## Intro

This blogging app is built on [Google App engine](https://cloud.google.com/appengine/docs/python/) using Python 2.7 and [webapp2](https://webapp2.readthedocs.io/en/latest/), a lightweight web application framework. Requests are handled using the WSGI application (Web Server Gateway Interface). [Jinja](http://jinja.pocoo.org/docs/2.9/) is the template engine used.

Authentication is custom designed. Password digests are created and validated using Python's hashlib module (sha256).

## Structure of the files

* The `static` directory holds stylesheets
* The `templates` directory holds templates
* `app.yaml` is the configuration file for the app
* `blog.py` has the app logic
* `signup_helper.py` has functions that help during the authentication process

## How to run the app locally

1. Install Google App Engine onto the machine that will run this app and install the necessary components
2. Download this directory
3. Navigate to the directory one level up from the app directory
3. In the terminal, type `dev_appserver <app_directory_name>`
4. In a browser, go to `http://localhost:8080/`
5. To see the datastore locally and to delete entries
go to `http://localhost:8000/datastore`

## How to deploy the app to App Engine

1. Navigate to app directory
2. In the terminal, type `gcloud app deploy <path/for/yaml-file>`
3. Access at `<unique-name>.appspot.com/path`
4. To see the app in the deployed web browser, type in the terminal `gcloud app browse`


#### Todo for Udacity's Full Stack Nanodegree assignment

###### Code functionality
- [x] App is built using Google App Engine
- [x] Submitted URL is publicly accessible

###### Site Usability
[x] User is directed to login, logout, and signup pages as appropriate
  - [x] Login page should have a link to signup page and vice-versa
  - [x] Logout page is only available to logged in user
- [x] User can edit their own posts
- [x] Using creating new post or editing post can cancel and go back to viewing the index page or that post's page, respectively
- [x] Blog pages render properly and use templates to to keep things DRY

###### Accounts and Security
- [x] Users are able to create accounts, login, and logout
- [x] Existing users can revisit the site and log back in without having to recreate their accounts each time (in appspot, not local server)
- [x] Usernames have to be unique. Attempting to create a duplicate user results in an error message.
- [x] Stored passwords are hashed and checked during login.

###### Permissions
- [x] Logged out users are redirected to the login page when attempting to create, edit, delete, or like a blog post.
- [x] Logged in users can edit or delete posts they themselves have created
- [x] Users can only like posts that are not theirs and only like or dislike it once.
- [x] Only signed-in users can post comments
- [x] Users can edit and delete comments they have made

###### Permissions
- [x] README has instructions on how to run the app


Todos
- [x] Blog has an index page as the front page
- [x] User can create new posts and edit/delete their own posts
- [x] Each post has its own page with comments and a comment form
- [x] User can sign up, log in and out
- [x] User cannot access posts if they're not logged in
- [x] User can comment on all posts if they're logged in
- [x] User can like posts by other authors
- [x] Styling
- [x] Readme
- [x] Deploy app to appspot.com
