'use strict';

nttApp.service('dataService', ['$http', '$q', function ($http, $q) {
    this.get = function (url) {
        var deferred = $q.defer();
        var request = $http.get(url);
        request.success(function (data, status, headers, config) {
            deferred.resolve(data);
        });
        request.error(function (data, status) {
            deferred.reject(data);
        });
        return deferred.promise;
    };

    this.post = function (url, params) {
        var deferred = $q.defer();
        var request = $http({
            method: "post",
            url: url,
            data: $.param(params)
        });
        request.success(function (data, status, headers, config) {
            deferred.resolve(data)
        });
        request.error(function (response) {
            deferred.reject(response);
        });
        return deferred.promise;
    };

    this.getJSON = function(url, params) {
        var deferred = $q.defer();
        var request = $http({
            method: "get",
            url: url,
            data: $.param({"json": angular.toJson(params)}),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }
        });
        request.success(function (data, status, headers, config) {
            deferred.resolve(data)
        });
        request.error(function (response) {
            deferred.reject(response);
        });
        return deferred.promise;
    };
    

    this.postJSON = function(url, params) {
        var deferred = $q.defer();
        var request = $http({
            method: "post",
            url: url,
            data: $.param({"json": angular.toJson(params)}),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }
        });
        request.success(function (data, status, headers, config) {
            deferred.resolve(data)
        });
        request.error(function (response) {
            deferred.reject(response);
        });
        return deferred.promise;
    };

    this.update = function (url, params) {
        var deferred = $q.defer();
        var request = $http({
            method: "put",
            url: url,
            data: "data="+$.param(params)
        });
        request.success(function (data, status, headers, config) {
            deferred.resolve(data)
        });
        request.error(function (response) {
            deferred.reject(response);
        });
        return deferred.promise;
    };

    this.delete = function (url) {
        var deferred = $q.defer();
        var request = $http({
            method: "delete",
            url: url,
        });
        request.success(function (data, status, headers, config) {
            deferred.resolve(data)
        });
        request.error(function (response) {
            deferred.reject(response);
        });
        return deferred.promise;
    };

    this.put = function (url, params) {
        var deferred = $q.defer();
        var request = $http.put(url, params);
        request.success(function (data, status, headers, config) {
            deferred.resolve(data)
        });
        request.error(function (response) {
            deferred.reject(response);
        });
        return deferred.promise;
    }
}]);