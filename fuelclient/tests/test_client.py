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


import os

from shutil import rmtree
from tempfile import mkdtemp

from fuelclient.tests.base import BaseTestCase


class TestHandlers(BaseTestCase):

    def test_env_action(self):
        #check env help
        help_msgs = ["usage: fuel environment [-h]",
                     "[-h] [--env ENV] [-l] [-s]",
                     "optional arguments:", "--help", "--list", "--set",
                     "--delete", "--rel", "--release", "--env-create,",
                     "--create", "--name", "--env-name", "--mode", "--net",
                     "--network-mode", "--nst", "--net-segment-type",
                     "--deployment-mode"]
        self.check_all_in_msg("env --help", help_msgs)
        #no clusters
        self.check_for_rows_in_table("env")

        for action in ("set", "create", "delete"):
            self.check_if_required("env {0}".format(action))

        #list of tuples (<fuel CLI command>, <expected output of a command>)
        expected_stdout = \
            [(
                "env create --name=TestEnv --release=1",
                "Environment 'TestEnv' with id=1, mode=ha_compact and "
                "network-mode=nova_network was created!\n"
            ), (
                "--env-id=1 env set --name=NewEnv",
                "Environment with id=1 was renamed to 'NewEnv'.\n"
            ), (
                "--env-id=1 env set --mode=multinode",
                "Mode of environment with id=1 was set to 'multinode'.\n"
            )]

        for cmd, msg in expected_stdout:
            self.check_for_stdout(cmd, msg)

    def test_node_action(self):
        help_msg = ["fuel node [-h] [--env ENV] [-l]",
                    "[-l] [-s] [--delete] [--default]", "-h", "--help", "-l",
                    "--list", "-s", "--set", "--delete", "--default", "-d",
                    "--download", "-u", "--upload", "--dir", "--node",
                    "--node-id", "-r", "--role", "--net", "--network",
                    "--disk", "--deploy", "--provision"]
        self.check_all_in_msg("node --help", help_msg)

        self.check_for_rows_in_table("node")

        for action in ("set", "remove", "--network", "--disk"):
            self.check_if_required("node {0}".format(action))

        self.load_data_to_nailgun_server()
        self.check_number_of_rows_in_table("node --node 9f:b7,9d:24,ab:aa", 3)

    def test_selected_node_deploy_or_provision(self):
        self.load_data_to_nailgun_server()
        self.run_cli_commands((
            "env create --name=NewEnv --release=1",
            "--env-id=1 node set --node 1 --role=controller"
        ))
        commands = ("--provision", "--deploy")
        for action in commands:
            self.check_if_required("--env-id=1 node {0}".format(action))
        messages = (
            "Started provisioning nodes [1].\n",
            "Started deploying nodes [1].\n"
        )
        for cmd, msg in zip(commands, messages):
            self.check_for_stdout(
                "--env-id=1 node {0} --node=1".format(cmd),
                msg
            )

    def test_for_examples_in_action_help(self):
        actions = (
            "node", "stop", "deployment", "reset", "task", "network",
            "settings", "provisioning", "environment", "deploy-changes",
            "role", "release", "snapshot", "health"
        )
        for action in actions:
            self.check_all_in_msg("{0} -h".format(action), ("Examples",))


class TestFiles(BaseTestCase):

    def setUp(self):
        super(TestFiles, self).setUp()
        self.temp_directory = mkdtemp()

    def tearDown(self):
        rmtree(self.temp_directory)

    def test_file_creation(self):
        self.load_data_to_nailgun_server()
        self.run_cli_commands((
            "env create --name=NewEnv --release=1",
            "--env-id=1 node set --node 1 --role=controller",
            "--env-id=1 node set --node 2,3 --role=compute"
        ))
        for action in ("network", "settings"):
            self.check_if_files_created(
                "--env 1 {0} --download".format(action),
                ("{0}_1.yaml".format(action),)
            )
        deployment_provision_files = {
            "--env 1 deployment --default": (
                "deployment_1",
                "deployment_1/primary-controller_1.yaml",
                "deployment_1/compute_2.yaml",
                "deployment_1/compute_3.yaml"
            ),
            "--env 1 provisioning --default": (
                "provisioning_1",
                "provisioning_1/engine.yaml",
                "provisioning_1/node-1.yaml",
                "provisioning_1/node-2.yaml",
                "provisioning_1/node-3.yaml"
            )
        }
        for command, files in deployment_provision_files.iteritems():
            self.check_if_files_created(command, files)
        node_configs = (
            (
                "node --node 1 --disk --default",
                ("node_1", "node_1/disks.yaml")
            ),
            (
                "node --node 1 --network --default",
                ("node_1", "node_1/interfaces.yaml")
            )
        )
        for command, files in node_configs:
            self.check_if_files_created(command, files)

    def check_if_files_created(self, command, paths):
        command_in_dir = "{0} --dir={1}".format(command, self.temp_directory)
        self.run_cli_command(command_in_dir)
        for path in paths:
            self.assertTrue(os.path.exists(
                os.path.join(self.temp_directory, path)
            ))
