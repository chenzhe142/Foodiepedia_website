import os
import jinja2
import webapp2
import time
import webapp2_extras.appengine.auth.models

from google.appengine.ext import ndb

from webapp2_extras import security
from webapp2_extras import auth
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)


################################################################################################
#                set up User database and query_string                                         #
################################################################################################

class User(model.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty(required = True)

def query(username):
	q = db.GqlQuery('SELECT * FROM User WHERE username=:1', username)
	r = q.get()
	return r
	#return value: User object, should be handled like: r.username, r.password


class BaseHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	# Cookie
	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)
	# Cookie end

	# User authentication
	@webapp2.cached_property
	def auth(self):
		# """Shortcut to access the auth instance as a property."""
		return auth.get_auth()
	 
	@webapp2.cached_property
	def user_info(self):
		# """Shortcut to access a subset of the user attributes that are stored
		# in the session.
	 
		# The list of attributes to store in the session is specified in
		#   config['webapp2_extras.auth']['user_attributes'].
		# :returns
		#   A dictionary with most user information
		# """
		return self.auth.get_user_by_session()
	 
	@webapp2.cached_property
	def user(self):
		# """Shortcut to access the current logged in user.
	 
		# Unlike user_info, it fetches information from the persistence layer and
		# returns an instance of the underlying model.
	 
		# :returns
		#   The instance of the user model associated to the logged in user.
		# """
		u = self.user_info
		return self.user_model.get_by_id(u['user_id']) if u else None
	 
	@webapp2.cached_property
	def user_model(self):
		# """Returns the implementation of the user model.
	 
		# It is consistent with config['webapp2_extras.auth']['user_model'], if set.
		# """   
		return self.auth.store.user_model
	 
	@webapp2.cached_property
	def session(self):
		# """Shortcut to access the current session."""
		return self.session_store.get_session(backend="datastore")
	 
	def render_template(self, view_filename, params={}):
		user = self.user_info
		params['user'] = user
		path = os.path.join(os.path.dirname(__file__), 'views', view_filename)
		self.response.out.write(template.render(path, params))
	 
	def display_message(self, message):
		# """Utility function to display a template with a simple message."""
		params = {
		  'message': message
		}
		self.render_template('message.html', params)
	 
	  # this is needed for webapp2 sessions to work
	def dispatch(self):
		# Get a session store for this request.
		self.session_store = sessions.get_store(request=self.request)
	 
		try:
			# Dispatch the request.
			webapp2.RequestHandler.dispatch(self)
		finally:
			# Save all sessions.
			self.session_store.save_sessions(self.response)

class SignupHandler(BaseHandler):
	def get(self):
		self.render_template('signup.html')
	 
	def post(self):
		user_name = self.request.get('username')
		email = self.request.get('email')
		name = self.request.get('name')
		password = self.request.get('password')
		last_name = self.request.get('lastname')
	 
		unique_properties = ['email_address']
		user_data = self.user_model.create_user(user_name, unique_properties,
												email_address=email, name=name, password_raw=password,
												last_name=last_name, verified=False)
		if not user_data[0]: #user_data is a tuple
			self.display_message('Unable to create user for email %s because of \
								  duplicate keys %s' % (user_name, user_data[1]))
			return
	 
		user = user_data[1]
		user_id = user.get_id()
	 
		token = self.user_model.create_signup_token(user_id)
	 
		verification_url = self.uri_for('verification', type='v', user_id=user_id,
										signup_token=token, _full=True)
	 
		msg = 'Send an email to user in order to verify their address. \
			  They will be able to do so by visiting  <a href="{url}">{url}</a>'
	 
		self.display_message(msg.format(url=verification_url))

class LoginHandler(BaseHandler):
	def get(self):
		self._serve_page()
	 
	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		try:
			u = self.auth.get_user_by_password(username, password, remember=True)
			self.redirect(self.uri_for('home'))
		except (InvalidAuthIdError, InvalidPasswordError) as e:
			logging.info('Login failed for user %s because of %s', username, type(e))
			self._serve_page(True)
	 
	def _serve_page(self, failed=False):
		username = self.request.get('username')
		params = {
			'username': username,
			'failed': failed
		}
		self.render_template('login.html', params)

class LogoutHandler(BaseHandler):
	def get(self):
		self.auth.unset_session()
		self.redirect(self.uri_for('home'))


class VerificationHandler(BaseHandler):
	def get(self, *args, **kwargs):
		user = None
		user_id = kwargs['user_id']
		signup_token = kwargs['signup_token']
		verification_type = kwargs['type']
	 
		# it should be something more concise like
		# self.auth.get_user_by_token(user_id, signup_token
		# unfortunately the auth interface does not (yet) allow to manipulate
		# signup tokens concisely
		user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token, 'signup')
	 
		if not user:
			logging.info('Could not find any user with id "%s" signup token "%s"',
						  user_id, signup_token)
			self.abort(404)
	 
		# store user data in the session
		self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
	 
		if verification_type == 'v':
		  # remove signup token, we don't want users to come back with an old link
			self.user_model.delete_signup_token(user.get_id(), signup_token)
	 
			if not user.verified:
				user.verified = True
				user.put()
	 
			self.display_message('User email address has been verified.')
			return
		elif verification_type == 'p':
			# supply user to the page
			params = {
				'user': user,
				'token': signup_token
			}
			self.render_template('resetpassword.html', params)
		else:
			logging.info('verification type not supported')
			self.abort(404)


class Index(BaseHandler):
	def get(self):
		cookie_exist = read_secure_cookie()
		username = ''
		item = ''
		name = ''

		if username:
			isAuthenticated = True
			item = 'banana'
			name = 'yeah!'
		else:
			isAuthenticated = False
			item = 'apple'
			name = 'sorry'

		self.render("index.html", username=username, isAuthenticated=isAuthenticated, item=item, name=name)

def user_required(handler):
	# """
	# 	Decorator that checks if there's a user associated with the current session.
	# 	Will also fail if there's no session present.
	# """
	def check_login(self, *args, **kwargs):
		auth = self.auth
		if not auth.get_user_by_session():
			self.redirect(self.uri_for('login'), abort=True)
		else:
			return handler(self, *args, **kwargs)
	 
		return check_login


class AuthenticatedHandler(BaseHandler):
	@user_required
	def get(self):
		self.render_template('authenticated.html')

config = {
	'webapp2_extras.auth': {
		'user_model': 'models.User',
		'user_attributes': ['name']
	},
	'webapp2_extras.sessions': {
		'secret_key': 'YOUR_SECRET_KEY'
	}
}

application = webapp2.WSGIApplication([('/', Index),
									   ('/login', 'handlers.login.login.Login'),
									   ('/signup', 'handlers.signup.signup.Signup'),
									   ('/logout', 'handlers.logout.logout.Logout'),
									   ('/post_item', 'handlers.post_item.post_item.Post_item'),
									   ('/item/(\d+)', 'handlers.post_item.post_item.Permalink')
									   ], 
									   debug=True)