"""Tests for artifact."""

import json
import os
import unittest

import artifact
from thirdparty import mock
from thirdparty import networkx

from google.appengine.ext import ndb
from google.appengine.ext import testbed

ARTIFACT_PATH = "../artifacts/"


class ArtifactGraphTest(unittest.TestCase):

  def setUp(self):
    self.bootstrap = open(
        os.path.join(ARTIFACT_PATH, "windows_bootstrap.yaml")).read()
    self.windows = open(
        os.path.join(ARTIFACT_PATH, "windows.yaml")).read()
    self.yamlstring = "---\n".join((self.bootstrap, self.windows))

    # First, create an instance of the Testbed class.
    self.testbed = testbed.Testbed()
    # Then activate the testbed, which prepares the service stubs for use.
    self.testbed.activate()
    # Next, declare which service stubs you want to use.
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

  def testInitializeFromYAMLBuffers(self):
    graph = artifact.ArtifactGraph()
    graph.InitializeFromYAMLBuffers([self.windows, self.bootstrap])
    self._CheckGraph(graph)
    graph.InitializeFromYAMLBuffers([self.windows])
    graph.InitializeFromYAMLBuffers([self.bootstrap])
    self._CheckGraph(graph)

  def testLoadFromStore(self):
    test_parent_key = ndb.Key("ArtifactStore", "default")
    with mock.patch("artifact.ARTIFACT_STORE_KEY", test_parent_key) as mock_key:
      artifact_obj = artifact.Artifact(parent=test_parent_key,
                                       filename="windows.yaml",
                                       content=self.yamlstring)
      artifact_obj.put()
      graph = artifact.ArtifactGraph()
      graph.LoadGraphFromDataStore()
      self._CheckGraph(graph)


if __name__ == "__main__":
  unittest.main()
