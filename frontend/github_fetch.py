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

  def GetArtifacts(self):
    if not self.CheckThrottle():
      return (500, "Not retrieving due to throttle")

    result = urlfetch.fetch(ARTIFACTS_DIR, validate_certificate=True)
    if not result.status_code == 200:
      return (result.status_code, "Error fetching %s from github" %
              ARTIFACTS_DIR)

    dir_listing = json.loads(result.content)
    filenames = [x["name"] for x in dir_listing]

    graph = artifact.ArtifactGraph()
    for artifactfile in filenames:
      url = urlparse.urljoin(ARTIFACTS_DIR, artifactfile)
      result = urlfetch.fetch(url, validate_certificate=True)

      if not result.status_code == 200:
        return (result.status_code, "Error fetching %s from github" % url)

      yaml_content = base64.decodestring(json.loads(result.content)["content"])
      artifact_obj = artifact.Artifact(parent=artifact.ARTIFACT_STORE_KEY,
                                   filename=artifactfile, content=yaml_content)
      artifact_obj.put()

    memcache.add("last_github_fetch_time", datetime.now())
    return (200, "Retrieved artifact files: %s" % filenames)

  def get(self):
    response_code, response_content = self.GetArtifacts()
    self.response.status = response_code
    self.response.write(response_content)
