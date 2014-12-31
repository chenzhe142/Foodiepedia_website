import os
import re
import random
import string
import hashlib
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

################################################################################################
#                           SET UP jinja2 working path, Handler                                #
################################################################################################

template_dir = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, 'templates', 'login')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

################################################################################################
#                               Hashing password Function                                      #
################################################################################################
# implement the function make_salt() that returns a string of 5 random
# letters use python's random module.
# Note: The string package might be useful here.

def make_salt():
	###Your code here
	a = "".join(random.choice(string.ascii_letters) for x in range(5))
	return a

# implement the function make_pw_hash(name, pw) that returns a hashed password 
# of the format: 
# HASH(name + pw + salt),salt
# use sha256

def make_pw_hash(name, pw):
	###Your code here
	salt = make_salt();
	put = name + pw + salt
	hash_value = hashlib.sha256(put).hexdigest()
	return "%s,%s" % (hash_value, salt)

# Implement the function valid_pw() that returns True if a user's password 
# matches its hash. You will need to modify make_pw_hash.

def valid_pw(name, pw, h):
	###Your code here
	salt = h.split(",")[1]
	prev_hash_value = h.split(",")[0]
	hash_value = hashlib.sha256(name + pw + salt).hexdigest()
	if prev_hash_value == hash_value:
		return True
	else:
		return False

################################################################################################
#                               Hashing cookie Function                                        #
################################################################################################
def hash_str(s):
	return hashlib.md5(s).hexdigest()

def make_secure_val(s):
	return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
	val = h.split("|")[0]
	if h == make_secure_val(val):
		return val


################################################################################################
#                           validate username,password and email                               #
################################################################################################

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
	return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
	return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
	return not email or EMAIL_RE.match(email)


################################################################################################
#                set up User database and query_string                                         #
################################################################################################

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty(required = True)

def query(username):
	q = db.GqlQuery('SELECT * FROM User WHERE username=:1', username)
	r = q.get()
	return r
	#return value: User object, should be handled like: r.username, r.password


################################################################################################
#                           login handlers                                                     #
################################################################################################


class Login(Handler):
	def get(self):
		self.render("login.html")

	def post(self):
		have_error = False

		input_username = self.request.get('username')
		input_password = self.request.get('password')

		params = dict(username = input_username)

		if not valid_username(input_username):
			params['error_username'] = "That's not a valid username."
			have_error = True

		if not valid_password(input_password):
			params['error_password'] = "That wasn't a valid password."
			have_error = True

		name = str(input_username)


		if not have_error:
			query_result = query(name)
			password_str = query_result.password
			
			if password_str:
				validate_result = valid_pw(input_username, input_password, password_str)
				if not validate_result:
					params['verify_error'] = "Username and password don't match."
					have_error = True
				else:
					#set cookie, send cookie to user
					new_cookie_val = make_secure_val(str(input_username))
					self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % new_cookie_val)

					
					self.redirect('/')   
			else:
				params['verify_error'] = "Username does not exist."
				have_error = True

			if have_error:
				self.render('login.html', **params)

		else:
			self.render('login.html', **params)

		


# application = webapp2.WSGIApplication([('/', Login)], debug=True)
		














