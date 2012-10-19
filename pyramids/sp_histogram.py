from numpy import *
import os
opj = os.path.join
ope = os.path.splitext
import sys
import numpy as np

import pdb
import time
import pickle
import ioutil #from utilities

from scipy import spatial
#import shutils

metrics = spatial.distance

class SP_histogram:
    def __init__(self, splits, sizes = None, scale_levels = 1, bsize = None):
        self.scale_levels = scale_levels
      
        self.splits = splits
        self.sizes = sizes
        self.bsize = bsize
        if self.bsize != None:
            self.hist_size = bsize*sum([prod(self.splits**level) for level in range(self.scale_levels+1)])
        if bsize:
            self.pyramid_index = cumsum([bsize*prod(self.splits**(level)) for level in range(scale_levels)])   
            
        if scale_levels == 0: return
        if sizes != None:
            self.gridder = array([[self.sizes[dim]/self.splits[dim]**(sl+1) 
                         for dim in range(len(self.splits))] 
                        for sl in range(self.scale_levels)]).reshape(-1, len(self.splits))
        else:
            self.gridder = array([[1.0/self.splits[dim]**(sl+1) 
                         for dim in range(len(self.splits))] 
                        for sl in range(self.scale_levels)]).reshape(-1, len(self.splits))
        
        
          
    def create_histogram(self, locs, bins, sizes = None, bsize = None):
        
        bsize= self.bsize if bsize==None else bsize
        indices = [bins]
        if self.scale_levels ==0:
            gridder = []
        else:
            gridder = ceil(self.gridder) if sizes==None else ceil(sizes*self.gridder)

        base = bsize
        for level, grid in enumerate(gridder):
            mult = array([ prod(self.splits[:i]**(level+1)) for i in range(len(grid))])            
            try:
                index = base + sum(int32(locs/grid) * mult,1) * bsize + bins
            except:
                print "ERROR"
                pdb.set_trace()
            
            indices.append(index)
            base += bsize*prod(self.splits**(level+1))   
        indices = vstack(indices).T
        result = zeros(base)
        
#        print indices
#        pdb.set_trace()
        for i in indices.ravel(): 
            result[i]+=1
        return result
    
    def sp_distance(self, M, reweight = True, ignore_flat = False):
#        pdb.set_trace()
        weight = ones(self.hist_size)
        if reweight:
            for ip in self.pyramid_index:
                weight[ip:] *= self.splits[0] #maybe invalid assumption
        if ignore_flat:
            weight[:self.pyramid_index[0]] = 0
        result = []
#        pdb.set_trace()
        for row in M:
            inter = sum((row+M - abs(row-M))*weight/2.0,1)
            result.append(inter)
#        pdb.set_trace()
        return -vstack(result)
    
    def L2_dist(self, M, normalize = False):
        if normalize:
            M = M/sqrt(sum(M**2,1).reshape(-1,1))
        return metrics.squareform(metrics.pdist(M))
    
    def L1_dist(self, M, normalize = False):
        if normalize:
            M = M/sum(M,1).reshape(-1,1)
        return metrics.squareform(metrics.pdist(M,'cityblock'))

def edist(M):
    M2 = sum(M**2,1)
    return -2*dot(M,M.T) + M2 + M2.reshape(-1,1)   
        
def search( data, sph, dist_metric = 'spd', weight_scheme = 'reweight'):
    filenames = [filename for filename in data.iterkeys()]
    histograms = vstack([data[filename]['histogram'] for filename in filenames ])
#    pdb.set_trace()
#    histograms = histograms/sum(histograms,1).reshape(-1,1)
#    result = edist(histograms)

