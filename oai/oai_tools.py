import os
import sys
import glob
import time
import Queue
import array
import thread
import ctypes
import argparse
import numpy as np
import os.path as path
from threading import Thread
from threading import RLock
from multiprocessing.pool import ThreadPool

import pdb
opj = os.path.join

def cfunc(name, dll, result, *args):
    atypes = []
    aflags = []
    for arg in args:
        atypes.append(arg[1])
        aflags.append((arg[2], arg[0]) + arg[3:])
    return ctypes.CFUNCTYPE(result, *atypes)((name, dll), tuple(aflags))

#_metricDLL = ctypes.cdll.LoadLibrary('libmetrics.so')
_metricDLL = ctypes.cdll.LoadLibrary('libmetrics.dylib')

c_float_p = ctypes.POINTER(ctypes.c_float)
c_double_p = ctypes.POINTER(ctypes.c_double)

#mapping numpy types to c types
ctype2numpy_dict_ = {'float32':ctypes.c_float, 'int32':ctypes.c_int32,
                     'uint8':ctypes.c_byte,'float64': ctypes.c_double}

def n2c(arr):
    """Return the data of numpy array as a c pointer
    """
    return arr.ctypes.data_as(ctypes.POINTER(ctype2numpy_dict_[arr.dtype.name]))


#These are the handles for the c librar functions
c_L1_double = cfunc('L1dist_double', _metricDLL, None, ('feature',c_double_p,1), ('data_Matrix',c_double_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_double_p,1))

c_intersection_double = cfunc('histIntersection_double', _metricDLL, None, ('feature',c_double_p,1), ('data_Matrix',c_double_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_double_p,1))

c_L2_double = cfunc('L2dist_double', _metricDLL, None, ('feature',c_double_p,1), ('data_Matrix',c_double_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_double_p,1))
c_hellinger_double = cfunc('hellinger_double', _metricDLL, None, ('feature',c_double_p,1), ('data_Matrix',c_double_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_double_p,1))

c_L1_float = cfunc('L1dist_float', _metricDLL, None, ('feature',c_float_p,1), ('data_Matrix',c_float_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_float_p,1))

c_intersection_float = cfunc('histIntersection_float', _metricDLL, None, ('feature',c_float_p,1), ('data_Matrix',c_float_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_float_p,1))

c_L2_float = cfunc('L2dist_float', _metricDLL, None, ('feature',c_float_p,1), ('data_Matrix',c_float_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_float_p,1))
c_hellinger_float = cfunc('hellinger_float', _metricDLL, None, ('feature',c_float_p,1), ('data_Matrix',c_float_p,1), 
            ('dim',ctypes.c_int,1), ('n',ctypes.c_int,1), ('output',c_float_p,1))

#f1 is a n dimensional numpy vector
#F2 is a n x k dimensional matrix, where the rows are vectors compared to f1
def fast_L1(f1,F2, output = None):
    dtype = F2.dtype
    if f1.dtype != dtype:
        f1 = f1.astype(dtype)

    if output == None:
        output = np.zeros(F2.shape[0], dtype = dtype)
    if dtype == np.float64:
        c_L1_double(n2c(f1),n2c(F2),F2.shape[1],F2.shape[0], n2c(output))
    else:
        c_L1_float(n2c(f1),n2c(F2),F2.shape[1],F2.shape[0], n2c(output))
    return output

def fast_L2(f1,F2, output = None):
    dtype = F2.dtype
    if f1.dtype != dtype:
        f1 = f1.astype(dtype)

    if output == None:
        output = np.zeros(F2.shape[0], dtype = dtype)
    if dtype == np.float64:
        c_L2_double(n2c(f1),n2c(F2),F2.shape[1],F2.shape[0], n2c(output))
    else:
        c_L2_float(n2c(f1),n2c(F2),F2.shape[1],F2.shape[0], n2c(output))
    return output

def fast_hellinger(f1, F2, output = None):
    """This is slower than it needs to be, if we preprocessed data we
    would not need to computer sqrt(F2) every search.
    
    Hellinger needs L1 normalization.
    """
    dtype = F2.dtype
    if f1.dtype != dtype:
        f1 = f1.astype(dtype)

    if output == None:
        output = np.zeros(F2.shape[0], dtype = dtype)
    fast_L2(np.sqrt(f1), np.sqrt(F2), output)     
    return output

