import os
import jinja2
import webapp2

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



def user_required(handler):
	"""
		Decorator for checking if there's a user associated with the current session.
		Will also fail if there's no session present.
	"""
	def check_login(self, *args, **kwargs):
		auth = self.auth
		if not auth.get_user_by_session():
			# If handler has no login_url specified invoke a 403 error
			try:
				self.redirect(self.auth_config['login_url'], abort=True)
			except (AttributeError, KeyError), e:
				self.abort(403)
		else:
			return handler(self, *args, **kwargs)
 
	return check_login

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
		try:
			response = super(BaseHandler, self).dispatch()
			self.response.write(response)
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
#              Login Handler 									                               #
################################################################################################
class LoginHandler(BaseHandler):
	def get(self):
		self.render("login.html")
 
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
		self.render("signup.html")
 
	def post(self):
		"""
			username: Get the username from POST dict
			password: Get the password from POST dict
		"""
		username = self.request.POST.get('username')
		password = self.request.POST.get('password')
		# Passing password_raw=password so password will be hashed
		# Returns a tuple, where first value is BOOL. If True ok, If False no new user is created
		user = self.auth.store.user_model.create_user(username, password_raw=password)
		if not user[0]: #user is a tuple
			return user[1] # Error message
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
 
 
class SecureRequestHandler(BaseHandler):
	"""
		Only accessible to users that are logged in
	"""
	@user_required
	def get(self, **kwargs):
		a = self.app.config.get('foo')
		try:
			return "Secure zone %s <a href='%s'>Logout</a>" % (a, self.auth_config['logout_url'])
		except (AttributeError, KeyError), e:
			return "Secure zone"

