nttApp.service('tenantService', function (dataService) {
    this.discover = function(params){
        return dataService.get('/api/tenant/discover/?'+$.param(params));
    };

    this.list = function(trafficId){
        return dataService.get('/api/tenant/?traffic_id='+trafficId);
    };

    this.save = function(params){
        return dataService.post('/api/tenant/', params);
    };
});


nttApp.service('networkService', function (dataService) {
    this.discover = function (tenantId) {
        return dataService.get('/api/network/discover/?tenant_id='+tenantId);
    };

    this.list = function (tenantId) {
        return dataService.get('/api/network/?tenant_id='+tenantId);
    };
});


nttApp.service('endpointService', function (dataService) {
    this.list = function (trafficId) {
        return dataService.get('/api/endpoint/?traffic_id=' + trafficId);
    };

    this.discover = function (trafficId, params) {
        return dataService.postJSON('/api/endpoint/discover/' + trafficId + '/', params);
    };

    this.launch = function (trafficId, params) {
        return dataService.postJSON('/api/endpoint/launch/' + trafficId + '/', params);
    };
    
    this.select = function (pk, isSelected) {
        return dataService.get('/api/endpoint/' + pk + '/select/?is_selected=' + JSON.stringify(isSelected));
    };
});