def fast_intersection(f1, F2, output = None):
    """Computes the histogram intersection. Remember that this is not a 
    distance.
    """
    dtype = F2.dtype
    if f1.dtype != dtype:
        f1 = f1.astype(dtype)
    if output == None:
        output = np.zeros(F2.shape[0], dtype = dtype)
    if dtype == np.float64:
        c_intersection_double(n2c(f1),n2c(F2),F2.shape[1],F2.shape[0], n2c(output))
    else: 
        c_intersection_float(n2c(f1),n2c(F2),F2.shape[1],F2.shape[0], n2c(output))
    return output

def assign_func(func,store,i,args):
    store[i] = func(*args)
    
def thread_func(func,args,store,i):
    """Take the func, apply it to the args, and save the result in store
    """
    return thread.start_new_thread(assign_func,(func,store,i,args))

def threaded_intersection(f1, F2, output = None, nproc = 1,
                          wait_time = 0.01):
    """Computes the histogram intersection.
    
    Remember that this is not a distance.
    """
    dtype = F2.dtype
    if f1.dtype != dtype:
        f1 = f1.astype(dtype)
    steps = np.linspace(0,F2.shape[0],nproc+1)
    tmp_input = [F2[i:j] for i,j in zip(steps[:-1], steps[1:]) ]
    output = [None]*nproc
    threads = []
    for i in range(len(output)):
        threads.append(thread_func( fast_intersection, 
            (f1, tmp_input[i]), output, i ) )    
    while True:
        still_running = np.sum( [value==None for value in output] )
        if still_running == 0: 
            break
        else:
            time.sleep(wait_time)
    output = np.hstack(output)                       
    return output


def fast_inter_over_union(f1, F2, output = None, F2sum = None):
    """  
    This is not a distance, so searching with minimum will fail because
    large is good."""
    inter = threaded_intersection(f1, F2)
    if F2sum == None:
        inter_over_union = inter/(np.sum(F2,1) + np.sum(f1) - inter)
    else:
        inter_over_union = inter/(F2sum + np.sum(f1) - inter)
    if output != None:
        output[:] = inter_over_union
    return inter_over_union
    
def negated_inter_over_union(f1, F2, output = None, F2sum = None ):
    """We need the negation because intersection is not a distance."""
    return 1-fast_inter_over_union(f1,F2,output,F2sum)

def load_hists(files, dtype):
    datatypes = {"byte":   {"size": 1, "code": "c", 'dtype': np.uint8},
                 "int":    {"size": 4, "code": "I", 'dtype': np.int32},
                "float":  {"size": 4, "code": "f", 'dtype': np.float32},
                "double": {"size": 8, "code": "d", 'dtype': np.float64}}

    typesize = datatypes[dtype]["size"]
    typecode = datatypes[dtype]["dtype"]

    if len(files) == 0:
        return

    # Make sure all files exists and are the same size
    filesize = os.stat(files[0]).st_size
    if filesize%typesize != 0:
        raise Exception("File size not multiple of %d. Wrong datatype."%typesize)

    for f in files:
        if not path.isfile(f):
            raise Exception("File %s does not exist"%f)
        if os.stat(f).st_size != filesize:
            raise Exception("File %s not same size as first file"%f)

    numdims = filesize / typesize
    sys.stdout.write("Allocating memory")
    sys.stdout.flush()
    data = np.empty((len(files), numdims))
    print " ... done!"

    for i,f in enumerate(files):
        if i%50 == 0 or i == 0 or i == len(files)-1:
            sys.stdout.write("\rReading files: %d%%"%(float(i)/len(files)*100))
            sys.stdout.flush()

#        a = array.array(typecode)
        with open(f,'r') as fd:
#            a.fromfile(fd, numdims)
            data[i,:] = np.fromfile(fd, dtype = typecode)
#    print " ... done!"

    return data

