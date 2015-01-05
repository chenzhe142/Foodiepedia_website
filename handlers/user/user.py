import os
import jinja2
import webapp2

import re
import string
from string import letters

from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

################################################################################################
#               SET UP jinja2 working path   					                               #
################################################################################################
template_dir = os.path.join(os.path.dirname(__file__), os.path.pardir, 
							os.path.pardir, 'templates', 'user')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

################################################################################################
#              BaseHandler function 							                               #
################################################################################################
class BaseHandler(webapp2.RequestHandler):
	"""
		BaseHandler for all requests

		Holds the auth and session properties so they are reachable for all requests
	"""
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def check_authenticated(self):
		auth = self.auth
		if not auth.get_user_by_session():
			isAuthenticated = False
		else:
			isAuthenticated = True

		return isAuthenticated


	def dispatch(self):
		"""
			Save the sessions for preservation across requests
		"""
		self.session_store = sessions.get_store(request=self.request)
		try:
			# response = super(BaseHandler, self).dispatch()
			# self.response.write(response)
			webapp2.RequestHandler.dispatch(self)
		finally:
			
			self.session_store.save_sessions(self.response)
 
	@webapp2.cached_property
	def auth(self):
		return auth.get_auth()
 
	@webapp2.cached_property
	def session_store(self):
		return sessions.get_store(request=self.request)
 
	@webapp2.cached_property
	def auth_config(self):
		"""
			Dict to hold urls for login/logout
		"""
		return {
			'login_url': self.uri_for('login'),
			'logout_url': self.uri_for('logout')
		}

################################################################################################
#					functions for validating username,password and email         			   #
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
#              Login Handler 									                               #
################################################################################################
class LoginHandler(BaseHandler):
	def get(self):
		page_title = 'Login | Foodiepedia'
		isAuthenticated = False
		isAuthenticated = self.check_authenticated()
		if isAuthenticated == True:
			self.redirect('/')
		else:
			self.render("login.html", page_title=page_title)
 
	def post(self):
		"""
			username: Get the username from POST dict
			password: Get the password from POST dict
		"""
		username = self.request.POST.get('username')
		password = self.request.POST.get('password')
		# Try to login user with password
		# Raises InvalidAuthIdError if user is not found
		# Raises InvalidPasswordError if provided password doesn't match with specified user
		try:
			self.auth.get_user_by_password(username, password)
			self.redirect('/')
		except (InvalidAuthIdError, InvalidPasswordError), e:
			# Returns error message to self.response.write in the BaseHandler.dispatcher
			# Currently no message is attached to the exceptions
			return e

################################################################################################
#              Create User Handler 									                           #
################################################################################################
class CreateUserHandler(BaseHandler):
	def get(self):
		page_title = 'Signup | Foodiepedia'
		isAuthenticated = False
		isAuthenticated = self.check_authenticated()
		if isAuthenticated == True:
			self.redirect('/')
		else:
			self.render("signup.html", page_title=page_title)
 
	def post(self):
		"""
			username: Get the username from POST dict
			password: Get the password from POST dict
		"""
		have_error = False

		#get user input
		username = self.request.POST.get('username')

		password = self.request.POST.get('password')
		verify_password = self.request.POST.get('verify_password')

		# firstname = self.request.POST.get('firstname')
		# lastname = self.request.POST.get('lastname')

		email = self.request.POST.get('email')


		#define a dict params to store error information
		params = dict(username=username, email=email)
		
		if not valid_username(username):
			params['error_username'] = "That's not a valid username."
			have_error = True

		#verify password and email
		if not valid_password(password):
			params['error_password'] = "That wasn't a valid password."
			have_error = True
		elif password != verify_password:
			params['error_verify_password'] = "Your passwords didn't match."
			have_error = True
		
		if not valid_email(email):
			params['error_email'] = "That's not a valid email."
			have_error = True

		if have_error:
			self.render('signup.html', **params)
		else:
			# Passing password_raw=password so password will be hashed
			# Returns a tuple, where first value is BOOL. If True ok, If False no new user is created
			user = self.auth.store.user_model.create_user(username, password_raw=password, email_address=email,
														  name=username)
			if not user[0]: #user is a tuple
				params['error_username'] = 'This username is taken. Please try another one.'
				self.render('signup.html', **params)
			else:
				# User is created, let's try redirecting to login page
				try:
					self.redirect('/login')
					# self.redirect(self.auth_config['login_url'], abort=True)
				except (AttributeError, KeyError), e:
					self.abort(403)
 
################################################################################################
#              Logout Handler 	 									                           #
################################################################################################
class LogoutHandler(BaseHandler):
	"""
		Destroy user session and redirect to login
	"""
	def get(self):
		self.auth.unset_session()
		# User is logged out, let's try redirecting to login page
		try:
			self.redirect('/')
		except (AttributeError, KeyError), e:
			return "User is logged out"


