"""Tests for artifact."""

import os
import unittest

import artifact

ARTIFACT_PATH = "../artifacts/"


class ArtifactGraphTest(unittest.TestCase):

  def setUp(self):
    self.yamlstring = open(os.path.join(ARTIFACT_PATH, "windows.yaml")).read()

  def testGraph(self):
    pass


if __name__ == '__main__':
  unittest.main()
