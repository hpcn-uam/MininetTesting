#!/usr/bin/python

""" Script that tests RTT in a mininet deployment with IPSEC tunnels
Usage: ./test_VPN.py [Options]
Available options:
* '-v', '--verbose': provide higher detail for logs
* '-o', '--output': set output path
* '-t', '--time': Duration of test (in minutes)
* '-H', '--n_hosts': set number of hosts
"""

__author__ = "Javier Ramos & David Muelas ({dav.muelas,javier.ramos}@uam.es)"
__version__ = "$2.0$"
__date__ = "$Date: 2017/05/10$"

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.link import TCLink
from mininet.node import Host
from mininet.cli import CLI
from functools import partial
import time
import sys
import getopt

H = 2
TIME=2

class SingleSwitchTopo(Topo):
	"Single switch connected to n hosts."
	def build(self, n=2):
		switch = self.addSwitch('s1')
		switchOut= self.addSwitch('s2')

		
		privateDirs=[( '/var/log', '/tmp/%(name)s/var/log' ),( '/var/run', '/tmp/%(name)s/var/run' ),( '/etc', '/tmp/%(name)s/etc' )]

		for h in range(n):
			host = self.addHost('h%s' % (h + 1),privateDirs=privateDirs) 
			linkopts = dict(bw=20)
			self.addLink(host, switch,**linkopts)
		
		endHost=self.addHost('endHost',privateDirs=privateDirs)
		gateway=self.addHost('gateway',privateDirs=privateDirs)
		linkopts = dict(bw=1000)
		self.addLink(switch, gateway,**linkopts)
		self.addLink(gateway, switchOut,**linkopts)
		self.addLink(endHost, switchOut,**linkopts)



def testConnection(net,output_path,n_minutes,n=2):
	for t in range (n_minutes):
		time.sleep(60)
		for h in range(n):
				hn='h%s' % (h + 1)
                	        host = net.get(hn)
				host.cmd('ping -D -c 1 10.0.0.2 >> %s/%s' % (output_path,hn+'.results'))		


def configureHosts(net,n=2):
	confGwBase='config setup\\nconn %%default\\n\\tikelifetime=60m\\n\\tkeylife=20m\\n\\trekeymargin=3m\\n\\tkeyingtries=1\\n\\tkeyexchange=ikev2\\n\\tauthby=secret\\n\\nconn rw\\n\\tleft=%s\\n\\tleftsubnet=10.0.0.0/8\\n\\tleftfirewall=yes\\n\\tright=%%any\\n\\tauto=add\\n'
	confHost='config setup\\nconn %%default\\n\\tikelifetime=60m\\n\\tkeylife=20m\\n\\trekeymargin=3m\\n\\tkeyingtries=1\\n\\tkeyexchange=ikev2\\n\\tauthby=secret\\nconn host-host\\n\\tleft=%s\\n\\tleftfirewall=yes\\n\\tright=%s\\n\\trightsubnet=10.0.0.0/8\\n\\tauto=add\\n'

	subnetgw1='192.168.1.%s/24' % (n+1)
	ipgw1='192.168.1.%s' % (n+1)
	subnetgw2='10.0.0.1/8'
	pskLine='%s : PSK %s\\n'
	gateway = net.get('gateway')

	for h in range(n):
			hn='h%s' % (h + 1)
                        host = net.get(hn)		
			res=host.cmd('ipsec stop')
	
			subnet='192.168.1.%s/24' % (h + 1)
			ip='192.168.1.%s' % (h + 1)
                        host.setIP(subnet)
                        # Create isec.conf file for each host
			hostConf=confHost % (ip,ipgw1)
			host.cmd('echo -e "%s" > /etc/ipsec.conf' % (hostConf))
			psk=host.cmd('openssl rand -base64 48')
			host.cmd('echo -e "%s" > /etc/ipsec.secrets' % (pskLine % (ip,psk)))
			res=host.cmd('ipsec start')
			print res
			if (h==0):
				gateway.cmd('echo -e "%s" > /etc/ipsec.secrets' % (pskLine % (ip,psk)))

			else:
				gateway.cmd('echo -e "%s" >> /etc/ipsec.secrets' % (pskLine % (ip,psk)))

	

	
	intf = gateway.intf('gateway-eth0')
	intf.setIP(subnetgw1)
	intf = gateway.intf('gateway-eth1')
	intf.setIP(subnetgw2)
	
	endHost = net.get('endHost')
	intf = endHost.intf('endHost-eth0')
	intf.setIP('10.0.0.2/8')
	
	#create ipsec.conf file for gw
	confGw=confGwBase % (ipgw1)
	gateway.cmd('echo -e "%s" > /etc/ipsec.conf' % (confGw))
	gateway.cmd('sysctl -w net.ipv4.ip_forward=1')
	gateway.cmd('iptables -t nat -A POSTROUTING -o gateway-eth1 -j MASQUERADE')
	gateway.cmd('iptables -t nat -A POSTROUTING -o gateway-eth0 -j MASQUERADE')

	gateway.cmd('ipsec stop')

	gateway.cmd('ipsec start')
	time.sleep(2)
	print 'Setting Tunnels'
	for h in range(n):
			hn='h%s' % (h + 1)
			print 'Host:%s' %hn
                        host = net.get(hn)			
			res=host.cmd('ipsec up host-host')
			print res


def simpleTest(output_path,n_minutes,n=1):
	"Create and test a simple network"
	topo =SingleSwitchTopo(n)
	privateDirs = [( '/var/log', '/tmp/%(name)s/var/log' ),( '/var/run', '/tmp/%(name)s/var/run' ),( '/etc', '/tmp/%(name)s/etc' )]

	host = partial( Host, privateDirs=privateDirs)

	net = Mininet(topo,link=TCLink)
	net.start()
	print "Dumping host connections"
	dumpNodeConnections(net.hosts)
	print "Testing network connectivity"
	configureHosts(net,n)

	net.pingAll()
	testConnection(net,output_path,n_minutes,n)
	net.stop()

if __name__ == '__main__':
      
	setLogLevel('error')	
	options, remainder = getopt.getopt(sys.argv[1:], 'vo:H:C:t:', ['verbose','output','n_hosts','time'])
	verbose=False
	udp_op=''
	output_path=''
	H = 2
	S = 1
	for opt, arg in options:

		if opt in ('-v', '--verbose'):
			verbose=True

		if opt in ('-o', '--output'):
			output_path=arg+'/'

	

		if opt in ('-H', '--n_hosts'):

			H = int(arg)

		if opt in ('-t', '--time'):
			TIME=int(arg)

	
	simpleTest(output_path,TIME,n=H)
