import os
import ioutil
import subprocess
import shutil
opj = os.path.join
from numpy import *

import pickle
import pdb

def grab_sift_filenames(directory):
    return sort([filename for filename in os.listdir(directory) 
            if os.path.splitext(filename)[1] == '.sift'])

class Processor:
    def __init__(self,opts):
        self.__dict__.update(opts)
        self.feature_file = opj(self.data_dir,self.vocab_name)
        self.feature_dir = opj(self.data_dir, 'features')
        self.feat_dim = int(self.feat_dim)
        
        self.membership_file = self.feature_file + '.membership'
        self.keypoint_file = opj(self.data_dir,self.vocab_name+'.assigned')
    def extract_features(self, oaitk_dir, extractor):
        curr_dir = os.getcwd()
        os.chdir(oaitk_dir)
        tmpdir = 'tmp'
        command = [extractor, self.image_dir, self.data_dir, tmpdir]
        proc = subprocess.Popen(command)
        proc.wait()
        shutil.move(opj(self.data_dir, tmpdir,'features'),
                    self.feature_dir)
        os.chdir(curr_dir)
        
    def cluster(self):
        self._combine_data()
        
        command = [self.cluster_exec, '-i', self.feature_file,
                   '-b', '-n', self.nwords, '-t', self.cluster_threshold,
                   '-p', self.nproc, '-o']
        print "RUNNING : ", " ".join(command)
        proc = subprocess.Popen(command)
        proc.wait()
        print "DONE: ",command[0]

        self._assign_keypoints()
        
    def _combine_data(self):
        
        nfeatures = 0
        self.sift_filenames = grab_sift_filenames(self.feature_dir)
        all_data = []
        for filename in self.sift_filenames:
            tmpdata = fromfile(open(opj(self.feature_dir, filename),'r'), dtype = float32).reshape(-1,36)
            all_data.append(tmpdata[:,:self.feat_dim])
            nfeatures += tmpdata.shape[0]
        
        fp = open(self.feature_file, 'w')
        header = array((nfeatures, self.feat_dim), dtype = int32)
        header.tofile(fp)
        for sift_data in all_data:
            sift_data.tofile(fp)       
        fp.close()
    
    def _assign_keypoints(self):
        
        fp = open(self.membership_file,'r')
        membership_data = int64(fromfile(fp, sep = ' \n').reshape(-1,2))
        fp.close()
        assignment = membership_data[:,1] #Making an assumption that data is ordered
        
        data = {}
        prev_index = 0
#        pdb.set_trace()
        for filename in self.sift_filenames:
            tmpdata = fromfile(open(opj(self.feature_dir, filename),'r'), dtype = float32).reshape(-1,36)
            data[filename] = {'keypoints': tmpdata[:,self.feat_dim:],
                        'locs': tmpdata[:,self.feat_dim:self.feat_dim+2],
                        'scale': tmpdata[:,self.feat_dim+2],
                        'membership': assignment[prev_index:prev_index+tmpdata.shape[0]]}
            prev_index += tmpdata.shape[0]
#        pdb.set_trace()
        fp = open(self.keypoint_file,'w')
        pickle.dump(data,fp)
        fp.close()
        

    
