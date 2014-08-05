import itertools
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


#    TODO: add another method to get artifact list dependencies, see
#    KasperskyCareto artifacts
#    Group the tree by OS


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
    """Create the tree from a list of yaml buffers.

    All buffers must be passed in at once to allow a valid dependency tree to be
    created.
    """
    raw_list = []
    for yaml_buffer in yaml_buffers:
      raw_list.extend(list(yaml.safe_load_all(yaml_buffer)))

    self.UpdateProvidesMap(raw_list)

    # Use this lookup dict to check os conditions so we don't create
    # dependencies across operating system boundaries
    artifact_lookup_dict = {}
    for artifact_dict in raw_list:
      artifact_lookup_dict[artifact_dict["name"]] = artifact_dict

    for artifact_dict in raw_list:
      self.add_node(artifact_dict["name"])
      for dependency in self.GetArtifactPathDependencies(
          artifact_dict["collectors"]):
        for dep in self.provides_map[dependency]:
          dep_os = set(artifact_lookup_dict[dep]["supported_os"])
          if set(artifact_dict["supported_os"]).intersection(dep_os):
            self.add_edge(artifact_dict["name"], dep)

    # Take all nodes who have no predecessors and put them under a root node so
    # we have a real tree
    for nodename, in_degree in self.in_degree().iteritems():
      if in_degree == 0:
        self.add_edge("Artifacts", nodename)

  def GetJSONTree(self, root, attrs={'children': 'children', 'id': 'label'}):
    """Based on networkx.readwrite.json_graph.tree_data()

    Unlike the original we allow non-tree graphs because our leaves can have
    multiple predecessors.  i.e. many nodes require SystemRoot.
    """
    id_ = attrs['id']
    children = attrs['children']
    if id_ == children:
        raise nx.NetworkXError('Attribute names are not unique.')

    def add_children(n, self):
        nbrs = self[n]
        if len(nbrs) == 0:
            return []
        children_ = []
        for child in nbrs:
            d = dict(itertools.chain(self.node[child].items(), [(id_, child)]))
            c = add_children(child, self)
            if c:
                d[children] = c
            children_.append(d)
        return children_

    data = dict(itertools.chain(self.node[root].items(), [(id_, root)]))
    data[children] = add_children(root, self)
    return json.dumps([data])

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






