import base64
from datetime import datetime, timedelta
import json
import webapp2
import urlparse

import artifact

from google.appengine.api import memcache
from google.appengine.api import urlfetch


ARTIFACTS_DIR = "https://api.github.com/repos/destijl/forensicartifacts/contents/artifacts/"
MIN_FETCH_INTERVAL = timedelta(hours=1)


class GitHubFetch(webapp2.RequestHandler):

  def CheckThrottle(self):
    last_fetch = memcache.get("last_github_fetch_time")
    if not last_fetch:
      return True
    return (datetime.now() - last_fetch) > MIN_FETCH_INTERVAL

  def get(self):
    if not self.CheckThrottle():
      self.response.write("Not retrieving due to throttle")
      return

    result = urlfetch.fetch(ARTIFACTS_DIR, validate_certificate=True)
    if not result.status_code == 200:
      self.response.status = result.status_code
      return

    dir_listing = json.loads(result.content)
    filenames = [x["name"] for x in dir_listing]

    for artifactfile in filenames:
      result = urlfetch.fetch(urlparse.urljoin(ARTIFACTS_DIR, artifactfile),
                              validate_certificate=True)

      if not result.status_code == 200:
        self.response.status = result.status_code
        return

      yaml_content = base64.decodestring(json.loads(result.content)["content"])
      artifact = artifact.Artifact(parent=artifact.ARTIFACT_STORE_KEY,
                                   filename=artifactfile, content=yaml_content)
      artifact.put()

    memcache.add("last_github_fetch_time", datetime.now())
    self.response.write("Retrieved artifact files: %s" % filenames)




