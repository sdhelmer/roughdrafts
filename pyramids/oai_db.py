import couchdb
from numpy import random
import os
import shutil
opj = os.path.join
import numpy as np
import pdb
import pickle
import time
#categories = ['bags','shoes','shirts','watches']
categories = ['shoes-main']
root_path = '/media/ssd/productify-main/'
dest_path = '/home/scott/Datasets/test1'
server = 'http://localhost:3000'

def doc2dict(data):
    data_dict = {}
    for key, value in data.iteritems():
        data_dict[key] = value
    return data_dict

def grab_images():
    couch = couchdb.Server('http://localhost:3000')
    for category in categories:
        data = {}
        db = couch[category]
        ids = [id for id in db]
#        sub_ids = ids[0:10]
    
        sub_ids = [ids[id] for id in random.permutation(len(ids))]
#        docs = [db[id] for id in sub_ids]
#        for doc in docs: print docs
        for id in sub_ids:
            doc = db[id]
            if doc['type'] != 'product': continue
            
            product = doc2dict(doc)
#                for key, value in doc.iteritems():
#                    doc_dict[key] = value
            print doc
            for view_key, image_id in product['views'].iteritems():
#                if view_key == 'main':
                image = doc2dict(db[image_id])
                image['id'] = image_id
                product['views'][view_key] = image 
                        
                source = opj( root_path, category, image['path'], image['data'])
                dest = opj( dest_path, category+'_'+id+'_'+view_key+'.jpg')
#                print 'SOURCE: ',source
#                print 'DEST: ',dest
                shutil.copy(source, dest)

def grab_descriptors(feature_type, data_type, combine = True):
    couch = couchdb.Server('server')
    data ={'imids':[],'pids':[],'data':[],'data_type':data_type}
    c= 0
    t1 = time.clock()
    matrix = []
    for category in categories:
        db = couch[category]
        for key in couch[category]:
            product = db[key]
#            pdb.set_trace()
            if (not product.has_key('type') or product['type'] != 'product'
            or not product['views'].has_key('main')):
                continue
            pid = key
            imid = product['views']['main']
#            impath = db[imid]['path']
            file_name = opj(root_path,category, db[imid]['path'],db[imid][feature_type])
            feature_data = np.fromfile(open(file_name,'r'), dtype = data_type)
            data['imids'].append(imid)
            data['pids'].append(pid)
#            data['data'].append(feature_data)
            matrix.append(feature_data)
            c += 1
#            if c >3000: break
#            if c>100: break
#        data['data'] = np.vstack(data['data'])
        matrix = np.vstack(matrix)
#    print data['data'].shape 
    data['data'] = matrix.shape
    fp = open(opj(dest_path,'boc_test'),'w')
    pickle.dump(data,fp)
    matrix.tofile(fp)
    fp.close() 
    print matrix.shape
    print time.clock() - t1            
                
                
        
        
        
if __name__ == '__main__':
    grab_descriptors('boc', np.float64)
    
    
        
            
            

