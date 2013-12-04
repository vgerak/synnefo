# Copyright 2013 GRNET S.A. All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
#   1. Redistributions of source code must retain the above
#      copyright notice, this list of conditions and the following
#      disclaimer.
#
#   2. Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY GRNET S.A. ``AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL GRNET S.A OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be
# interpreted as representing official policies, either expressed
# or implied, of GRNET S.A.

"""
Utility functions for Cyclades Tests
Cyclades require a lot helper functions and `common'
had grown too much.

"""

import time
import IPy
import base64
import socket
import random
import paramiko
import tempfile
import subprocess

from kamaki.clients import ClientError

from synnefo_tools.burnin.common import BurninTests, MB, GB


# Too many public methods. pylint: disable-msg=R0904
class CycladesTests(BurninTests):
    """Extends the BurninTests class for Cyclades"""
    def _try_until_timeout_expires(self, opmsg, check_fun):
        """Try to perform an action until timeout expires"""
        assert callable(check_fun), "Not a function"

        action_timeout = self.action_timeout
        action_warning = self.action_warning
        if action_warning > action_timeout:
            action_warning = action_timeout

        start_time = int(time.time())
        end_time = start_time + action_warning
        while end_time > time.time():
            try:
                ret_value = check_fun()
                self.info("Operation `%s' finished in %s seconds",
                          opmsg, int(time.time()) - start_time)
                return ret_value
            except Retry:
                time.sleep(self.query_interval)
        self.warning("Operation `%s' is taking too long after %s seconds",
                     opmsg, int(time.time()) - start_time)

        end_time = start_time + action_timeout
        while end_time > time.time():
            try:
                ret_value = check_fun()
                self.info("Operation `%s' finished in %s seconds",
                          opmsg, int(time.time()) - start_time)
                return ret_value
            except Retry:
                time.sleep(self.query_interval)
        self.error("Operation `%s' timed out after %s seconds",
                   opmsg, int(time.time()) - start_time)
        self.fail("time out")

    def _get_list_of_servers(self, detail=False):
        """Get (detailed) list of servers"""
        if detail:
            self.info("Getting detailed list of servers")
        else:
            self.info("Getting simple list of servers")
        return self.clients.cyclades.list_servers(detail=detail)

    def _get_list_of_networks(self, detail=False):
        """Get (detailed) list of networks"""
        if detail:
            self.info("Getting detailed list of networks")
        else:
            self.info("Getting simple list of networks")
        return self.clients.network.list_networks(detail=detail)

    def _get_server_details(self, server, quiet=False):
        """Get details for a server"""
        if not quiet:
            self.info("Getting details for server %s with id %s",
                      server['name'], server['id'])
        return self.clients.cyclades.get_server_details(server['id'])

    def _create_server(self, image, flavor, personality=None, network=False):
        """Create a new server"""
        if network:
            fip = self._create_floating_ip()
            port = self._create_port(fip['floating_network_id'],
                                     floating_ip=fip)
            networks = [{'port': port['id']}]
        else:
            networks = None

        servername = "%s for %s" % (self.run_id, image['name'])
        self.info("Creating a server with name %s", servername)
        self.info("Using image %s with id %s", image['name'], image['id'])
        self.info("Using flavor %s with id %s", flavor['name'], flavor['id'])
        server = self.clients.cyclades.create_server(
            servername, flavor['id'], image['id'],
            personality=personality, networks=networks)

        self.info("Server id: %s", server['id'])
        self.info("Server password: %s", server['adminPass'])

        self.assertEqual(server['name'], servername)
        self.assertEqual(server['flavor']['id'], flavor['id'])
        self.assertEqual(server['image']['id'], image['id'])
        self.assertEqual(server['status'], "BUILD")

        # Verify quotas
        self._check_quotas(disk=+int(flavor['disk'])*GB,
                           vm=+1,
                           ram=+int(flavor['ram'])*MB,
                           cpu=+int(flavor['vcpus']))

        return server

    def _delete_servers(self, servers, error=False):
        """Deleting a number of servers in parallel"""
        # Disconnect floating IPs
        for srv in servers:
            self.info("Disconnecting all floating IPs from server with id %s",
                      srv['id'])
            self._disconnect_from_network(srv)

        # Delete servers
        for srv in servers:
            self.info("Sending the delete request for server with id %s",
                      srv['id'])
            self.clients.cyclades.delete_server(srv['id'])

        if error:
            curr_states = ["ACTIVE", "ERROR", "STOPPED", "BUILD"]
        else:
            curr_states = ["ACTIVE"]
        for srv in servers:
            self._insist_on_server_transition(srv, curr_states, "DELETED")

        # Servers no longer in server list
        new_servers = [s['id'] for s in self._get_list_of_servers()]
        for srv in servers:
            self.info("Verifying that server with id %s is no longer in "
                      "server list", srv['id'])
            self.assertNotIn(srv['id'], new_servers)

        # Verify quotas
        flavors = \
            [self.clients.compute.get_flavor_details(srv['flavor']['id'])
             for srv in servers]
        self._verify_quotas_deleted(flavors)

    def _verify_quotas_deleted(self, flavors):
        """Verify quotas for a number of deleted servers"""
        used_disk = 0
        used_vm = 0
        used_ram = 0
        used_cpu = 0
        for flavor in flavors:
            used_disk += int(flavor['disk']) * GB
            used_vm += 1
            used_ram += int(flavor['ram']) * MB
            used_cpu += int(flavor['vcpus'])
        self._check_quotas(disk=-used_disk,
                           vm=-used_vm,
                           ram=-used_ram,
                           cpu=-used_cpu)

    def _get_connection_username(self, server):
        """Determine the username to use to connect to the server"""
        users = server['metadata'].get("users", None)
        ret_user = None
        if users is not None:
            user_list = users.split()
            if "root" in user_list:
                ret_user = "root"
            else:
                ret_user = random.choice(user_list)
        else:
            # Return the login name for connections based on the server OS
            self.info("Could not find `users' metadata in server. Let's guess")
            os_value = server['metadata'].get("os")
            if os_value in ("Ubuntu", "Kubuntu", "Fedora"):
                ret_user = "user"
            elif os_value in ("windows", "windows_alpha1"):
                ret_user = "Administrator"
            else:
                ret_user = "root"

        self.assertIsNotNone(ret_user)
        self.info("User's login name: %s", ret_user)
        return ret_user

    def _insist_on_server_transition(self, server, curr_statuses, new_status):
        """Insist on server transiting from curr_statuses to new_status"""
        def check_fun():
            """Check server status"""
            srv = self._get_server_details(server, quiet=True)
            if srv['status'] in curr_statuses:
                raise Retry()
            elif srv['status'] == new_status:
                return
            else:
                msg = "Server \"%s\" with id %s went to unexpected status %s"
                self.error(msg, server['name'], server['id'], srv['status'])
                self.fail(msg % (server['name'], server['id'], srv['status']))
        opmsg = "Waiting for server \"%s\" with id %s to become %s"
        self.info(opmsg, server['name'], server['id'], new_status)
        opmsg = opmsg % (server['name'], server['id'], new_status)
        self._try_until_timeout_expires(opmsg, check_fun)

    def _insist_on_network_transition(self, network,
                                      curr_statuses, new_status):
        """Insist on network transiting from curr_statuses to new_status"""
        def check_fun():
            """Check network status"""
            ntw = self.clients.network.get_network_details(network['id'])
            if ntw['status'] in curr_statuses:
                raise Retry()
            elif ntw['status'] == new_status:
                return
            else:
                msg = "Network %s with id %s went to unexpected status %s"
                self.error(msg, network['name'], network['id'], ntw['status'])
                self.fail(msg %
                          (network['name'], network['id'], ntw['status']))
        opmsg = "Waiting for network \"%s\" with id %s to become %s"
        self.info(opmsg, network['name'], network['id'], new_status)
        opmsg = opmsg % (network['name'], network['id'], new_status)
        self._try_until_timeout_expires(opmsg, check_fun)

    def _insist_on_tcp_connection(self, family, host, port):
        """Insist on tcp connection"""
        def check_fun():
            """Get a connected socket from the specified family to host:port"""
            sock = None
            for res in socket.getaddrinfo(host, port, family,
                                          socket.SOCK_STREAM, 0,
                                          socket.AI_PASSIVE):
                fam, socktype, proto, _, saddr = res
                try:
                    sock = socket.socket(fam, socktype, proto)
                except socket.error:
                    sock = None
                    continue
                try:
                    sock.connect(saddr)
                except socket.error:
                    sock.close()
                    sock = None
                    continue
            if sock is None:
                raise Retry
            return sock
        familystr = {socket.AF_INET: "IPv4", socket.AF_INET6: "IPv6",
                     socket.AF_UNSPEC: "Unspecified-IPv4/6"}
        opmsg = "Connecting over %s to %s:%s"
        self.info(opmsg, familystr.get(family, "Unknown"), host, port)
        opmsg = opmsg % (familystr.get(family, "Unknown"), host, port)
        return self._try_until_timeout_expires(opmsg, check_fun)

    def _get_ips(self, server, version=4, network=None):
        """Get the IPs of a server from the detailed server info

        If network not given then get the public IPs. Else the IPs
        attached to that network

        """
        assert version in (4, 6)

        nics = server['attachments']
        addrs = []
        for nic in nics:
            net_id = nic['network_id']
            if network is None:
                if self.clients.network.get_network_details(net_id)['public']:
                    if nic['ipv' + str(version)]:
                        addrs.append(nic['ipv' + str(version)])
            else:
                if net_id == network['id']:
                    if nic['ipv' + str(version)]:
                        addrs.append(nic['ipv' + str(version)])

        self.assertGreater(len(addrs), 0,
                           "Can not get IPs from server attachments")

        for addr in addrs:
            self.assertEquals(IPy.IP(addr).version(), version)

        if network is None:
            msg = "Server's public IPv%s is %s"
            for addr in addrs:
                self.info(msg, version, addr)
        else:
            msg = "Server's IPv%s attached to network \"%s\" is %s"
            for addr in addrs:
                self.info(msg, version, network['id'], addr)
        return addrs

    def _insist_on_ping(self, ip_addr, version=4):
        """Test server responds to a single IPv4 of IPv6 ping"""
        def check_fun():
            """Ping to server"""
            cmd = ("ping%s -c 3 -w 20 %s" %
                   ("6" if version == 6 else "", ip_addr))
            ping = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            ping.communicate()
            ret = ping.wait()
            if ret != 0:
                raise Retry
        assert version in (4, 6)
        opmsg = "Sent IPv%s ping requests to %s"
        self.info(opmsg, version, ip_addr)
        opmsg = opmsg % (version, ip_addr)
        self._try_until_timeout_expires(opmsg, check_fun)

    def _image_is(self, image, osfamily):
        """Return true if the image is of `osfamily'"""
        d_image = self.clients.cyclades.get_image_details(image['id'])
        return d_image['metadata']['osfamily'].lower().find(osfamily) >= 0

    def _ssh_execute(self, hostip, username, password, command):
        """Execute a command via ssh"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostip, username=username, password=password)
        except socket.error as err:
            self.fail(err)
        try:
            _, stdout, _ = ssh.exec_command(command)
        except paramiko.SSHException as err:
            self.fail(err)
        status = stdout.channel.recv_exit_status()
        output = stdout.readlines()
        ssh.close()
        return output, status

    def _insist_get_hostname_over_ssh(self, hostip, username, password):
        """Connect to server using ssh and get it's hostname"""
        def check_fun():
            """Get hostname"""
            try:
                lines, status = self._ssh_execute(
                    hostip, username, password, "hostname")
                self.assertEqual(status, 0)
                self.assertEqual(len(lines), 1)
                # Remove new line
                return lines[0].strip('\n')
            except AssertionError:
                raise Retry()
        opmsg = "Connecting to server using ssh and get it's hostname"
        self.info(opmsg)
        hostname = self._try_until_timeout_expires(opmsg, check_fun)
        self.info("Server's hostname is %s", hostname)
        return hostname

    # Too many arguments. pylint: disable-msg=R0913
    def _check_file_through_ssh(self, hostip, username, password,
                                remotepath, content):
        """Fetch file from server and compare contents"""
        self.info("Fetching file %s from remote server", remotepath)
        transport = paramiko.Transport((hostip, 22))
        transport.connect(username=username, password=password)
        with tempfile.NamedTemporaryFile() as ftmp:
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(remotepath, ftmp.name)
            sftp.close()
            transport.close()
            self.info("Comparing file contents")
            remote_content = base64.b64encode(ftmp.read())
            self.assertEqual(content, remote_content)

    # ----------------------------------
    # Networks
    def _create_network(self, cidr="10.0.1.0/28", dhcp=True):
        """Create a new private network"""
        name = self.run_id
        network = self.clients.network.create_network(
            "MAC_FILTERED", name=name, shared=False)
        self.info("Network with id %s created", network['id'])
        subnet = self.clients.network.create_subnet(
            network['id'], cidr=cidr, enable_dhcp=dhcp)
        self.info("Subnet with id %s created", subnet['id'])

        # Verify quotas
        self._check_quotas(network=+1)

        #Test if the right name is assigned
        self.assertEqual(network['name'], name)

        return network

    def _delete_networks(self, networks, error=False):
        """Delete a network"""
        for net in networks:
            self.info("Deleting network with id %s", net['id'])
            self.clients.network.delete_network(net['id'])

        if error:
            curr_states = ["ACTIVE", "SNF:DRAINED", "ERROR"]
        else:
            curr_states = ["ACTIVE", "SNF:DRAINED"]
        for net in networks:
            self._insist_on_network_transition(net, curr_states, "DELETED")

        # Networks no longer in network list
        new_networks = [n['id'] for n in self._get_list_of_networks()]
        for net in networks:
            self.info("Verifying that network with id %s is no longer in "
                      "network list", net['id'])
            self.assertNotIn(net['id'], new_networks)

        # Verify quotas
        self._check_quotas(network=-len(networks))

    def _get_public_network(self, networks=None):
        """Get the public network"""
        if networks is None:
            networks = self._get_list_of_networks(detail=True)
        self.info("Getting the public network")
        for net in networks:
            if net['SNF:floating_ip_pool'] and net['public']:
                return net
        self.fail("Could not find a public network to use")

    def _create_floating_ip(self):
        """Create a new floating ip"""
        pub_net = self._get_public_network()
        self.info("Creating a new floating ip for network with id %s",
                  pub_net['id'])
        fip = self.clients.network.create_floatingip(pub_net['id'])
        # Verify that floating ip has been created
        fips = self.clients.network.list_floatingips()
        fips = [f['id'] for f in fips]
        self.assertIn(fip['id'], fips)
        # Verify quotas
        self._check_quotas(ip=+1)
        # Check that IP is IPv4
        self.assertEquals(IPy.IP(fip['floating_ip_address']).version(), 4)

        self.info("Floating IP %s with id %s created",
                  fip['floating_ip_address'], fip['id'])
        return fip

    def _create_port(self, network_id, device_id=None, floating_ip=None):
        """Create a new port attached to the a specific network"""
        self.info("Creating a new port to network with id %s", network_id)
        if floating_ip is not None:
            fixed_ips = [{'ip_address': floating_ip['floating_ip_address']}]
        else:
            fixed_ips = None
        port = self.clients.network.create_port(network_id,
                                                device_id=device_id,
                                                fixed_ips=fixed_ips)
        # Verify that port created
        ports = self.clients.network.list_ports()
        ports = [p['id'] for p in ports]
        self.assertIn(port['id'], ports)
        # Insist on creation
        if device_id is None:
            self._insist_on_port_transition(port, ["BUILD"], "DOWN")
        else:
            self._insist_on_port_transition(port, ["BUILD", "DOWN"], "ACTIVE")

        self.info("Port with id %s created", port['id'])
        return port

    def _insist_on_port_transition(self, port, curr_statuses, new_status):
        """Insist on port transiting from curr_statuses to new_status"""
        def check_fun():
            """Check port status"""
            portd = self.clients.network.get_port_details(port['id'])
            if portd['status'] in curr_statuses:
                raise Retry()
            elif portd['status'] == new_status:
                return
            else:
                msg = "Port %s went to unexpected status %s"
                self.fail(msg % (portd['id'], portd['status']))
        opmsg = "Waiting for port %s to become %s"
        self.info(opmsg, port['id'], new_status)
        opmsg = opmsg % (port['id'], new_status)
        self._try_until_timeout_expires(opmsg, check_fun)

    def _insist_on_port_deletion(self, portid):
        """Insist on port deletion"""
        def check_fun():
            """Check port details"""
            try:
                self.clients.network.get_port_details(portid)
            except ClientError as err:
                if err.status != 404:
                    raise
            else:
                raise Retry()
        opmsg = "Waiting for port %s to be deleted"
        self.info(opmsg, portid)
        opmsg = opmsg % portid
        self._try_until_timeout_expires(opmsg, check_fun)

    def _disconnect_from_network(self, server, network=None):
        """Disconnnect server from network"""
        if network is None:
            # Disconnect from public network
            network = self._get_public_network()

        lports = self.clients.network.list_ports()
        ports = []
        for port in lports:
            dport = self.clients.network.get_port_details(port['id'])
            if str(dport['network_id']) == str(network['id']) \
                    and str(dport['device_id']) == str(server['id']):
                ports.append(dport)

        # Find floating IPs attached to these ports
        ports_id = [p['id'] for p in ports]
        fips = [f for f in self.clients.network.list_floatingips()
                if str(f['port_id']) in ports_id]

        # First destroy the ports
        for port in ports:
            self.info("Destroying port with id %s", port['id'])
            self.clients.network.delete_port(port['id'])
            self._insist_on_port_deletion(port['id'])

        # Then delete the floating IPs
        for fip in fips:
            self.info("Destroying floating IP %s with id %s",
                      fip['floating_ip_address'], fip['id'])
            self.clients.network.delete_floatingip(fip['id'])

        # Check that floating IPs have been deleted
        list_ips = [f['id'] for f in self.clients.network.list_floatingips()]
        for fip in fips:
            self.assertNotIn(fip['id'], list_ips)
        # Verify quotas
        self._check_quotas(ip=-len(fips))


class Retry(Exception):
    """Retry the action

    This is used by _try_unit_timeout_expires method.

    """