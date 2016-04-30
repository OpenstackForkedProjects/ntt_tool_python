var nttApp = angular.module('nttApp', [
    'ngRoute',
    'ngCookies',
    'http-auth-interceptor',
    'ui.bootstrap',
    'checklist-model',
]);

nttApp.config(['$httpProvider', '$interpolateProvider', function($httpProvider, $interpolateProvider, $window){
    /* For compatibility with django template engine */
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');

    /* Adding XMLHttpRequest to angular AJAX request */
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded';

    /* CSRF Protection */
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);

nttApp.config(['$routeProvider', function($routeProvider){
    $routeProvider.when('/', {
        controller: 'IndexCtrl',
        templateUrl: '/static/partials/index.html',
    });

    $routeProvider.when('/dashboard/', {
        controller: 'DashboardCtrl',
        templateUrl: '/static/partials/dashboard.html',
    });

    /**
     * URL patterns for cloud
     */
    $routeProvider.when('/cloud/', {
        controller: 'CloudListCtrl',
        templateUrl: '/static/partials/cloud/cloud_list.html',
    });

    $routeProvider.when('/cloud/add/', {
        controller: 'CloudCtrl',
        templateUrl: '/static/partials/cloud/cloud_form.html',
    });

    $routeProvider.when('/cloud/edit/:id/', {
        controller: 'CloudCtrl',
        templateUrl: '/static/partials/cloud/cloud_form.html',
    });

    $routeProvider.when('/cloud/view/:id/', {
        controller: 'CloudCtrl',
        templateUrl: '/static/partials/cloud/cloud_view.html',
    });

    /**
     * URL patterns for cloud traffic
     */

    $routeProvider.when('/cloud/:cloudId/traffic/:id/', {
        controller: 'TrafficViewCtrl',
        templateUrl: '/static/partials/cloud/traffic/traffic_view.html'
    });
}]);









