/**
 * Controller to list all clouds and delete selected cloud
 */
nttApp.controller('CloudListCtrl', function($scope, ngToast, cloudService){
    $scope.cloudList = [];

    cloudService.list().then(function(data){
        $scope.cloudList = data;
    });

    $scope.delete = function($index){
        if(confirm("Are you sure want to delete?")){
            var cloudName = $scope.cloudList[$index].name;
            cloudService.delete($scope.cloudList[$index].id).then(
                function(data){
                    $scope.cloudList.splice($index, 1);
                    ngToast.create("<b>" + cloudName + "</b> cloud deleted successfully.");
                },
                function(error) {
                    console.log(error);
                    ngToast.create({
                        className: 'danger',
                        content: "Errors while deleting cloud <b>" + cloudName + ".</b>"
                    });
                }
            );
        }
    };

    $scope.cloud = {};
    $scope.eventType = "add";
    $scope.addCloud = function () {
        $scope.eventType = "add";
        $scope.event = event;
        $scope.cloud = {};
    };

    $scope.editCloud = function ($index) {
        $scope.eventType = "edit";
        $scope.cloud = angular.copy($scope.cloudList[$index]);
        $scope.cloud["$index"] = $index;
    };

    $scope.save = function(){
        if ($scope.eventType == "add") {
            cloudService.create($scope.cloud).then(
                function (response) {
                    $scope.cloudList.push(response);
                    ngToast.create("<b>" + response.name + "</b> cloud created successfully.");
                    $("#cloudFormModal").modal('hide');
                },
                function(error) {
                    console.log(error)
                }
            );
        }
        else {
            cloudService.update($scope.cloud.id, $scope.cloud).then(
                function(response) {
                    $scope.cloudList[$scope.cloud.$index] = response;
                    ngToast.create("<b>" + response.name + "</b> cloud updated successfully.");
                    $("#cloudFormModal").modal('hide');
                },
                function(error) {
                    console.log(error)
                }
            );
        }
    };

});


nttApp.controller('CloudViewCtrl', function($scope, $routeParams, $location, cloudService){
    $scope.id = $routeParams.id;
    $scope.event = $scope.id == undefined ? "add" : "edit";
    $scope.cloud = {};

    cloudService.get($scope.id).then(function(response){
        $scope.cloud = response;
    });
});
