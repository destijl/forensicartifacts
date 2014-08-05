"""Tests for artifact."""

import json
import os
import unittest

import artifact
import thirdparty

import mock
import networkx
from networkx.readwrite import json_graph

from google.appengine.ext import ndb
from google.appengine.ext import testbed

ARTIFACT_PATH = "../artifacts/"


class ArtifactGraphTest(unittest.TestCase):

  def setUp(self):
    self.bootstrap = open(
        os.path.join(ARTIFACT_PATH, "windows_bootstrap.yaml")).read()
    self.windows = open(
        os.path.join(ARTIFACT_PATH, "windows.yaml")).read()
    self.linux = open(
        os.path.join(ARTIFACT_PATH, "linux.yaml")).read()
    self.yamlstring = "---\n".join((self.bootstrap, self.windows, self.linux))

    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_datastore_v3_stub()
    self.testbed.init_memcache_stub()

  def tearDown(self):
    self.testbed.deactivate()

  def _CheckGraph(self, graph):
    self.assertTrue("WindowsRegistryProfiles" in graph.nodes())
    self.assertItemsEqual(graph.neighbors("WMIProfileUsersHomeDir"),
                          ["WindowsRegistryProfiles"])
    self.assertItemsEqual(graph.neighbors("WindowsUserRegistryFiles"),
                          ["UserShellFolders", "WindowsRegistryProfiles",
                           "WMIProfileUsersHomeDir"])
    self.assertItemsEqual(graph.predecessors("MFTFiles"), ["Artifacts"])

    # Check we respect operating system constraints
    self.assertFalse(networkx.has_path(graph, "WMIAccountUsersDomain",
                                       "LinuxWtmp"))

  def testInitializeFromYAMLBuffers(self):
    graph = artifact.ArtifactGraph()
    graph.InitializeFromYAMLBuffers([self.windows, self.bootstrap, self.linux])
    self._CheckGraph(graph)

  def testLoadFromStore(self):
    test_parent_key = ndb.Key("ArtifactStore", "default")
    with mock.patch("artifact.ARTIFACT_STORE_KEY", test_parent_key) as mock_key:
      artifact_obj = artifact.Artifact(parent=test_parent_key,
                                       filename="all.yaml",
                                       content=self.yamlstring)
      artifact_obj.put()
      graph = artifact.ArtifactGraph()
      graph.LoadGraphFromDataStore()
      self._CheckGraph(graph)


if __name__ == "__main__":
  unittest.main()
