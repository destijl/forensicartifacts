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


class ArtifactGraph(networkx.DiGraph):

  # Hardcode these for now to hopefully make the node colors stay consistent
  OS_GROUP_MAP = {"Darwin": 1, "Windows": 2, "Linux": 3,
               "Darwin,Windows": 4, "Darwin,Linux": 5,
               "Darwin,Linux,Windows": 6, "Linux,Windows": 7}

  def __init__(self, *args, **kwargs):
    self.top_level = kwargs.pop("top_level", None)
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
      self.add_node(artifact_dict["name"], data_dict=artifact_dict)

      for dependency in self.GetArtifactPathDependencies(
          artifact_dict["collectors"]):
        for dep in self.provides_map[dependency]:
          dep_os = set(artifact_lookup_dict[dep]["supported_os"])
          if set(artifact_dict["supported_os"]).intersection(dep_os):
            self.add_edge(artifact_dict["name"], dep)

    # If top_level is set, take all nodes who have no predecessors and create a
    # root node with that name so we have an overall parent
    if self.top_level:
      for nodename, in_degree in self.in_degree().iteritems():
        if in_degree == 0:
          self.add_edge(self.top_level, nodename)
      self.node[self.top_level]["data_dict"] = {"supported_os": [
          "Darwin", "Linux", "Windows"]}

  def GetJSONTree(self, root, attrs={'children': 'children', 'id': 'label'}):
    """Based on networkx.readwrite.json_graph.tree_data()

    Unlike the original we allow non-tree graphs because our leaves can have
    multiple predecessors.  i.e. many nodes require SystemRoot.
    """
    id_ = attrs['id']
    children = attrs['children']
    if id_ == children:
        raise networkx.NetworkXError('Attribute names are not unique.')

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

  def GetD3JSON(self, group=None):
    """Converts a NetworkX Graph to D3.js JSON formatted dictionary"""
    ints_graph = networkx.convert_node_labels_to_integers(
        self, label_attribute="name")

    nodes_list = []
    os_group_map = {}
    next_int = 1
    for nodenum in ints_graph.nodes():
      artifact_name = ints_graph.node[nodenum]["name"]

      # Use supported_os as the node color
      supported_os_list = self.node[artifact_name]["data_dict"]["supported_os"]
      supported_os_list.sort()

      group = self.OS_GROUP_MAP[",".join(supported_os_list)]
      nodes_list.append(dict(name=artifact_name,
                             group=group))

    graph_edges = ints_graph.edges(data=True)

    # Build up edge dictionary in JSON format
    json_edges = list()
    for j, k, w in graph_edges:
      json_edges.append({'source' : j, 'target' : k, 'value': 1})

    graph_json = {"links": json_edges, "nodes": nodes_list}
    return json.dumps(graph_json)

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
