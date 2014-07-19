import webapp2
import sys

import github_fetch


class MainPage(webapp2.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.write('placeholder')


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/githubfetch', github_fetch.GitHubFetch),
], debug=True)
