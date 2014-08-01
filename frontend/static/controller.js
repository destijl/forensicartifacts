var app = angular.module('Artifact', ['angularBootstrapNavTree', 'ngAnimate']);

app.controller('ArtifactController', function($scope, $http) {
  // TODO: Display all the artifact data in the yellow box.
  $scope.artifact_tree_handler = function(branch) {
    return $scope.output = branch.label
  };
  $scope.artifact_tree_data = [{label: "...Loading..."}];
  $http.get('/artifact_tree.json').success(function(data) {
    $scope.artifact_tree_data = data;
  });
});
