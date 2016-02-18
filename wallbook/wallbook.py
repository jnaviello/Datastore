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

#global variable error is set to False
error = False


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
    name = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

class Post(ndb.Model):
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=True)
    date = ndb.DateTimeProperty(auto_now_add=True)



class MainPage(Handler):
    def get(self):
        guestbook_name = self.request.get('guestbook_name', DEFAULT_WALL)
        max_posts=10
        # [START query]
        post_query = Post.query(ancestor=guestbook_key(guestbook_name)).order(-Post.date)
        post = post_query.fetch(max_posts)
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
            'post': post,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
            'error': error
        }

        template = jinja_env.get_template('Notes.html')
        self.response.write(template.render(template_values))


class Guestbook(webapp2.RequestHandler):
    def post(self):
#I am declaring the variable error as global
        global error
        time_to_sleep = .1
        guestbook_name = self.request.get('guestbook_name', DEFAULT_WALL).strip()
        post = Post(parent=guestbook_key(guestbook_name))

        post.content = self.request.get('content')

        if users.get_current_user():
            post.author = Author(identity=users.get_current_users().user_id(),
                                 name=users.get_current_user().nickname(),
                                 email=users.get_current_user().email)
        else:
            post.author = Author(name='anonymous@anonymous.com',
                                 email='anonymous@anonymous.com')

# I am using the isspace() method to check if the comment is blank and assigning the global variable error to True
# or False depending on the condition
        if post.content and(not post.content.isspace()):
            error = False
            post.put()
        else:
            error = True
            self.redirect('/?Notes.html')

        time.sleep(time_to_sleep)
        query_params = {'guestbook_name': guestbook_name, 'error':error}
        self.redirect('/?' + urllib.urlencode(query_params))

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/sign', Guestbook),
                               ], debug=True)
