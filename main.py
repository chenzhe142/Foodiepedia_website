import os
import jinja2
import webapp2

import time
import urllib2
import webapp2_extras.appengine.auth.models as auth_models

import sys
from google.appengine.ext import ndb
# sys.modules['ndb'] = ndb

from google.appengine.ext import db


from webapp2_extras import security
from webapp2_extras import auth
from webapp2_extras import sessions

from webapp2_extras.auth import InvalidAuthIdError
from webapp2_extras.auth import InvalidPasswordError

from webapp2_extras.routes import RedirectRoute


################################################################################################
#               SET UP jinja2 working path, BaseHandler function                               #
################################################################################################
template_dir = os.path.join(os.path.dirname(__file__),'templates','main')
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

	def get_user_profile_link(self, username):
		user_profile_link = '/user/' + username
		return user_profile_link

	def get_navbar_status(self):
		isAuthenticated = False
		isAuthenticated = self.check_authenticated()

		params = dict(isAuthenticated=isAuthenticated)

		if not isAuthenticated:
			return params;
		else:
			params['username'] = self.get_current_username()
			params['user_profile_link'] = self.get_user_profile_link(params['username'])
			return params;

	########################################################


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
#                set up Item database and query_string                                         #
################################################################################################
class Item(db.Model):
	item_name = db.StringProperty(required = True)
	item_description = db.TextProperty(required = True)
	item_photo_link = db.StringProperty(required = False)
	created = db.DateTimeProperty(auto_now_add = True)

################################################################################################
#                Index page Handler	 				  	                                       #
################################################################################################
class IndexHandler(BaseHandler):
	def get(self):
		page_title = 'Foodiepedia'

		params = dict()
		params = self.get_navbar_status()
		params['page_title'] = page_title

		self.render('index.html', **params)


################################################################################################
#                About Handler	 				  	                                           #
################################################################################################
class AboutHandler(BaseHandler):
	def get(self):
		page_title = 'About | Foodiepedia'

		params = dict()
		params = self.get_navbar_status()
		params['page_title'] = page_title

		self.render('about.html', **params)

################################################################################################
#                Advertising Handler	 				  	                                   #
################################################################################################
class AdvertisingHandler(BaseHandler):
	def get(self):
		page_title = 'Advertising | Foodiepedia'

		params = dict()
		params = self.get_navbar_status()
		params['page_title'] = page_title

		self.render('advertising.html', **params)


################################################################################################
#                Contact us Handler	 				  	                                       #
################################################################################################
class ContactUsHandler(BaseHandler):
	def get(self):
		page_title = 'Contact us | Foodiepedia'

		params = dict()
		params = self.get_navbar_status()
		params['page_title'] = page_title

		self.render('contact_us.html', **params)

################################################################################################
#                API Handler	 				  	                                           #
################################################################################################
class ApiHandler(BaseHandler):
	def get(self):
		page_title = 'API | Foodiepedia'

		params = dict()
		params = self.get_navbar_status()
		params['page_title'] = page_title

		self.render('api.html', **params)


################################################################################################
#                Discover Handler	 				  	                                       #
################################################################################################
class Discover(BaseHandler):
	def get(self):
		page_title = 'Discover | Foodiepedia'

		params = dict()
		params = self.get_navbar_status()
		params['page_title'] = page_title

		self.render('about.html', **params)


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

application = webapp2.WSGIApplication([('/', IndexHandler),
									   ('/about', AboutHandler),
									   ('/advertising', AdvertisingHandler),
									   ('/contact_us', ContactUsHandler),
									   ('/api', ApiHandler),

									   webapp2.Route(r'/login', handler='handlers.user.user.LoginHandler', name='login'),
									   webapp2.Route(r'/logout', handler='handlers.user.user.LogoutHandler', name='logout'),
									   webapp2.Route(r'/login', handler='handlers.user.user.SecureRequestHandler', name='secure'),
									   ('/signup', 'handlers.user.user.CreateUserHandler'),
									   ('/user/(\S+)', 'handlers.user.user.UserProfileHandler'),

									   # ('/discover','handlers.discover.discover.Discover'),
									   ('/discover', Discover),
									   ('/find', 	  'handlers.item.item_post_find.Find'),


									   ('/post_item', 'handlers.item.item_post_find.Post_item'),
									   ('/item/(\S+)', 'handlers.item.item_post_find.ItemPermalink'),

									   ('/find/result/(\S+)', 'handlers.item.item_post_find.FindPermalink')
									   ], 
									   config=config,
									   debug=True)