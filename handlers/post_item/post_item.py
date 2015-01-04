import os
import re
import random
import string
import hashlib
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

################################################################################################
#                           SET UP jinja2 working path, Handler                                #
################################################################################################

template_dir = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, 'templates', 'post_item')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

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
class Post_item(Handler):
	def render_post(self, item_name="", item_description="", item_photo_link="", error=""):
		items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC")

		self.render("post_item.html", item_name=item_name, item_description=item_description, item_photo_link=item_photo_link, 
					error=error, items=items)

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

class PostShowPage(Handler):
	def render_post_show(self, item_name="", item_description="", item_photo_link="", error=""):
		items = db.GqlQuery("SELECT * FROM Item ORDER BY created DESC")

		self.render("show_item.html", item_name=item_name, item_description=item_description, item_photo_link=item_photo_link, 
					error=error, items=items)

	def get(self):
		#handle html content
		self.render_post_show();

class Permalink(PostShowPage):
	def get(self, item_id):
		s = Item.get_by_id(int(item_id))
		self.render("show_item.html", items=[s])













