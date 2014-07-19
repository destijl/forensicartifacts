import sys
import yaml

sys.path.insert(0, 'thirdparty/networkx-1.9')
sys.path.insert(0, 'thirdparty/decorator-3.4.0/src')
import networkx

from google.appengine.ext import ndb


ARTIFACT_STORE_KEY = ndb.Key("ArtifactStore", "default")


class Artifact(ndb.Model):
  filename = ndb.StringProperty()
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)


class ArtifactGraph(networkx.Graph):

  def InitializeFromYAML(self, yaml_buffer):
    pass


