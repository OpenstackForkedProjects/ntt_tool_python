nttApp.controller('TrafficListCtrl', function($scope, $routeParams, trafficService){
    $scope.cloudId = $routeParams.id;
    $scope.trafficList = [];
    trafficService.list($scope.cloudId).then(function(response){
        $scope.trafficList = response;
    });

    $scope.delete = function($index){
        if (confirm("Are you sure want to delete?")){
            trafficService.delete($scope.trafficList[$index].id).then(function(response){
                $scope.trafficList.splice($index, 1);
            });
        }
    };

    $scope.eventType = "add";
    $scope.traffic = {};
    $scope.addTraffic = function () {
        $scope.eventType = "add";
        $scope.traffic = {};
        $scope.traffic["cloud_id"] = $scope.cloudId;
        $scope.traffic["test_type"] = "intra-tenant";
        $scope.traffic["test_environment"] = "dev";
    };

    $scope.editTraffic = function ($index) {
        $scope.eventType = "edit";
        $scope.traffic = {};
        $scope.traffic = angular.copy($scope.trafficList[$index]);
        $scope.traffic["$index"] = $index;
    };
    
    $scope.save = function () {
        var selectedTestMethods = [];
        angular.forEach($scope.traffic.test_method, function (isSelected, testMethod) {
            if(isSelected){
                selectedTestMethods.push(testMethod)
            }
        });

        var trafficObj = angular.copy($scope.traffic);
        trafficObj["test_method"] = selectedTestMethods.join();

        if($scope.eventType == "add") {
            trafficService.create(trafficObj).then(function (response) {
                $scope.trafficList.push(response);
                $("#trafficFormModal").modal('hide');
            });
        }
        else {
            trafficService.update(trafficObj.id, trafficObj).then(function(response){
                $scope.trafficList[$scope.traffic.$index] = response;
                $("#trafficFormModal").modal('hide');
            });
        }
    }
});

