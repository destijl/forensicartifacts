import os
import json
import webapp2
import sys

import artifact
import github_fetch

from google.appengine.api import memcache


class JSONTree(webapp2.RequestHandler):

  def get(self):
    graph = memcache.get("artifact_graph")
    if not graph:
      # Try to get a fresh version
      github_fetch.GitHubFetch().GetArtifacts()

      # Load whatever we have from the datastore
      graph = artifact.ArtifactGraph(top_level="Artifacts")
      graph.LoadGraphFromDataStore()
      memcache.add("artifact_graph", graph)

    self.response.write(graph.GetJSONTree("Artifacts"))

class D3JSON(webapp2.RequestHandler):

  def get(self):
    d3json = memcache.get("d3json")
    if not d3json:
      graph = memcache.get("d3artifact_graph")
      if not graph:
        # Try to get a fresh version
        github_fetch.GitHubFetch().GetArtifacts()

        # Load whatever we have from the datastore
        graph = artifact.ArtifactGraph()
        graph.LoadGraphFromDataStore()
        memcache.add("d3artifact_graph", graph)

      d3json = graph.GetD3JSON()
      memcache.add("d3json", d3json)

    self.response.write(d3json)


application = webapp2.WSGIApplication([
    ("/artifact_tree.json", JSONTree),
    ("/d3artifact_tree.json", D3JSON),
    ("/githubfetch", github_fetch.GitHubFetch),
], debug=True)
