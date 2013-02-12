import os
import sys
import argparse

import pdb
opj = os.path.join



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

def crawl_subset(source_dir, img_list, img_type):
    paths = []
    for im_id in img_list:
#        pdb.set_trace()
        path = opj(source_dir, im_id[:2], im_id[2:4], im_id)
        if os.path.exists(path): 
            if (os.path.exists(opj(path,'cropmask')) and 
            os.path.exists(opj(path, 'cropped'))):
                paths.append(opj(path, img_type))
    return paths
    
    
               
if __name__ == '__main__':
    
    
    source_dir = sys.argv[1]
#    img_list = open(sys.argv[2], 'r').readlines()
#    img_list = [im.strip('\n') for im in img_list]
#    crawl_subset(source_dir, img_list[:10000])
    paths = get_db_paths(source_dir)
    
    if len(sys.argv)>3:
        paths = [opj(p, sys.argv[3]) for p in paths if 
                 os.path.exists(opj(p, sys.argv[3]))]
    
    fp = open(sys.argv[2], 'w')
    for p in paths: 
        fp.write(p+'\n')
    fp.close()
    
    
    
    
    
    
                
    