import re
import json
import sys
import yaml

from thirdparty import networkx

from google.appengine.ext import ndb


ARTIFACT_STORE_KEY = ndb.Key("ArtifactStore", "default")
INTERPOLATED_REGEX = re.compile(r"%%([^%]+?)%%")


class Artifact(ndb.Model):
  filename = ndb.StringProperty()
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)


class ArtifactGraph(networkx.DiGraph):

  def __init__(self, *args, **kwargs):
    super(ArtifactGraph, self).__init__(*args, **kwargs)
    self.provides_map = {}

  def UpdateProvidesMap(self, artifact_dicts):
    for artifact_dict in artifact_dicts:
      if "provides" in artifact_dict:
        for attr in artifact_dict["provides"]:
          self.provides_map.setdefault(attr, []).append(artifact_dict["name"])

  def LoadGraphFromDataStore(self):
    results = Artifact.query(ancestor=ARTIFACT_STORE_KEY).fetch()
    self.InitializeFromYAMLBuffers([x.content for x in results])

  def InitializeFromYAMLBuffers(self, yaml_buffers):
    raw_list = []
    for yaml_buffer in yaml_buffers:
      raw_list.extend(list(yaml.safe_load_all(yaml_buffer)))

    self.UpdateProvidesMap(raw_list)

    for artifact_dict in raw_list:
      self.add_node(artifact_dict["name"])
      for dependency in self.GetArtifactPathDependencies(
          artifact_dict["collectors"]):
        for dep in self.provides_map[dependency]:
          self.add_edge(artifact_dict["name"], dep)

  def GetJSONDictOfDicts(self):
    return json.dumps(networkx.to_dict_of_dicts(self))

  def GetArtifactPathDependencies(self, collectors):
    """Return a set of knowledgebase path dependencies.

    Returns:
      A set of strings for the required kb objects e.g.
      ["users.appdata", "systemroot"]
    """
    deps = set()
    for collector in collectors:
      for arg, value in collector["args"].items():
        paths = []
        if arg in ["path", "query"]:
          paths.append(value)
        if arg in ["paths", "path_list", "content_regex_list"]:
          paths.extend(value)
        for path in paths:
          for match in INTERPOLATED_REGEX.finditer(path):
            deps.add(match.group()[2:-2])   # Strip off %%.
    return deps







