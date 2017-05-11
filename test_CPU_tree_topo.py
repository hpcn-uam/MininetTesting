#!/usr/bin/python

""" Script that introduce activity in a mininet deployment by using ping

Usage: ./test_CPU_tree_topo.py [Options]

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
from  mininet.node import OVSBridge
from  mininet.node import UserSwitch
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

		for i in range(0, S):

			switch_l.append(self.addSwitch('s'+str(i),cores=str(i % (N_CORES-6)+6)))

			if (i > 0):
				self.addLink(switch_l[i], switch_l[i-1])

		for j in range(0, H):

			host_l.append(self.addHost('h'+str(j),cores=str(j % (N_CORES-6)+6)))
			if (j % 2 == 0):
				self.addLink(host_l[j], switch_l[0])
			else:
				self.addLink(host_l[j], switch_l[S-1])

		writeLogMessage('Topo is up')


def writeLogMessage(message,output_f=sys.stdout,label=' -INFO- '):

	output_f.write('['+time.strftime("%Y%m%d-%H:%M:%S")+'] '+label + str(message)+'\n')

def perfTest(verbose, udp_op, output_path,act=False):

	"Create network and run simple performance test"
	topo = SingleSwitchTopo()
	net = Mininet(topo=topo,switch=OVSBridge,controller=None,host=CPULimitedHost)

	net.start()

	switch_o_l = list()
	host_o_l = list()


	############################################################################
	# Get all objects, both switches and hosts
	############################################################################

	for i in range(0, S):
		switch_o_l.append(net.get('s'+str(i)))

	for j in range(0, H):
		host_o_l.append(net.get('h'+str(j)))

	############################################################################
	# Measure RTT with ping
	############################################################################

	if act:
			k=H/2
			
			if(os.path.exists(output_path+ str(S)+'/')==False):
				os.mkdir(output_path+ str(S)+'/')

			l=k
			for n in range(H-1,l-1,-1):
				if(os.path.exists(output_path+ str(S)+'/'+str(H)+'/')==False):

					os.mkdir(output_path+ str(S)+'/'+str(H)+'/')
				if str(host_o_l[n].IP())==str(host_o_l[n % (l)].IP()):
					exit(-1)

				command = 'taskset -c '+str(n % (N_CORES-6)+6)+' ping -i 0.01 '+str(host_o_l[n % (l)].IP())+' >' +output_path+ str(S)+'/'+str(H)+'/'+str(n)+'.data' + '&'
				print "Command "+command
				
				if (verbose):
					writeLogMessage('Client IP: '+str(host_o_l[n].IP())+' --- Server IP: '+str(host_o_l[n % (l)].IP()))
					writeLogMessage(command)

				result=host_o_l[n].cmd(command)

				if (verbose):
					print(result)

				writeLogMessage('Client '+str(host_o_l[n].IP())+' is up')

	time.sleep(15)
	os.system('killall -9 ping')
	
	for i in range(0, S):
		command = 'ovs-ofctl dump-flows s'+str(i) +' >' +output_path+ str(S)+'/'+str(H)+'/s'+str(i)+'.flows' + '&'
                switch_o_l[i].cmd(command)
	net.stop()

if __name__ == '__main__':

	setLogLevel('warning')	

	options, remainder = getopt.getopt(sys.argv[1:], 'vuo:H:S:C:t:', ['verbose','udp','output','n_hosts','n_switches','n_cores','time'])
	verbose=False
	udp_op=''
	output_path=''
	H = 2
	S = 1



	for opt, arg in options:

		if opt in ('-v', '--verbose'):
			verbose=True
			setLogLevel('debug')	

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

		if opt in ('-S', '--n_switches'):
			S=int(arg)

		if opt in ('-t', '--time'):
			TIME=int(arg)

	writeLogMessage('Starting test',sys.stdout)	
	perfTest(verbose, udp_op, output_path,True)

