/**
 * Controller to list all clouds and delete selected cloud
 */
nttApp.controller('CloudListCtrl', function($scope, cloudService){
    $scope.cloudList = [];

    cloudService.list().then(function(data){
        $scope.cloudList = data;
    });

    $scope.delete = function($index){
        if(confirm("Are you sure want to delete?")){
            cloudService.delete($scope.cloudList[$index].id).then(function(data){
               $scope.cloudList.splice($index, 1);
            });
        }
    };
});


nttApp.controller('CloudCtrl', function($scope, $routeParams, $location, cloudService){
    $scope.id = $routeParams.id;
    $scope.event = $scope.id == undefined ? "add" : "edit";
    $scope.cloud = {};

    if($scope.event == "edit"){
        cloudService.get($scope.id).then(function(data){
            $scope.cloud = data;
        });
    }

    $scope.save = function(){
        if ($scope.event == "add") {
            cloudService.create($scope.cloud).then(function (response) {
                $location.path("cloud/view/" + response.id + "/");
            });
        }
        else {
            cloudService.update($scope.cloud.id, $scope.cloud).then(function(response){
                $location.path("cloud/view/" + response.id + "/");
            });
        }
    };
});



nttApp.controller('CloudTrafficCtrl', function($scope, $routeParams, $location, cloudService, cloudTrafficService){
    $scope.cloud = {};
    $scope.event = $routeParams.event;
    cloudService.get($routeParams.cloudId).then(function(data){
        $scope.cloud = data;
    });

    $scope.cloudTraffic = {
        "tenant_type": "all"
    };
    if($scope.event == 'edit'){
        cloudTrafficService.get($routeParams.trafficId).then(function(data){
            $scope.cloudTraffic = data;
        });
    };

    $scope.save = function(){
        if($scope.event == 'add') {
            $scope.cloudTraffic["cloud"] = $scope.cloud.id;
            cloudTrafficService.create($scope.cloudTraffic).then(function (data) {
                $location.path("cloudtraffic/view/" + data.id + "/");
            });
        }
        else{
            cloudTrafficService.update($scope.cloudTraffic.id, $scope.cloudTraffic).then(function (data) {
                $location.path("cloudtraffic/view/" + data.id + "/");
            });
        }
    };
});

nttApp.controller('CloudTrafficViewCtrl', function($scope, $routeParams, $location, cloudService, cloudTrafficService, cloudTrafficTenantService){
    $scope.cloud = {};
    $scope.cloudTrafficId = $routeParams.id;
    $scope.cloudTraffic = {};

    cloudTrafficService.get($scope.cloudTrafficId).then(function(data){
        $scope.cloudTraffic = data;
        $scope.getCloud($scope.cloudTraffic.cloud);
    });

    $scope.getCloud = function(cloudId){
        cloudService.get(cloudId).then(function(data){
            $scope.cloud = data;
        });
    }

    $scope.tenantEvent = "add";
    $scope.tenants = [];
    $scope.tenant = {};
    cloudTrafficTenantService.list($scope.cloudTrafficId).then(function(data){
       $scope.tenants = data;
    });

    $scope.addTenant = function(){
        $scope.tenantEvent = "add";
        $scope.tenant["cloud_traffic_id"] = $scope.cloudTraffic.id;
        cloudTrafficTenantService.create($scope.tenant).then(function(data){
            $scope.tenants.push(data);
            $('#addTenantModal').modal('hide');
        });
    };

    $scope.editTenant = function($index){
        $scope.tenantEvent = "edit";
        $scope.tenant = angular.copy($scope.tenants[$index]);
        cloudTrafficTenantService.update($scope.tenant.id, $scope.tenant).then(function(data){
            $scope.tenant[$index] = data;
            $('#addTenantModal').modal('hide');
        });
    };

    $scope.saveTenant = function(event, $index){
        cloudTrafficTenantService.save($scope.tenant).then(function(data){
            $scope.tenant = {};
            return data;
        });
    }

    $scope.deleteTenant = function($index){
        if(confirm("Are you sure you want to delete?")){
            cloudTrafficTenantService.delete($scope.tenants[$index].id).then(function(data){
               $scope.tenants.splice($index, 1);
            });
        }
    };

    $scope.saveExternalHost = function(){
        cloudTrafficService.update($scope.cloudTraffic.id, $scope.cloudTraffic).then(function (data) {
            $location.path("cloudtraffictest");
        });
    };
});

nttApp.controller('CloudTrafficTestCtrl', function($scope, $location, cloudTrafficService){

});

