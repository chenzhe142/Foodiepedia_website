import os
import jinja2
import webapp2

import webapp2_extras.appengine.auth.models as auth_models

from webapp2_extras import auth
from webapp2_extras import sessions

################################################################################################
#               SET UP jinja2 working path, BaseHandler function                               #
################################################################################################
template_dir = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir,'templates','find')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

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

################################################################################################
#                Find(search) page Handler	 				  	                               #
################################################################################################
class Find(BaseHandler):
	def get(self):
		isAuthenticated = self.check_authenticated()
		username = ''
		if isAuthenticated:
			# get_current_username CANNOT FUNCTION 
			username = self.get_current_username()
		self.render('find.html', isAuthenticated=isAuthenticated, username=username)

	def post(self):
		item_name = self.request.get('item_name')
		
		





