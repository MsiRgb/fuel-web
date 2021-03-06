# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import fake_tasks
from nailgun.test.base import reverse


class TestNetworkModels(BaseIntegrationTest):

    def tearDown(self):
        self._wait_for_threads()
        super(TestNetworkModels, self).tearDown()

    @fake_tasks(godmode=True)
    def test_cluster_locking_after_deployment(self):
        self.env.create(
            nodes_kwargs=[
                {"pending_addition": True},
                {"pending_addition": True},
                {"pending_deletion": True},
            ]
        )
        supertask = self.env.launch_deployment()
        self.env.wait_ready(supertask, 60)

        test_nets = json.loads(self.env.nova_networks_get(
            self.env.clusters[0].id
        ).body)

        resp_nova_net = self.env.nova_networks_put(
            self.env.clusters[0].id,
            test_nets,
            expect_errors=True
        )

        resp_neutron_net = self.env.neutron_networks_put(
            self.env.clusters[0].id,
            test_nets,
            expect_errors=True
        )

        resp_cluster = self.app.put(
            reverse('ClusterAttributesHandler',
                    kwargs={'cluster_id': self.env.clusters[0].id}),
            json.dumps({
                'editable': {
                    "foo": "bar"
                }
            }),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEquals(resp_nova_net.status_code, 403)
        # it's 400 because we used Nova network
        self.assertEquals(resp_neutron_net.status_code, 400)
        self.assertEquals(resp_cluster.status_code, 403)
