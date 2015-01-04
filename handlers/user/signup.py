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
#							SET UP jinja2 working path, Handler    							   #
################################################################################################

template_dir = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, 'templates', 'user')
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
#								Hashing password Function          							   #
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
#								Hashing cookie Function          							   #
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
#							validate username,password and email         					   #
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
#							      set up User database         								   #
# username: required 																		   #
# password: required																		   #
# verify_password: required																	   #
# email: optional																			   #
#																							   #
################################################################################################

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty(required = False)

def query(username):
	q = db.GqlQuery('SELECT * FROM User WHERE username=:1', username)
	r = q.get()
	return r

def check_name_availablilty(username):
	result = query(username)
	if result == None:
		return True
	else:
		return False


################################################################################################
#							     Signup Page Handlers  	      								   #
# username: required 																		   #
# password: required																		   #
# verify_password: required																	   #
# email: optional																			   #
#																							   #
# procedure: request these parameters from user.                                               #
#			 verify parameters, mark error flag, set up new cookie.							   #
#			 check if name is not used														   #
#			 put verified user information to database.										   #
#			 redirect to '/welcome', pass cookie to user									   #
#																							   #
# set cookie:        																		   #
#        self.response.headers.add_header('Set-Cookie', 'name=%s ; Path=/' % new_cookie_val)   #
#		 note: ";", not ","!  																   #
#																							   #
#																							   #
################################################################################################

class Signup(Handler):
	def get(self):
		self.render("signup.html")

	def post(self):
		have_error = False
		#get user input
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')


		#define a dict params to store error information
		params = []
		
		if not valid_username(username):
			params['error_username'] = "That's not a valid username."
			have_error = True

		#check availablity of username
		if check_name_availablilty(username) == False:
			params['error_username'] = "Username has been used. Please try another one."
			have_error = True


		#if username is verified and not taken, pass parameters to params
		if email and username:
			params = dict(username = username, email = email)
		else:
			if username:
				params = dict(username = username)

		#verify password and email
		if not valid_password(password):
			params['error_password'] = "That wasn't a valid password."
			have_error = True
		elif password != verify:
			params['error_verify'] = "Your passwords didn't match."
			have_error = True

		if email:
			if not valid_email(email):
				params['error_email'] = "That's not a valid email."
				have_error = True


		if have_error:
			self.render('signup.html', **params)
		else:
			#add new user information to database User
			pw_hash = make_pw_hash(username, password)
			if email:
				user = User(username = username, password = pw_hash, email = email)
			else:
				user = User(username = username, password = pw_hash)
			user.put()

			#set new cookie, send cookie to user
			new_cookie_val = make_secure_val(str(username))
			self.response.headers.add_header('Set-Cookie', 'name=%s ; Path=/' % new_cookie_val) 

			#redirect to user welcome page: /welcome
			self.redirect('/welcome')


################################################################################################
#																							   #
#							     Welcome Page Handlers  	      							   #
#																							   #
# procedure: get name from user's cookie													   #
#			 if cookie not empty, pass this value to a new welcome page 					   #
#																							   #
#																							   #
################################################################################################		

class Welcome(Handler):
	def get(self):
		#self.response.headers['Content-Type'] = 'text/plain'
		name_cookie_str = self.request.cookies.get('name')

		#verify cookie, if cookie is not empty
		if name_cookie_str:
			name_cookie_val = check_secure_val(name_cookie_str)
			
			self.render('welcome.html', username = name_cookie_val)
		else:
			#if cookie empty, redirect to signup page
			self.redirect('/signup')
		
		

application = webapp2.WSGIApplication([('/signup', Signup),('/welcome', Welcome)], debug=True)