#    result = metrics.squareform(metrics.pdist(histograms))
    if dist_metric == 'spd':
        if weight_scheme == 'reweight':
            result = sph.sp_distance(histograms)
        elif weight_scheme == 'noweight':
            result = sph.sp_distance(histograms, False)
        elif weight_scheme == 'ignore_flat':
            result = sph.sp_distance(histograms, False, True)
    elif dist_metric == 'L2':
        result = sph.L2_dist(histograms, True)
    elif dist_metric == 'L1':
        result = sph.L1_dist(histograms, True)
    return result, filenames
 
def image_output(image_dir, output_dir, filenames, M, num_per_image = 7):
    from PIL import Image
    images = []
#    [Image.open(opj(image_dir, filename)) for filename in filenames ]

    for filename in filenames:
        image = Image.open(opj(image_dir, filename)).convert('RGB')
        image.thumbnail((80,80))
        images.append(image) 
#    pdb.set_trace()
    for i in np.random.permutation(len(images))[:40]:
        closest = np.argsort(M[i])
#        close_images = [images[j] for j in closest[range(num_per_image)]]
        for j in range(num_per_image):
#            print opj(output_dir,ope(filenames[i])[0] +
#                                        "_" + str(j)+".jpg")
#            print filenames[closest[j]]
            images[closest[j]].save(opj(output_dir,ope(filenames[i])[0] +
                                        "_" + str(j)+".jpg"))
        
def create_histograms(data_filename, nwords, splits = None, scale_levels = 1):
            
    splits = splits if splits != None else array((2,2))
    fp = open(data_filename, 'r')
    data = pickle.load(fp)
    hist_maker = SP_histogram( splits, None, scale_levels, nwords)
    fp.close()
    for filename, im_data in data.iteritems():
        im_data['histogram'] = hist_maker.create_histogram(im_data['locs'], im_data['membership'], amax(im_data['locs'],0)+1 )

        print filename
    return data, hist_maker

if __name__ == "__main__":
    np.set_printoptions(precision = 3, edgeitems  = None)

    opts =  ioutil.load_command_line(sys.argv[1:], keys = ['input_data', 'nwords',
                'image_dir', 'output_dir'],
                flag_keys=['make_hists', 'do_search','both'])
    if opts.has_key('make_hists'):
        data, hist_maker = create_histograms(opts['input_data'], int(opts['nwords']))
        fp = open(opts['output_data'],'w')
        pickle.dump(data,fp)
        fp.close()
    elif opts.has_key('do_search'):
        fp = open(opts['input'], 'r')
        data = pickle.load(fp)
        hist_maker = SP_histogram( array((2,2)), None, 1, int(opts['nwords']))
        result, filenames = search(data, hist_maker)
        filenames = [ope(filename)[0]+".png" for filename in filenames]
#        pdb.set_trace()
        if not os.path.exists(opts['output_dir']):
            os.makedirs(opts['output_dir']) 
        image_output(opts['image_dir'], opts['output_dir'], filenames, result, 5)
    elif opts.has_key('both'):
        data, hist_maker = create_histograms(opts['input_data'], int(opts['nwords']))
        result, filenames = search(data, hist_maker)
        filenames = [ope(filename)[0]+".png" for filename in filenames]
#        pdb.set_trace()
        if not os.path.exists(opts['output_dir']):
            os.makedirs(opts['output_dir']) 
        image_output(opts['image_dir'], opts['output_dir'], filenames, result, 7)   
        
#python sp_histogram.py --input_data dsift_small.spd --nwords 500 --image_dir /media/ssd/wolf/images_normalized/ --output_dir tmpresults/ --both 
 
    
#    bins = random.randint(0,999,1000)
#    locs = random.randint(0,100,2000).reshape(-1,2)
#    
#    
#    splits = array((2,2))
#    sizes = array((100,100))
#    hist_maker = SP_histogram( splits, sizes, 2 )
#    hist_maker = SP_histogram(splits, None, 2)
#    hist_maker.create_sp_histogram(2, array(( (10,2), (51,59), (88, 16) )), array((0,0,0)), array((100,100)))
#    hist_maker.create_sp_histogram(1000, locs, bins)
    