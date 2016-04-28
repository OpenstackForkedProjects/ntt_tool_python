nttApp.service('trafficService', function(dataService){
    this.list = function(cloudId){
        return dataService.get('/api/traffic/?cloud_id=' + cloudId);
    };

    this.get = function(pk) {
        return dataService.get('/api/traffic/' + pk + '/');
    };
    
    this.create = function(params){
        return dataService.post('/api/traffic/', params);
    };

    this.update = function(pk, params){
        return dataService.put('/api/traffic/' + pk + '/', params);
    };

    this.delete = function(pk){
        return dataService.delete('/api/traffic/' + pk + '/');
    };

    this.reports = function (pk) {
        return dataService.get('/api/traffic/reports/' + pk + '/');
    };

    this.report = function (testRunId) {
        return dataService.get('/api/traffic/report/' + testRunId + '/');
    };
    
    this.runTrafficTest = function(pk, testDuration){
        return dataService.get('/api/traffic/' + pk + '/run/test/?duration='+testDuration);
    };
    
    this.emailReport = function (pk) {
        return dataService.get('/api/traffic/' + pk + '/email/report/');
    }
});






