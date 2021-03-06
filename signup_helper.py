#######################################################
# The signup_helper.py module contains the methods that
# validate forms and create password digests
#######################################################

import re
import hashlib
import random
import string

def validate_username(username):
    USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return username and re.match(USERNAME_RE, username)

def validate_password(password):
    PASSWORD_RE = re.compile("^.{3,20}$")
    return password and re.match(PASSWORD_RE, password)

def password_match(password, verify):
    if password == verify:
        return True

def validate_email(email):
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    return not email or EMAIL_RE.match(email)

def secure_str(username, password):
    h = hashlib.sha256(username+password).hexdigest()
    return "{0}|{1}".format(username, h)

def validate_credentials(username, password, password_digest):
    h = password_digest.split('|')[1]
    return secure_str(username, password).split('|')[1] == h
