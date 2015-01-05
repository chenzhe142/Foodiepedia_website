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
		user = auth_models.User.get_by_id(u['user_id'])
		return user.name
 
	@webapp2.cached_property
	def auth(self):
		return auth.get_auth()
 
	@webapp2.cached_property
	def session_store(self):
		return sessions.get_store(request=self.request)
 

################################################################################################
#                Index page Handler	 				  	                                       #
################################################################################################
class Index(BaseHandler):
	def get(self):
		isAuthenticated = self.check_authenticated()

		username = ''
		if isAuthenticated:
			# get_current_username CANNOT FUNCTION 
			username = self.get_current_username()

		self.render("index.html", username=username, isAuthenticated=isAuthenticated)



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

									   ('/item/(\d+)', 'handlers.item.item_post_find.Permalink')
									   ], 
									   config=config,
									   debug=True)