#!/usr/bin/python

""" Script that tests BW in a mininet deployment

Usage: ./test_BW_subnets_topo.py [Options]

Available options:

* '-v', '--verbose': provide higher detail for logs
* '-u', '--udp': use UDP as transport protocol
* '-o', '--output': set output path
* '-C', '--n_cores': set number of cores to be used
* '-H', '--n_hosts': set number of hosts

"""

__author__ = "Javier Ramos & David Muelas ({dav.muelas,javier.ramos}@uam.es)"
__version__ = "$2.0$"
__date__ = "$Date: 2017/05/10$"

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
import sys
import time 
import getopt
import os
N_CORES=1
S = 1
H = 2
TIME=300
switch_l = list()
host_l = list()

def constant(f):

	def fset(self, value):
		raise SyntaxError

	def fget(self):
		return f()

	return property(fget, fset)

class SingleSwitchTopo(Topo):


	"Tree of N switches, each one connected to M hosts"
	def build(self):

		switch_l.append(self.addSwitch('s6000',cores=str(0)))
		for i in range(0, S):

			switch_l.append(self.addSwitch('s'+str(i),cores=str(i % N_CORES)))
			
			#Connect each subnet switch to the core switch
			self.addLink(switch_l[-1], switch_l[0])

			#'192.168.%d.0/24'%(i)

			for j in range(0, H/S):

				host_l.append(self.addHost('h'+str(i)+','+str(j),cores=str(i % N_CORES)))
				
				self.addLink(host_l[-1], switch_l[-1])
				

		writeLogMessage('Topo is up')


def writeLogMessage(message,output_f=sys.stdout,label=' -INFO- '):

	output_f.write('['+time.strftime("%Y%m%d-%H:%M:%S")+'] '+label + str(message)+'\n')

arpTable={}
def perfTest(verbose, udp_op, output_path):

	"Create network and run simple performance test"
	topo = SingleSwitchTopo()
	net = Mininet(topo=topo, link=TCLink,   controller=None)

	net.start()

	switch_o_l = list()
	host_o_l = {}

	############################################################################
	# Get all objects, both switches and hosts and set IPs
	############################################################################
	switch_core=net.get('s6000')

	for i in range(0, S/2):
		switch_core.cmd('ovs-ofctl add-flow s6000 idle_timeout=0,priority=2000,ip,nw_dst=10.%d.0.0/16,actions=output:%d'%(i,i+1))
	for i in range(S/2, S):
		switch_core.cmd('ovs-ofctl add-flow s6000 idle_timeout=0,priority=2000,ip,nw_dst=10.%d.0.0/16,actions=output:%d'%(i,i+1))

	servers=[]
	clients=[]
	for i in range(0, S):
		switch_o_l.append(net.get('s'+str(i)))
		switchAux=net.get('s'+str(i))
		switchAux.cmd('ovs-ofctl add-flow s%i idle_timeout=0,priority=2000,ip,nw_dst=10.%d.0.0/16,actions=output:1'%(i,S-i-1))
		for j in range(0, H/S):
			
			haux=net.get('h'+str(i)+','+str(j))
			haux.setIP('10.%d.%d.%d'%(i,(j/254),(j%254)+1),16)
			haux.cmd('route add -net 0.0.0.0/0 h%i,%i-eth0'%(i,j))
			arpTable['10.%d.%d.%d'%(i,(j/254),(j%254)+1)]=haux.MAC()
			switchAux.cmd('ovs-ofctl add-flow s%d idle_timeout=0,priority=2001,dl_dst=%s,actions=output:%d'%(i,haux.MAC(),j+2))
			if(os.path.exists(output_path+ '10.%d.%d.%d'%(i,(j/254),(j%254)+1)+'/')==False):
				os.mkdir(output_path+ '10.%d.%d.%d'%(i,(j/254),(j%254)+1)+'/')
			host_o_l[haux.IP()]=haux

			#Setup servers on IP even hosts			
			if (j+1)%2==0:	
				command = 'iperf -s ' + ' -i 1 -y c' + udp_op +' &> ' + output_path + '10.%d.%d.%d'%(i,(j/254),(j%254)+1)+'/'+ 'server_' +'10.%d.%d.%d'%(i,(j/254),(j%254)+1) + ' &'

				if (verbose):

					writeLogMessage('Server IP: '+str(haux.IP()))
					writeLogMessage(command)

				result = haux.cmd(command)
				servers.append(haux)
				if (verbose):
					print(result)

			else:
				clients.append(haux)

			if (H/S)%2!=0 and j+1==H/S:
				command = 'iperf -s ' + ' -i 1 -y c' + udp_op +' &> ' + output_path +'10.%d.%d.%d'%(i,(j/254),(j%254)+1)+'/'+ '10.%d.%d.%d'%(i,(j/254),(j%254)+1) + ' &'

                                if (verbose):

                                        writeLogMessage('Server IP: '+str(haux.IP()))
                                        writeLogMessage(command)

                                result = haux.cmd(command)
                                servers.append(haux)
                                if (verbose):
                                        print(result)


	writeLogMessage('Testing with '+str(H/2)+' servers')

	############################################################################
	# Measure bandwidth with iperf servers and clients
	############################################################################
	for elem in clients:
		serv=servers.pop(-1)
		
		res=elem.cmd('arp -s %s %s'%(serv.IP(),arpTable[serv.IP()]))
		res=serv.cmd('arp -s %s %s'%(elem.IP(),arpTable[elem.IP()]))

		command = 'iperf -c ' + str(serv.IP()) + ' -i 1 -t '+str(TIME)+' -y c ' + udp_op +' &> ' + output_path + str(elem.IP())+'/'+ 'client_' +str(elem.IP()) + ' &'

		if (verbose):
			writeLogMessage('Client '+str(elem.IP())+' is up and connected with server '+serv.IP())

		result=elem.cmd(command)

		if (verbose):
			print(result)

	time.sleep(TIME+10)
	net.stop()

if __name__ == '__main__':

	setLogLevel('info')	
	options, remainder = getopt.getopt(sys.argv[1:], 'vuo:H:S:C:t:', ['verbose','udp','output','n_hosts','n_subnets','n_cores','time'])
	verbose=False
	udp_op=''
	output_path=''
	H = 2
	S = 1



	for opt, arg in options:

		if opt in ('-v', '--verbose'):
			verbose=True

		if opt in ('-u', '--udp'):
			udp_op=' -u '

		if opt in ('-o', '--output'):
			output_path=arg+'/'

		if opt in ('-C', '--n_cores'):
			N_CORES=int(arg)

		if opt in ('-H', '--n_hosts'):

			aux = int(arg)

			if (aux % 2 == 1):
				aux = aux + 1
				writeLogMessage('Number of hosts must be even. Automatically set to ' + str(int(aux)),sys.stderr,' -ERROR- ')

			H = aux

		if opt in ('-S', '--n_subnets'):
			S=int(arg)

		if opt in ('-t', '--time'):
			TIME=int(arg)

	if H%S!=0:
		writeLogMessage('The number of hosts (H) must be a multiple of the subnet number (S)',sys.stdout,' -ERROR- ')
		exit(0)		
	writeLogMessage('Starting test',sys.stdout)	
	perfTest(verbose, udp_op, output_path)

