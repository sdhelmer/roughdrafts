from numpy import *
import numpy as np
import os
import sys
opj = os.path.join
import pdb
import pickle

SIFT_DIM = 32

def combine_data():
    np.set_printoptions(precision = 3, edgeitems  = None)
    data_dir = sys.argv[1]
    filenames = os.listdir(data_dir)
    sift_data = {}
    run_name = sys.argv[2]
    output_fp = open(run_name +'.subset','w')
    n_features = 0
    count = 0
    for filename in filenames:
        
        if os.path.splitext(filename)[1] != '.sift': continue
        tmpdata = np.fromfile(open(opj(data_dir, filename)), dtype = float32).reshape(-1,SIFT_DIM+4)
        sift_data[filename] = {'descriptors': tmpdata[:,:SIFT_DIM], 'keypoints':tmpdata[:,128:]}
        count += 1

        n_features += tmpdata.shape[0]
        if count>750: break

    header = array((n_features,SIFT_DIM),dtype = int32)
    
    fp_fnames = open(run_name+'.fnames','w')
    header.tofile(output_fp)
    for filename, data in sift_data.iteritems():
        data['descriptors'].tofile(output_fp)
        fp_fnames.write(filename+"\n") 

def combine_membership_keypoints():
    data_dir = sys.argv[1]
    run_name = sys.argv[2]
    fp_fnames = open(run_name+'.fnames','r')
    filenames = [fname.strip() for fname in fp_fnames.readlines()]
    membership = np.fromfile(open(run_name +'.subset.membership','r'), sep = " \n").reshape(-1,2)
    print sum(diff(membership[:,0])), membership.shape[0]
    base = 0
    sift_data = {}
#    pdb.set_trace()
    for filename in filenames:
        tmpdata = np.fromfile(open(opj(data_dir, filename)), dtype = float32).reshape(-1, SIFT_DIM+4)
        sift_data[filename] = {'membership':int32(membership[base:base+tmpdata.shape[0],1]), 'keypoints':tmpdata[:,SIFT_DIM:],
                               'locs':tmpdata[:, SIFT_DIM:SIFT_DIM+2], 'scales':tmpdata[:,SIFT_DIM+2]}
        base += tmpdata.shape[0]
    output_fp = open(run_name+'.spd','w')
    pickle.dump(sift_data, output_fp)


if __name__ == "__main__":
    combine_membership_keypoints()
#    combine_data()
