nttApp.run(function($rootScope, $window, $location){
    $rootScope.isLoggedin = false;
    if($window.localStorage.isLoggedin){
        $rootScope.isLoggedin = true;
    }

    $rootScope.$on('event:auth-loginConfirmed', function(event, data){
        $('#modal').modal('hide');
        $rootScope.isLoggedin = true;
        $window.localStorage['isLoggedin'] = true;
        $window.localStorage['token'] = data.token;
        $location.path("cloud");
    });

    $rootScope.$on('event:auth-loginRequired', function (event) {
        $rootScope.$broadcast('event:auth-logout');
    });

    $rootScope.$on('event:auth-logout', function (event) {
        $rootScope.isLoggedin = false;
        $window.localStorage.removeItem('isLoggedin')
        $window.localStorage.removeItem('token');
        $location.path("/");
    });

    $rootScope.logout = function(){
        $rootScope.$broadcast('event:auth-logout');
    }
});

nttApp.controller('LoginCtrl', function($scope, $http, authService){
    $scope.credentials = {};
    $scope.login = function(){
        $http({
            method: 'post',
            url: '/api/auth-token/',
            data: $.param($scope.credentials)
        }).success(function(response){
            authService.loginConfirmed(response);
        });
    };
});


nttApp.factory('token-interceptor', function($rootScope, $q, $window, $location){
    return {
        request: function(config){
            config.headers = config.headers || {};
            if ($rootScope.isLoggedin && $window.localStorage.token) {
                config.headers.Authorization = 'JWT '+ $window.localStorage.token;
            }
            return config;
        }
    }
}).config(['$httpProvider', function ($httpProvider) {
    $httpProvider.interceptors.push('token-interceptor');
}]);