nttApp.controller('TrafficViewCtrl', function($scope, $routeParams, trafficService, tenantService, networkService, endpointService, $http){
    $scope.cloudId = $routeParams.cloudId;
    $scope.id = $routeParams.id;
    $scope.traffic = {};

    trafficService.get($scope.id).then(function(response){
        $scope.traffic = response;
        $scope.getTenants();
        $scope.getReports();
    });

    $scope.tenants = [];
    $scope.selectedTenant = {};
    $scope.showTenantsLoading = false;
    $scope.getTenants = function () {
        $scope.showTenantsLoading = true;
        tenantService.list($scope.id).then(function (response) {
            $scope.showTenantsLoading = false;
            $scope.tenants = response;
            angular.forEach($scope.tenants, function (tenant, i) {
                if(tenant.is_selected){
                    $scope.selectedTenant = tenant;
                }
            });
            $scope.getNetworks($scope.selectedTenant.id);
        });
    };
    
    $scope.showTenantsDiscovering = false;
    $scope.discoverTenants = function () {
        $scope.showTenantsDiscovering = true;
        tenantService.discover({"cloud_id": $scope.cloudId, "traffic_id":$scope.id}).then(function (response) {
            $scope.showTenantsDiscovering = false;
            $scope.tenants = response;
        });
    };


    $scope.networks = [];
    $scope.showNetworkDiscovering = false;
    $scope.discoverNetworks = function ($index) {
        $scope.showNetworkDiscovering = true;
        $scope.selectedTenant = $scope.tenants[$index];
        networkService.discover($scope.selectedTenant.id).then(function (response) {
            $scope.networks = response;
            $scope.showNetworkDiscovering = false;
        });
    };

    $scope.getNetworks = function (tenantId) {
        if(tenantId != undefined) {
            networkService.list(tenantId).then(function (response) {
                $scope.networks = response;
                $scope.getEndpoints();
            });
        }
    };

    
    $scope.enabledEndpointActionBtn = false;
    $scope.$watch('networks', function(newValues, oldValue, scope){
        var flag = false;
        angular.forEach(newValues, function(network, i){
            if(network.is_selected){
                flag = true
            }
        });
        $scope.enabledEndpointActionBtn = flag;
    }, true);


    $scope.endpoints = [];
    $scope.showEndpointLoading = false;
    $scope.discoverEndpoints = function () {
        $scope.showEndpointLoading = true;
        var selectedNetworks = [];
        angular.forEach($scope.networks, function(network, i) {
            if(network.is_selected){
                selectedNetworks.push({
                    "network_id": network.id,
                    "ip_range_start": network.subnets[0].ip_range_start,
                    "ip_range_end": network.subnets[0].ip_range_end,
                });
            }
        });
        endpointService.discover($scope.traffic.id, selectedNetworks).then(function (response) {
            $scope.endpoints = response;
            $scope.showEndpointLoading = false;
        });
    };

    $scope.showEndpointLaunching = false;
    $scope.launchEndpoints = function () {
        $scope.showEndpointLaunching = true;
        var selectedNetworks = [];
        angular.forEach($scope.networks, function(network, i) {
            if(network.is_selected){
                selectedNetworks.push({
                    "network_id": network.id,
                    "endpoint_count": network.endpoint_count
                });
            }
        });
        endpointService.launch($scope.traffic.id, selectedNetworks).then(function (response) {
            $scope.endpoints = response;
            $scope.showEndpointLaunching = false;
        });
    };

    $scope.getEndpoints = function () {
        endpointService.list($scope.traffic.id).then(function (response) {
            $scope.endpoints = response;
        });
    };

    $scope.selectEndpoint = function ($index, id, isSelected) {
        var endpoint = $scope.endpoints[$index];
        endpointService.select(id, isSelected).then(function (response) {
            endpoint = response;
        });
    };

    $scope.selectedEndpointsCount = 0;
    $scope.$watch('endpoints', function(newValues, oldValue, scope){
        var count = 0;
        angular.forEach(newValues, function(endpoint, i){
            if(endpoint.is_selected){
                count++;
            }
        });
        $scope.selectedEndpointsCount = count;
    }, true);


    $scope.reports = [];
    $scope.getReports = function () {
        trafficService.reports($scope.traffic.id).then(function (response) {
            $scope.reports = response;
        });
    };
    
    $scope.report = {};
    $scope.trafficTestDuration = "1";
    $scope.trafficTestRunning = false;
    $scope.runTrafficTest = function () {
        $scope.report = {};
        $scope.trafficTestRunning = true;
        trafficService.runTrafficTest($scope.traffic.id, $scope.trafficTestDuration).then(function (response) {
            $scope.report = response;
            $scope.trafficTestRunning = false;
            $scope.reports.push($scope.report);
            $('#trafficTestFormModal').modal('hide');
            $('#viewReportModal').modal('show');
        });
    };

    $scope.showLoadingReport = false;
    $scope.viewReport = function (testRunId) {
        $scope.report = {};
        $scope.showLoadingReport = true;
        trafficService.report(testRunId).then(function (response) {
            $scope.report = response;
            $scope.showLoadingReport = false;
        });
    };
    
    $scope.downloadReport = function (testRunId, trafficName) {
        var url = '/api/traffic/report/download/' + testRunId + '/';
        $http.post(url, {}, {responseType: 'arraybuffer'}).then(function (response) {
            var headers = response.headers();
            var blob = new Blob([response.data],{type:headers['content-type']});
            var link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = trafficName+"_"+testRunId+".pdf";
            link.click();
        });
    };


    $scope.deleteReport = function ($index, testRunId) {
        if(confirm("Are you sure want to delete?")) {
            trafficService.deleteReport(testRunId).then(function (response) {
                $scope.reports.splice($index, 1);
            });
        }
    };


    $scope.emailReport = function (testRunId) {
        trafficService.emailReport(testRunId).then(function (response) {
            console.log(response)
        });
    }
});
