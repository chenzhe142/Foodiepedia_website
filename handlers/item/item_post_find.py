import os
import re
import random
import string
import hashlib
from string import letters

import handlers.user.user

import webapp2
from webapp2_extras import auth
from webapp2_extras import sessions

import jinja2

from google.appengine.ext import db

################################################################################################
#                           SET UP jinja2 working path, Handler                                #
################################################################################################

template_dir = os.path.join(os.path.dirname(__file__), os.path.pardir, 
							os.path.pardir, 'templates', 'item')
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
				self.redirect('/')
				# self.redirect(self.auth_config['login_url'], abort=True)
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

################################################################################################
#                set up Item database and query_string                                         #
################################################################################################
class Item(db.Model):
	item_name = db.StringProperty(required = True)
	item_description = db.TextProperty(required = True)
	item_photo_link = db.StringProperty(required = False)
	created = db.DateTimeProperty(auto_now_add = True)

################################################################################################
#                           Post-item handlers                                                 #
################################################################################################
class Post_item(BaseHandler):
	def render_post(self, item_name="", item_description="", item_photo_link="", error=""):
		items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC")

		self.render("post_item.html", item_name=item_name, 
									  item_description=item_description, 
									  item_photo_link=item_photo_link, 
					error=error, items=items)

	@user_required
	def get(self):
		self.render_post()

	def post(self):
		item_name = self.request.get('item_name')
		item_description = self.request.get('item_description')

		if item_name and item_description:
			i = Item(item_name=item_name, item_description=item_description)
			i_key = i.put()

			self.redirect("/item/%d" % i_key.id())
		else:
			error = "please enter both item name and item description!"
			self.render_post(item_name, item_description, error)

class PostShowPage(BaseHandler):
	def render_post_show(self, item_name="", item_description="", item_photo_link="", error=""):
		items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC")

		self.render("show_item.html", item_name=item_name, 
					item_description=item_description, 
					item_photo_link=item_photo_link, 
					error=error, items=items)

	def get(self):
		#handle html content
		self.render_post_show();

class Permalink(PostShowPage):
	def get(self, item_id):
		s = Item.get_by_id(int(item_id))
		self.render("show_item.html", items=[s])

################################################################################################
#                Find(search) page Handler	 				  	                               #
################################################################################################
class Find(BaseHandler):
	def get(self):
		isAuthenticated = self.check_authenticated
		username = ''
		if isAuthenticated:
			# get_current_username CANNOT FUNCTION 
			# username = self.get_current_username()
			username = 'show_username'
		self.render('find.html', isAuthenticated=isAuthenticated, username=username)

	def post(self, item_name="", item_description="", item_photo_link="", error=""):
		item_name = self.request.get('item_name')
		items = db.GqlQuery("SELECT * FROM Item WHERE item_name=:1", item_name)

		self.render("show_item.html", item_name=item_name, 
					item_description=item_description, 
					item_photo_link=item_photo_link, 
					error=error, items=items)




