nttApp.controller('TrafficListCtrl', function($scope, $routeParams, trafficService){
    $scope.trafficList = [];
    trafficService.list($routeParams.id).then(function(response){
        $scope.trafficList = response;
    });

    $scope.delete = function($index){
        if (confirm("Are you sure want to delete?")){
            trafficService.delete($scope.trafficList[$index].id).then(function(response){
                $scope.trafficList.splice($index, 1);
            });
        }
    };
});


nttApp.controller('TrafficCtrl', function($scope, $routeParams, $location, trafficService, tenantService){
    $scope.cloudId = $routeParams.cloudId;
    $scope.id = $routeParams.id;
    $scope.event = $scope.id == undefined ? "add" : "edit";
    $scope.traffic = {
        "cloud_id": $scope.cloudId,
        "test_type": "intra-tenant",
        "test_environment": "dev",
    };

    if ($scope.event == "edit"){
        trafficService.get($scope.id).then(function(response){
            $scope.traffic = response;
            var testMethods = {
                icmp: false,
                tcp: false,
                udp: false
            };
            angular.forEach(response.test_method.split(","), function (testMethod, i) {
                testMethods[testMethod] = true;
            });
            $scope.traffic["test_method"] = testMethods;
        });
    }

    $scope.save = function(){
        var selectedTestMethods = [];
        angular.forEach($scope.traffic.test_method, function (isSelected, testMethod) {
            if(isSelected){
                selectedTestMethods.push(testMethod)
            }
        });
        $scope.traffic["test_method"] = selectedTestMethods.join();

        if($scope.event == "add") {
            trafficService.create($scope.traffic).then(function (response) {
                $location.path("cloud/traffic/view/" + $scope.cloudId + "/" + response.id + "/");
            });
        }
        else {
            trafficService.update($scope.traffic.id, $scope.traffic).then(function(response){
                $location.path("cloud/traffic/view/" + $scope.cloudId + "/" + $scope.traffic.id + "/");
            });
        }
    };
});


nttApp.controller('TrafficViewCtrl', function($scope, $routeParams, trafficService, tenantService){
    $scope.cloudId = $routeParams.cloudId;
    $scope.id = $routeParams.id;
    $scope.traffic = {};

    trafficService.getWithRelatedData($scope.id).then(function(response){
        $scope.traffic = response;
        $scope.getTenants();
        $scope.getEndpoints();
    });

    $scope.isAnyNetworkSelected = false;
    $scope.tenants = [];
    $scope.getTenants = function(){
        tenantService.list($scope.cloudId).then(function(response){
            $scope.tenants = response;
            // Iterating through tenants to make radio button checked for matching tenant
            angular.forEach(response, function(tenant, i){
                if ($scope.traffic.tenants[0].tenant_id == tenant.tenant_id){
                    $scope.traffic.tenants[0] = tenant;
                    angular.forEach($scope.traffic.tenants[0].networks, function(network, j){
                        angular.forEach($scope.traffic.selected_networks, function(selectedNetwork, k){
                            if(selectedNetwork.network == network.id){
                                network["is_selected"] = true;
                                if($scope.traffic.test_environment == 'prod'){
                                    network["endpoint_count"] = selectedNetwork.endpoint_count;
                                }
                                else{
                                    network.subnets[0]["ip_range_start"] = selectedNetwork.ip_range_start;
                                    network.subnets[0]["ip_range_end"] = selectedNetwork.ip_range_end;    
                                }
                                $scope.isAnyNetworkSelected = true;
                            }
                        });
                    });
                }
            });
        });
    };

    $scope.selectTenant = function(tenant_id){
        trafficService.selectTenant($scope.traffic.id, tenant_id).then(function(response){
            console.log(response)
        });
    };

    $scope.selectNetwork = function($index, networkId, isSelected){
        var params = {
            "network_id": networkId,
            "is_selected": isSelected,
        };
        trafficService.selectNetwork($scope.traffic.id, params).then(function(response){
            if(isSelected){
                $scope.traffic.tenants[0].networks[$index].subnets[0] = response;
            }
        });
    };

    $scope.$watch('traffic.tenants[0].networks', function(newValues, oldValue, scope){
        var flag = false;
        angular.forEach(newValues, function(network, i){
            if(network.is_selected){
                flag = true
            }
        });
        $scope.isAnyNetworkSelected = flag;
    }, true);

    $scope.showLoadingEndpoints = false;
    $scope.endpoints = [];
    $scope.getEndpoints = function () {
        trafficService.endpoints($scope.traffic.id).then(function(response){
            $scope.endpoints = response;
        });
    };
    
    $scope.discoverEndpoints = function(){
        $scope.showLoadingEndpoints = true;
        $scope.endpoints = [];
        var selectedItems = [];
        
        angular.forEach($scope.traffic.tenants[0].networks, function(network, i){
            console.log(network.is_selected)
            if(network.is_selected){
                if($scope.traffic.test_environment == 'prod'){
                    selectedItems.push({
                        "network_id": network.id,
                        "endpoint_count": network.endpoint_count
                    })
                }
                else {
                    selectedItems.push({
                        "network_id": network.id,
                        "ip_range_start": network.subnets[0].ip_range_start,
                        "ip_range_end": network.subnets[0].ip_range_end,
                    });
                }
            }
        });

        if($scope.traffic.test_environment == "dev") {
            trafficService.discoverEndpoints($scope.traffic.id, selectedItems).then(function (response) {
                $scope.endpoints = response;
                $scope.showLoadingEndpoints = false;
        
            });
        }
        else {
            trafficService.launchEndpoints($scope.traffic.id, selectedItems).then(function (response) {
                $scope.endpoints = response;
                $scope.showLoadingEndpoints = false;
            });
        }
    };

    $scope.selectEndpoint = function($index) {
        var endpoint = $scope.endpoints[$index];
        var params = {
            "endpoint_pk": endpoint.id,
            "endpoint_id": endpoint.endpoint_id,
            "is_selected": endpoint.is_selected
        };
        trafficService.selectEndpoint($scope.traffic.id, params).then(function (response) {
            $scope.endpoints[$index] = response;
        });
    };

    
    $scope.testResult = {};
    $scope.testResultRunning = false;
    $scope.runTrafficTest = function (trafficId) {
        $scope.testResultRunning = true;
        trafficService.runTrafficTest(trafficId).then(function (response) {
            $scope.testResult = response;
            $scope.testResultRunning = false;
        });
    };

    var doc = new jsPDF();
    var specialElementHandlers = {
        '#editor': function (element, renderer) {
            return true;
        }
    };
    $scope.exportTrafficTestResults = function () {
        doc.fromHTML($('#traffic-test-results').html(), 10, 10, {
            'width': 200,
            'elementHandlers': specialElementHandlers
        });
        doc.save('traffic-test-report.pdf');
    };
    
    
    $scope.emailReport = function () {
        trafficService.emailReport($scope.traffic.id).then(function (response) {
            console.log(response)
        });
    }
});
