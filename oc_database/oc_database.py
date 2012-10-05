import couchdb
from numpy import random
import os
import shutil
opj = os.path.join


categories = ['bags','shoes','shirts','watches']
root_path = '/media/ssd/productify'
dest_path = '/home/scott/Datasets/test1'

def doc2dict(data):
    data_dict = {}
    for key, value in data.iteritems():
        data_dict[key] = value
    return data_dict

if __name__ == '__main__':
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
        
            
            

