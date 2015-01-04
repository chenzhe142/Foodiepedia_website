import os
import jinja2
import webapp2

import time
import webapp2_extras.appengine.auth.models as auth_models

import sys
from google.appengine.ext import ndb
# sys.modules['ndb'] = ndb


from webapp2_extras import security
from webapp2_extras import auth
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError



################################################################################################
#               SET UP jinja2 working path, BaseHandler function                               #
################################################################################################
template_dir = os.path.join(os.path.dirname(__file__),'templates')
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

	def get_current_username(self):
		# PROBLEM: CANNOT FIND CURRENT USER'S NAME
		u = self.auth.get_user_by_session()
		userid = u['user_id']
		username = auth_models.User.get_by_auth_id(str(u['user_id']))
		if username is None:
			username = ''

		return username


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

################################################################################################
#                Index page Handler	 				  	                                       #
################################################################################################
class Index(BaseHandler):
	def get(self):
		isAuthenticated = self.check_authenticated()

		username = ''
		if isAuthenticated:
			# get_current_username CANNOT FUNCTION 
			# username = self.get_current_username()
			username = 'show_username'
		
		name = 'apple'

		self.render("index.html", username=username, isAuthenticated=isAuthenticated, name=name)



################################################################################################
#                Config information 	 				                                       #
################################################################################################
config = {
	# 'webapp2_extras.auth': {
	# 	'user_model': 'models.User',
	# 	'user_attributes': ['name']
	# },
	'webapp2_extras.sessions': {
		'secret_key': 'b11e05a05dsadf702527e16bae300bc339fda3139b6ce'
	}
}

application = webapp2.WSGIApplication([('/', Index),
									   webapp2.Route(r'/login', handler='handlers.user.user.LoginHandler', name='login'),
									   webapp2.Route(r'/logout', handler='handlers.user.user.LogoutHandler', name='logout'),
									   webapp2.Route(r'/login', handler='handlers.user.user.SecureRequestHandler', name='secure'),
									   ('/signup', 'handlers.user.user.CreateUserHandler'),

									   ('/discover','handlers.discover.discover.Discover'),
									   ('/find', 	  'handlers.item.item_post_find.Find'),
									   ('/post_item', 'handlers.item.item_post_find.Post_item'),

									   ('/item/(\d+)', 'handlers.post_item.post_item.Permalink')
									   ], 
									   config=config,
									   debug=True)