def get_db_paths(source_dir):
    paths = []
    for dir1 in os.listdir(source_dir):
        path = opj(source_dir,dir1)
        if not os.path.isdir(path): continue
        for dir2 in os.listdir(path):
            path = opj(source_dir, dir1, dir2)
            if not os.path.isdir(path): continue
            for dir3 in os.listdir(path):
                path = opj(source_dir, dir1, dir2,dir3)
                if not os.path.isdir(path): continue
                paths.append(path)                
    return paths

def load_data(ext, dtype, source_dir = None, paths = None):
    """Load numpy vectors of dtype from either the source_dir or given paths 
    where each path is joined with ext."""
    if source_dir is not None:
        paths = get_db_paths(source_dir)
    paths = [opj(p, ext) for p in paths]
    return load_hists(paths, dtype)


def search(query, database, desc_keys = None):
    all_scores = 0
#    pdb.set_trace()
    for desc_key, desc_data in database.iteritems():
        if desc_keys is not None and desc_key not in desc_keys:
            continue
        if desc_data.has_key('data_sum'):
            scores = desc_data['metric'](query[desc_key],
                        desc_data['data'], F2sum = desc_data['data_sum'])
        else:
            scores = desc_data['metric'](query[desc_key],
                                         desc_data['data'])
        all_scores += scores * desc_data['w']
    return all_scores
settings = {"ngist1pc" : {'w': 0.0005, 'metric': fast_L1, 'dtype': 'double'},
            "bocsph": {'w': 0.2, 'metric': negated_inter_over_union,
                       'dtype':'float'},
            "sph": {'w': 0.8, 'metric': negated_inter_over_union,
                    'dtype': 'float'}}

metrics = {"negated_inter_over_union": negated_inter_over_union,
               "L1": fast_L1,
               "L2": fast_L2,
               "hellinger": fast_hellinger}
     
class Searcher:
    def __init__(self, db_paths, query_paths = None, desc_settings = settings):
        self.db_data = desc_settings.copy()
        for key, data in self.db_data.iteritems():
            self.db_data[key]['data'] = load_data(  key, data['dtype'],
                                                        paths =  db_paths)
            if data['metric'] == negated_inter_over_union:
                data['data_sum'] = np.sum( self.db_data[key]['data'] , 1)
            
        self.db_paths = db_paths
    def load_queries(self, query_paths):
        """Uses the current db_data settings to read in the various types of
        data from query_paths"""
        queries = {}
        for query_path in query_paths:
            queries[query_path] = {}
       
        for key, data in self.db_data.iteritems():
            query_data = load_data(  key, data['dtype'], paths = query_paths)
            for query_path, q_data in zip(query_paths, query_data):
                queries[query_path][key] = q_data
        return queries
                
    def search(self, query = None, query_path = None, rank = True):
        if query is not None:
            query_data = query
        elif query_path is not None:
            query_data = self.load_queries([query_path])[0]
        results = search(query_data, self.db_data)
        if rank:
            results = zip(results, self.db_paths)
            results.sort(key = lambda x: x[0])
            return results
        else:
            return results

if __name__ == '__main__':
    db_dir = '/media/ssd-256/productify/shoes'
    q_dir = '/media/ssd/scott/shoes_mobile-groundtruth_164/images'
    db_stubs = get_db_paths( db_dir)[:1000]
    q_stubs = get_db_paths( q_dir)
    
    output_dir = 'top_results'
    
    searcher = Searcher(db_stubs)
    queries = searcher(q_stubs)

    query_paths = queries.keys()
    completed = Queue.Queue()
    def save_top_results(x):
        results = searcher.search(queries[query_paths[x]])
        fp = open(opj(output_dir, os.path.split(query_paths[x])[1]+'.txt'),'w')
        for i in range(50):
            fp.write(os.path.split(results[i][1])[1] + '\n')
        fp.close()
     
     
    def print_search_progress():
        while completed.qsize() != len(q_stubs):
            sys.stdout.write("\rGenerating results: %d%%"%(float(
                                completed.qsize())/len(q_stubs)*100))
            sys.stdout.flush()
            time.sleep(0.2)
            
    Thread(target=print_search_progress).start()    
    pool = ThreadPool(processes=20)
    pool.map(search, range(len(q_stubs)))
 
 