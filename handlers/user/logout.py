import os
import jinja2
import webapp2

################################################################################################
#                           SET UP jinja2 working path, Handler                                #
################################################################################################

template_dir = os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, 'templates', 'login')
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
#                          logout handlers                                                     #
################################################################################################

class Logout(Handler):
	def get(self):
		#set cookie to empty
		new_cookie_val = ""
		self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % new_cookie_val)

		self.redirect('/signup')

	
		


application = webapp2.WSGIApplication([('/logout', Logout)], debug=True)