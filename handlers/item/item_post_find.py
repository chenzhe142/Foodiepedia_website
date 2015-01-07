import os
import re
import random
import string
import hashlib
from string import letters

import webapp2_extras.appengine.auth.models as auth_models

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
		user = auth_models.User.get_by_id(u['user_id'])
		return user.name

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
#                           Post-item handlers                                                 #
################################################################################################
class Post_item(BaseHandler):
	def render_post(self, item_name="", item_description="", item_photo_link="", error=""):
		page_title = 'Post | Foodiepedia'
		items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC")

		isAuthenticated = False
		isAuthenticated = self.check_authenticated()

		if not isAuthenticated:
			self.redirect('/')
		else:
			username = self.get_current_username()
			self.render("post_item.html", item_name=item_name, 
										  item_description=item_description, 
									  	  item_photo_link=item_photo_link, 
										  error=error, items=items, page_title=page_title)

	def get(self):
		page_title = 'Post | Foodiepedia'
		isAuthenticated = False
		isAuthenticated = self.check_authenticated()
		if not isAuthenticated:
			self.redirect('/')
		else:
			username = self.get_current_username()
			self.render('post_item.html',page_title=page_title,username=username)

	def post(self):
		item_name = self.request.get('item_name')
		item_description = self.request.get('item_description')
		item_photo_link = self.request.get('item_photo_link')

		username = self.get_current_username()
		page_title = 'Post | Foodiepedia'

		if item_name and item_description:
			i = Item(item_name=item_name, item_description=item_description, item_photo_link=item_photo_link)
			i_key = i.put()

			# self.redirect("/item/%d" % i_key.id())
			self.redirect("/item/%s" % i_key.item_name)
		else:
			error = "please enter both item name and item description!"
			self.render('post_item.html',item_name=item_name, 
										item_description=item_description,
										item_photo_link=item_photo_link, 
										error=error, username=username,
										page_title=page_title)

class PostShowPage(BaseHandler):
	def render_post_show(self, item_name="", item_description="", item_photo_link="", error=""):
		items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC")
		page_title = item_name + ' | Foodiepedia'

		self.render("show_item.html", item_name=item_name, 
					item_description=item_description, 
					item_photo_link=item_photo_link, 
					error=error, items=items, page_title=page_title)

	def get(self):
		#handle html content
		self.render_post_show();

class ItemPermalink(PostShowPage):
	# def get(self, item_id):
	def get(self, item_name):
		isAuthenticated = self.check_authenticated()
		username = ''
		if isAuthenticated:
			# get_current_username CANNOT FUNCTION 
			username = self.get_current_username()

		item_name = item_name.replace("-", " ")
		items = db.GqlQuery("SELECT * FROM Item WHERE item_name=:1", item_name)
		self.render("show_item.html", items=items, isAuthenticated=isAuthenticated, username=username)

		# s = Item.get_by_id(int(item_id))
		# self.render("show_item.html", items=[s], isAuthenticated=isAuthenticated, username=username)

################################################################################################
#                Find(search) page Handler	 				  	                               #
#                #need to redirect to item page 											   #
################################################################################################
class Find(BaseHandler):
	def get(self):
		page_title = 'Find | Foodiepedia'
		isAuthenticated = self.check_authenticated()
		username = ''
		if isAuthenticated:
			username = self.get_current_username()

		self.render('find.html', isAuthenticated=isAuthenticated, username=username, page_title=page_title)

	def post(self):
		item_name = str(self.request.get('item_name'))
		
		#########################
		#ISSUE: escape item_name#
		#########################
		if not item_name:
			#if user's input is empty, let's try redirect to homepage
			self.redirect('/')
		else:
			#if we have an input, try to redirect to result page
			item_name = item_name.replace(" ", "-")
			self.redirect("/find/result/%s" % item_name)

################################################################################################
#                FindPermalink Handler	 				  	                               	   #
################################################################################################
# redirect to result page																	   #
# Search algorithm needs to be re-designed 													   #
################################################################################################
class FindPermalink(PostShowPage):
	# def get(self, item_id):
	def get(self, item_name):
		isAuthenticated = self.check_authenticated()
		username = ''
		item_name = item_name.replace("-", " ")

		page_title = 'Result | Foodiepedia'

		if isAuthenticated:
			# get_current_username CANNOT FUNCTION 
			username = self.get_current_username()
		if item_name:
			items = db.GqlQuery("SELECT * FROM Item WHERE item_name=:1", item_name)
			self.render("show_item.html", items=items, 
						isAuthenticated=isAuthenticated, username=username, page_title=page_title)
		else:
			if items == '':
				self.render("popular_item.html", 
							isAuthenticated=isAuthenticated, username=username, page_title=page_title)


