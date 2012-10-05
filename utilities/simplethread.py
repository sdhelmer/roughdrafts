import thread
import numpy as nu
import time
import sys

import subprocess
import tempfile
import copy
import os

class Threaded_Iterator:
	"""This class manages a set of threads in the case when we want to cap the number running.
	
	nproc: is the max number of threads we want running
	overwhat: is the list over which we iterate, where one is returned only when a thread is free
	results: is where we look to determine if the thread has finished,
	        which presummes it puts something in this list that is not None
	"""
	def __init__(self,nproc,overwhat,results):
		self.mythreads = [None]*nproc
		self.overwhat = overwhat
		self.myiter=None
		self.count=0
		self.results=results
		self.currentThread = -1
		self.alldone = False
	def __iter__(self):
		self.myiter = self.overwhat.__iter__()
		self.count =0
		return self
	def wait(self):
		working = True
		while working:
			working = False
			for t in self.mythreads:
				if self.results[t] == None:
					working = True
					time.sleep(1)
					break		
	def next(self):
		"""Goes through my threads waits until one is idle and returns the next item in overwhat."""
		none_free = True
		while none_free:
			whichThread=0
			for t in self.mythreads:
				if t == None or self.results[t] !=None:
					none_free = False
					break
				whichThread+=1
			if none_free:
				time.sleep(1)
			else:
				if self.count==len(self.results):
					while None in self.results: 
						time.sleep(1)
					return self.myiter.next()
				else:
					self.mythreads[whichThread] = self.count
					self.count+=1
					self.currentThread = whichThread
					return self.myiter.next()
		
def thread_list(overwhat, results, nproc=8):
	return Threaded_Iterator(nproc,overwhat,results)
			
def assign_func(func,store,i,args):
	store[i] = func(*args)
	
def thread_func(func,args,store,i):
	"""Take the func, apply it to the args, and save the result in store
	"""
	thread.start_new_thread(assign_func,(func,store,i,args))

def threads_wait(store):
	working = True
	while working:
		working = False
		for i,value in enumerate(store):
			if value == None:
				working = True
				time.sleep(1)
				
def multi_process(base_command, in_flag, out_flag, input_list, 
				merge_func, nproc):
	n = len(input_list)
	index = nu.random.permutation(n)
	in_files = []
	out_files = []
	processes = []
	for i in range(0, n, nu.ceil(float(n)/nproc)):
		command = copy.copy(base_command)

		in_files.append( tempfile.NamedTemporaryFile(mode='w', delete = False))
		out_files.append( tempfile.NamedTemporaryFile(mode='w', delete = False))
		for fname in input_list[i:i+int(nu.ceil(float(n)/nproc))]:
			in_files[-1].write(fname+"\n")
		in_files[-1].close()
		out_files[-1].close()
		print "Starting at ",i
		command.extend( (in_flag, in_files[-1].name, 
									out_flag, out_files[-1].name ) )
		print command
		processes.append(subprocess.Popen(command))
	print "OK"
	working = True
	while working:
		working = False
		for p in processes:
			if p.poll() == None:
				working = True
				time.sleep(0.5)
	
#	time.sleep(50)
	print "ALL_DONE     Just Merging *************************"
	merge_func([fp.name for fp in out_files])
	for i in range(len(in_files)):
		os.remove(in_files[i].name)
		os.remove(out_files[i].name)	
		
			
def blad(a,b):
	print b
	for v in a:
		c =  open(v,'r').readlines()
		print c
		
if __name__=="__main__":
	print sys.argv
	
	if sys.argv[1] == "--detector":
		import ioutil
		opts = ioutil.load_command_line(sys.argv[1:], keys = ['csv_filename',
				'detector', 'config'])
		command = ['python', opts['detector'], '--config', opts['config']]

		tmp_filenames = []
		scene_list = ioutil.ext_filter(opts['scene_path'],['.xml'])
		for ovlp in [0.5]:
			for alg_type in ['UNION', 'INTERSECTION']:
				com = copy.copy(command)
				com.extend(['--nms_alg',alg_type,'--overlap',str(ovlp),
						'--alg_name', alg_type[0:5]+str(ovlp)])
				fp = tempfile.NamedTemporaryFile(mode='w', delete = False)
				tmp_filenames.append(fp.name)
				fp.close()
				merge_func = lambda filenames: ioutil.merge_csv_files(filenames,
											tmp_filenames[-1])
				multi_process(com,'--scene_list', '--csv_filename', scene_list,
					merge_func, 7)
		ioutil.merge_csv_files(tmp_filenames, opts['csv_filename'])
		for fname in tmp_filenames:
			os.remove(fname)	
		
	elif sys.argv[1] == "--config":
		import ioutil
		import pdb
		
		opts = {'detector':'contours.py'}
		keys = set(['config','csv_filename', 'detector'])
		add_keys = set([s[2:] for s in sys.argv[1:] if s[:2] == "--"])
		new_keys = list(add_keys.difference(keys))
#		new_keys.discard('detector')
		print add_keys
		print new_keys
		keys = keys.union(add_keys)
		print keys
		opts.update(ioutil.load_command_line(sys.argv[1:], keys = list(keys) ))
		
		command = ['python', opts['detector'], '--config', sys.argv[2]]
		for k in new_keys:
			command.extend(['--'+k, opts[k]])
		
		if opts.has_key('scene_list'):
			scene_list = [os.path.join(opts['root_path'],fname)
				  for fname in open(opts['scene_list'],'r').readlines()]
		else:
			scene_list = ioutil.ext_filter(opts['scene_path'],['.xml'])
		
			
		
		merge_func = lambda filenames: ioutil.merge_csv_files(filenames,
												opts['csv_filename']) 
		multi_process(command,'--scene_list', '--csv_filename', scene_list,
					merge_func, 7)
	
	elif sys.argv[1] == "1":
		base_command = ["python", "simplethread.py"]
		inlist = [str(i) for i in range(13)]
		merge_func = lambda files: blad(files,"BAD ")
		multi_process(base_command, "a", "b", inlist, merge_func, 2)
		
	elif sys.argv[1] == "a":
		f = open(sys.argv[2],'r').readline()
#		print f
		n = int(f.strip(" \n"))
#		print n
		a = nu.random.rand(2700,2700)
		c = nu.dot(a,a)
		f = open(sys.argv[4],'w')
		f.write(str(n*10))
		f.close()
		print "DONE"
			
			
			
	else:
		a = nu.random.rand(2000,2000)
		res = [None]*12
		for i in Threaded_Iterator(8,range(12),res):
			thread_func(nu.dot,(a,a),res,i)
			print i
		for i in res:
			print i.shape
