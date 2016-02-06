import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

DEFAULT_COMMENT_NAME = 'default_comment'


def comment_key(comment_name=DEFAULT_COMMENT_NAME):
  """Constructs a Datastore key for a comment entity.

  We use comment_name as the key.
  """
  return ndb.Key('Comment', comment_name)


class Author(ndb.Model):
  """Sub model for representing an author."""
  identity = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=False)
  email = ndb.StringProperty(indexed=False)

class Post(ndb.Model):
  """A main model for representing an individual post entry."""
  author = ndb.StructuredProperty(Author)
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)


class MainPage(webapp2.RequestHandler):
  def get(self):
    comment_name = self.request.get('comment_name',DEFAULT_COMMENT_NAME)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL

     # [START query]
    comment_query = Comment.query(ancestor = comment_key(comment_name)).order(-Post.date)
  
    posts =  posts_query.fetch()
    
    # If a person is logged into Google's Services
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        user_name = user.nickname()
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
        user_name = 'Anonymous Poster'

    # Create our posts html
    posts_html = ''
    for post in posts:

      # Check if the current signed in user matches with the author's identity from this particular
      # post. Newline character '\n' tells the computer to print a newline when the browser is
      # is rendering our HTML
      if user and user.user_id() == post.author.identity:
        posts_html += '<div><h3>(You) ' + post.author.name + '</h3>\n'
      else:
        posts_html += '<div><h3>' + post.author.name + '</h3>\n'

      posts_html += 'wrote: <blockquote>' + cgi.escape(post.content) + '</blockquote>\n'
      posts_html += '</div>\n'

    sign_query_params = urllib.urlencode({'comment_name': comment_name})

    # Render our page
    rendered_HTML = HTML_TEMPLATE % (sign_query_params, cgi.escape(comment_name), user_name,
                                    url, url_linktext, posts_html)

    # Write Out Page here
    self.response.out.write(rendered_HTML)

class PostWall(webapp2.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Post' to ensure each
    # Post is in the same entity group. Queries across the
    # single entity group will be consistent. However, the write
    # rate to a single entity group should be limited to
    # ~1/second.
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    post = Post(parent=wall_key(wall_name))

    # When the person is making the post, check to see whether the person
    # is logged into Google
    if users.get_current_user():
      post.author = Author(
            identity=users.get_current_user().user_id(),
            name=users.get_current_user().nickname(),
            email=users.get_current_user().email())
    else:
      post.author = Author(
            name='anonymous@anonymous.com',
            email='anonymous@anonymous.com')


    # Get the content from our request parameters, in this case, the message
    # is in the parameter 'content'
    post.content = self.request.get('content')

    # Write to the Google Database
    post.put()

    # Do other things here such as a page redirect
    self.redirect('/?wall_name=' + wall_name)

app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/sign', PostWall),
], debug=True)