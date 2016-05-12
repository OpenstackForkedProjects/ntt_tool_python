nttApp.run(function($rootScope, $window, $location, ngToast){
    $rootScope.isLoggedin = false;

    if($window.localStorage.isLoggedin){
        $rootScope.isLoggedin = true;
        $rootScope.user = JSON.parse($window.localStorage.getItem("user"));
    }
    $rootScope.$on('event:auth-loginConfirmed', function(event, data){
        $('#modal').modal('hide');
        $rootScope.isLoggedin = true;
        $rootScope.user = data.user;
        $window.localStorage['isLoggedin'] = true;
        $window.localStorage['token'] = data.token;
        $window.localStorage['user'] = angular.toJson(data.user);
        ngToast.dismiss();
        ngToast.create("Welcome <b>" + data.user.first_name + "&nbsp;" + data.user.last_name + "</b>");
        $location.path("cloud");
    });

    $rootScope.$on('event:auth-loginRequired', function (event) {
        $rootScope.$broadcast('event:auth-logout');
        ngToast.create({
            className: 'warning',
            content: 'Login required.',
        });
    });

    $rootScope.$on('event:auth-logout', function (event) {
        $rootScope.isLoggedin = false;
        $rootScope.user = {};
        $window.localStorage.removeItem('isLoggedin')
        $window.localStorage.removeItem('token');
        $window.localStorage.removeItem('user');
        ngToast.dismiss();
        ngToast.create("Logged out successfully.");
        $location.path("/");
    });

    $rootScope.logout = function(){
        $rootScope.$broadcast('event:auth-logout');
    }
});

nttApp.controller('LoginCtrl', function($scope, $http, authService, ngToast){
    $scope.credentials = {};
    $scope.login = function(){
        $http({
            method: 'post',
            url: '/api/auth-token/',
            data: $.param($scope.credentials)
        })
        .then(function successCallback(response) {
            authService.loginConfirmed(response.data);
        }, function errorCallback(response) {
            if(Object.keys(response.data)[0] == "non_field_errors"){
                ngToast.create({
                    className: "danger",
                    content: response.data.non_field_errors,
                });
            }
            else {
                ngToast.create({
                    className: 'danger',
                    content: 'Please enter <b>Username</b> and <b>Password</b>',
                });
            }
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


nttApp.config(['ngToastProvider', function(ngToast) {
    ngToast.configure({
        animation: 'slide',
        combineDuplications: true
    });
}]);