define(function() {
    var models = {};
    var collections = {};

    models.Release = Backbone.Model.extend({
        urlRoot: '/api/releases'
    });

    models.Releases = Backbone.Collection.extend({
        model: models.Release,
        url: '/api/releases'
    });

    models.Cluster = Backbone.Model.extend({
        urlRoot: '/api/clusters',
        validate: function(attrs) {
            var errors = {};
            if (!attrs.name || attrs.name.length == 0) {
                errors.name = 'Cluster name cannot be empty';
            } else if (attrs.name.length > 100) {
                errors.name = 'Cluster name is too long';
            }
            if (!attrs.release) {
                errors.release = 'Please choose OpenStack release';
            }
            if (attrs.mode == 'ha') {
                if (_.isNaN(attrs.redundancy)) {
                    errors.redundancy = 'Please enter integer number';
                } else if (attrs.redundancy < 2 || attrs.redundancy > 9) {
                    errors.redundancy = 'Please enter number between 2 and 9';
                }
            }
            return _.isEmpty(errors) ? null : errors;
        },
        locked: function() {
            return this.get('task') && !this.get('task').get('ready');
        },
        availableRoles: function() {
            if (this.get('type') == 'storage') {
                return ['controller', 'storage']
            } else if (this.get('type') == 'compute') {
                return ['controller', 'compute']
            } else {
                return ['controller', 'compute', 'storage']
            }
        },
        parse: function(response) {
            response.nodes = new models.Nodes(response.nodes);
            response.nodes.cluster = this;
            response.release = new models.Release(response.release);
            response.task = response.task ? new models.Task(response.task) : null;
            return response;
        }
    });

    models.Clusters = Backbone.Collection.extend({
        model: models.Cluster,
        url: '/api/clusters',
        toJSON: function(options) {
            return this.pluck('id');
        }
    });

    models.Node = Backbone.Model.extend({
        urlRoot: '/api/nodes',
        fullProductName: function() {
            return (this.get('manufacturer') ? this.get('manufacturer') + ' ' + this.get('platform_name') : this.get('platform_name')) || 'Unknown Platform';
        },
        resource: function(resourceName) {
            return this.get('info')[resourceName];
        }
    });

    models.Nodes = Backbone.Collection.extend({
        model: models.Node,
        url: '/api/nodes',
        toJSON: function(options) {
            return this.pluck('id');
        },
        resources: function(resourceName) {
            var resources = this.map(function(node) {return node.resource(resourceName)});
            return _.reduce(resources, function(sum, n) {return sum + n}, 0);
        }
    });

    return models;
});
