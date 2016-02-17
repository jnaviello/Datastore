import jinja2
import webapp2
import urllib
import os
import time
from google.appengine.api import users
from google.appengine.ext import ndb



template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

DEFAULT_WALL = 'Public'


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

def guestbook_key(guestbook_name=DEFAULT_WALL):
    return ndb.Key('Guestbook', guestbook_name)

class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

class Greeting(ndb.Model):
    name = ndb.StringProperty()
    comment = ndb.StringProperty(indexed=True)
    date = ndb.DateTimeProperty(auto_now_add=True)



class MainPage(Handler):
    def get(self):
        guestbook_name = self.request.get('guestbook_name', DEFAULT_WALL)
        max_posts=20
        error= self.request.get('error', "")
        # [START query]
        greetings_query = Greeting.query(ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(max_posts)
        # Check if a person is logged into Google's Services
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'

        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        template_values = {
            'user': user,
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
            'error': error
        }

        template = jinja_env.get_template('Notes.html')
        self.response.write(template.render(template_values))


class Guestbook(Handler):
    def post(self):
        guestbook_name = self.request.get('guestbook_name', DEFAULT_WALL).strip()
        greeting = Greeting(parent=guestbook_key(guestbook_name))
        if users.get_current_user():
            greeting.author = Author(identity=users.get_current_users().user_id(),email=users.get_current_user().email)
        greeting.content = self.request.get('content')
        greeting.content.strip()
        if greeting.content == '':
            error = "I'm sorry that's not a valid comment!"
            self.redirect('/?' + error)
        else:
            greeting.put()
            query_params = {'guestbook_name':guestbook_name}
            self.redirect('/?'+ urllib.urlencode(query_params))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
    ], debug=True)
