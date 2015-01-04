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

class BaseHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))	

	########################################
	# Cookie function					   #
	########################################
	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)
	# Cookie end

	#########################################
	# User authentication function			#
	#########################################
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
	 
	#########################################
	# User session 						    #
	#########################################
	@webapp2.cached_property
	def session(self):
		# """Shortcut to access the current session."""
		return self.session_store.get_session(backend="datastore")

	 
	# def render_template(self, view_filename, template, params={}):
	# 	user = self.user_info
	# 	params['user'] = user

	# 	# # change jinja2 template path
	# 	# template_dir = os.path.join(os.path.dirname(__file__),'templates',view_filename)
	# 	# jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

	# 	# self.render(template)	

	# 	# # recover default template path
	# 	# template_dir = os.path.join(os.path.dirname(__file__),'templates')
	# 	# jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)


	# 	path = os.path.join(os.path.dirname(__file__), 'templates', view_filename)

	# 	self.response.out.write(template.render(path, params))
	 
	def display_message(self, message):
		# """Utility function to display a template with a simple message."""
		params = {
		  'message': message
		}
		self.render_template('message', 'message.html', params)
	 
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