import xml.dom.minidom
import copy
import os
import ConfigParser
import getopt
import pdb
import numpy
import re
import sys
TEXT_NODE = xml.dom.minidom.Node.TEXT_NODE

opj = os.path.join
ops = os.path.split


def ext_filter(directory, exts, ABS_PATHS = True):
    """Returns all the files in directory with an extension in exts
    
    ABS_PATH = True implies that the full path will be returned
    """
    if isinstance(exts,list) or isinstance(exts,tuple):
        exts = list(exts)
    if ABS_PATHS:
        return [opj(directory,file) for file in os.listdir(directory) if 
                os.path.splitext(file)[1] in exts]
    else:
        return [file for file in os.listdir(directory) if 
                os.path.splitext(file)[1] in exts]


def recursive_load(filename, root_path, forcelist_keys = [], strip_upper = False):
    """Recursively loads the xml found at filename."""
    doc = xml.dom.minidom.parse(open(filename,"r"))
    if strip_upper:
        return recursive_xml2dict(doc.childNodes, root_path, forcelist_keys).values()[0] 
    else:
        return recursive_xml2dict(doc.childNodes, root_path, forcelist_keys)

def recursive_xml2dict(nodes, root_path, forcelist_keys =[]):
    """A helper function for recursive_load"""
    mydict = {}
#    pdb.set_trace()
    for node in nodes:
        if node.nodeType == TEXT_NODE:
            continue
        if len(node.childNodes)==1 and node.childNodes[0].nodeType == TEXT_NODE:
        
            if node.nodeName in forcelist_keys:
                mydict[node.nodeName] = [node.childNodes[0].nodeValue.strip()]
            else:
                mydict[node.nodeName] = node.childNodes[0].nodeValue.strip()
            
                
        else:
            child_dict = recursive_xml2dict(node.childNodes, root_path, forcelist_keys)
            if child_dict.has_key("xml_filename"):
#                pdb.set_trace()
                filename = os.path.join(root_path, child_dict['xml_filename'])
                if os.path.exists(filename):
                    ann = recursive_load(filename, root_path, forcelist_keys)
                    child_dict.update(ann.values()[0])
            if mydict.has_key(node.nodeName):
                if isinstance(mydict[node.nodeName],list):
                    mydict[node.nodeName].append(child_dict)
                else:
                    mydict[node.nodeName] = [mydict[node.nodeName], child_dict]
            else:
                if node.nodeName in forcelist_keys:
                    mydict[node.nodeName] = [child_dict]
                else:
                    mydict[node.nodeName] = child_dict
    return mydict
 
def get_anndict(filename, forcelist_keys = [], strip_upper = False):
    """Returns an dictionary, the relevant data being in result['annotation']"""
    doc = xml.dom.minidom.parse(open(filename,"r"))
    if strip_upper:
        return xml2dict(doc.childNodes, forcelist_keys).values()[0]
    else:
        return xml2dict(doc.childNodes, forcelist_keys)

def load_xml(filename, forcelist_keys = [], root_path = None):
    """Just a shortcut for get_anndict"""
    if root_path == None:
        return get_anndict(filename, forcelist_keys, True)
    else:
        return recursive_load(filename, root_path, forcelist_keys,
                               strip_upper = True)

def grab_item(data, find_key, with_value, trace = None):
    """Grabs the first item in data with item[find_key] = with_value"""
    if isinstance(data,list):
        for value in data:
            res = grab_item(value, find_key, with_value)
            if res != None:
                return res
        return  None
    elif isinstance(data, dict):
        if data.has_key(find_key) and data[find_key] == with_value:
            if trace != None:
                trace.append(data)
            return data[find_key]
        else:
            for value in data.itervalues():
                res = grab_item(value, find_key, with_value)
                if res != None: 
                    return res
    else:
        return None
            



def xml2dict(nodes, forcelist_keys = []):
    """Parses an xml file and returns a dictionary.
    
    All reoccurring items at one a level in the hierarchy are placed into a list
    """
    mydict = {}
#    pdb.set_trace()
    for node in nodes:
        if node.nodeType == TEXT_NODE:
            continue
        if len(node.childNodes)==1 and node.childNodes[0].nodeType == TEXT_NODE:
            if node.nodeName in forcelist_keys:
                mydict[node.nodeName] = [node.childNodes[0].nodeValue.strip()]
            else:
                mydict[node.nodeName] = node.childNodes[0].nodeValue.strip()
            
                
        else:
            child_dict = xml2dict(node.childNodes, forcelist_keys)
            if mydict.has_key(node.nodeName):
                if isinstance(mydict[node.nodeName],list):
                    mydict[node.nodeName].append(child_dict)
                else:
                    mydict[node.nodeName] = [mydict[node.nodeName], child_dict]
            else:
                if node.nodeName in forcelist_keys:
                    mydict[node.nodeName] = [child_dict]
                else:
                    mydict[node.nodeName] = child_dict
    return mydict
        
            
def save_as_xml(mydict, filename, embed = False):
    xmldata = CreateXML()

    if len(mydict.keys())>1:
        xmldata.create_annotation(mydict)
    else:
        xmldata.add_tags(mydict)    
    xmldata.save(filename)

def recursive_save_xml(mydict, filename, root = ""):
    """Needs testing"""
    myxml = xml.dom.minidom.Document()
    el = myxml.createElement(mydict.keys()[0])
    myxml.appendChild(el)
    recursive_dict2xml(myxml,el,mydict.values()[0], root)
    myxml.writexml(open(opj(root,filename),'w'))

def recursive_dict2xml(myxml, parent, mydict, root=""):
    """Needs testing"""
    #print mydict.keys()
    if 'xml_filename' in mydict.keys():
        tmp_dict = copy.deepcopy(mydict)
        del tmp_dict['xml_filename']
        tmp_dict = {parent.tagName: tmp_dict}
        recursive_save_xml(tmp_dict, mydict['xml_filename'], root)
        newTag = myxml.createElement('xml_filename')
        newTag.appendChild(myxml.createTextNode(
                        mydict['xml_filename']))
        parent.appendChild(newTag)
        return None
    for key, value in mydict.iteritems():
        if isinstance(value,list):
            for item in value: 
                newTag = myxml.createElement(key)
                recursive_dict2xml(myxml, newTag, item, root)
                parent.appendChild(newTag)
            continue
        newTag = myxml.createElement(key)
        if isinstance(value, dict):
            recursive_dict2xml(myxml, newTag, value, root)
        else:
            newTag.appendChild(myxml.createTextNode(str(value)))
        
        parent.appendChild(newTag)

class CreateXML:
    """CreateXML class 
    
    Create XML data for annotations in PASCAL VOC format
  
    @param selfThe object pointer
    """ 

    def __init__(self):
        self.xml = xml.dom.minidom.Document()

    def dict2xml(self, parent, mydict):
        """Turns a dict in a heiarchical xml thing, assumes that anything not a dict 
        is a valid item"""
    
        for key, value in mydict.iteritems():
            if isinstance(value,list):
                for item in value: 
                    newTag = self.xml.createElement(key)
                    self.dict2xml(newTag, item)
                    parent.appendChild(newTag)
                continue
            newTag = self.xml.createElement(key)
            if isinstance(value, dict):
                self.dict2xml(newTag, value)
            else:
                newTag.appendChild(self.xml.createTextNode(str(value)))
            
            parent.appendChild(newTag)

    def create_annotation(self, annotations):
        self.annotationTag = self.xml.createElement("annotation")
        self.xml.appendChild(self.annotationTag)
        self.dict2xml(self.annotationTag, annotations)
    #    return self.xml.toprettyxml()
    def add_tags(self, tags):
        #DAVE: I think this is the function you added, or something similar?
        self.dict2xml(self.xml, tags)
        
    def save(self, filename):
        #print filename
        #print self.xml.toprettyxml()
        self.xml.writexml(open(filename,"w"))#,"","\t","\n") prettier

def str2arr(input, new_shape = None, dtype = numpy.float32):
    """Takes a string with comma-sep numbers and returns an array"""
    input = input.split(",")
    input = numpy.array([dtype(el.strip()) for el in input])
    if new_shape == None: 
        return input
    else:
        return input.reshape(new_shape)



    
#####################################
#This section is for csv stuff
######################################
    
def parse_csvfile(filename):
    """Returns a list of dictionargies from filename"""
    return parse_csv(open(filename,'r').readlines())
    
def parse_csv(lines):
    """Returns a list of dictionaries from the data in lines."""
    data =[]
  #  pdb.set_trace()
    names = [item.strip(' ,\n') for item in lines[0].split(',') if item!="#"]
   # endlines = [line[-100:] for line in lines]
    for i,line in enumerate(lines[1:]):
    #    if line[-100:] in endlines[:i+1]:
     #       continue
        items = line.split(',')
        tmp = {}
        for i in range(len(names)):
            try:
                value = int(items[i].strip())
            except ValueError:
                try:
                    value = float(items[i].strip())
                except ValueError:
                    value = items[i].strip()
            except IndexError:
                print items     
            tmp[names[i]] = value
        data.append(tmp)
    return data
#            data[names[i]] = items[i]

def output_csvfile(filename, data, keys = None, use_first = False):
    file = open(filename,'w')
    output_csv(file, data, keys, use_first)

def output_csv(file, data, keys = None, use_first = False):
    """Saves the contents of the dictionary data into file in csv format
    
    keys is an optional argument that specifies which keys are saved, otherwise
    all of data is saved.
    """
    
    if keys == None and not use_first:
        keys = set(())
        for item in data:
            keys.update(set(item.keys()))
        keys = sorted(list(keys))
    #pdb.set_trace()
    if use_first:
        keys = sorted(data[0].keys())
    line = "#"
    for key in keys:
        line = line + ",%12s" % key
    line = line +"\n"
    file.write(line)
    for d in data:
        line = ""
        for k in keys:
            if d.has_key(k):
                line = line + "%12s, "% str(d[k])
            else:
                line = line + "%12s, "% str(-1 )
        line = line + "\n"
        file.write(line)    

def merge_csv_files(filenames, output_filename):
    """Loads all files and then outputs them in a single csv file."""
    all_csvs = []
    for filename in filenames:
  #      pdb.set_trace()
        all_csvs.extend(parse_csvfile(filename))
    output_csvfile(output_filename, all_csvs)
    return None

def load_config(filename, opt_dict = None):
    """Returns a dictionary from a config file."""
    config = ConfigParser.ConfigParser()
    file = config.read(filename)
    tmp_dict = config.defaults()
    prog = re.compile('\[[^\[\]]+\]')
    final_dict = {} if opt_dict == None else opt_dict
    done = False
    while not done:
        done = True
        for key, value in tmp_dict.iteritems():
            if value.find("[")<0:
                if not final_dict.has_key(key):
                    final_dict[key] = value
                continue
            myiter = prog.finditer(value)
            rs = []
            #Finding places where I can replace variables
            for match in myiter:
                si,ei = match.span()
                if final_dict.has_key(value[si+1:ei-1]):
                    rs.append([si,ei,final_dict[value[si+1:ei-1]]])
                elif os.environ.has_key(value[si+1:ei-1]):
                    rs.append([si,ei,os.environ[value[si+1:ei-1]]])
            if len(rs) == 0:
                done = False
                continue
            new_value = ""
            lasti = 0
            for si, ei, replacement in rs:
                new_value += value[lasti:si] + replacement
                lasti = ei
            new_value += value[lasti:]
            tmp_dict[key] = new_value
            if new_value.find('[')<0:
                final_dict[key] = new_value
            else: 
                done = False
                
            
    return final_dict
#        a = values.split('[')
#        new_value = ""
#        for b in a:
#            if len(b)
#            i = b.find(']')
#            if i == -1:
#                new_value += b
#            else:
                
#            if i == -1:
#                new_value += b
#            else:
#                tmp_val = b[:i]
#                if tmp_val in tmp_dict.keys():
#                    new_value += tmp_dict[tmp_val]
#                else:
#                    new_value += os.environ[tmp_val]
#                new_value += b[i+1:]
#        tmp_dict[key] = new_value
#    return tmp_dict


def load_command_line(argv, flags = "", keys = [],flag_keys = [], 
                      check_config = True, config_first = True):
    """Returns a dictionary from a config file. 
    
    flags aren't used at the moment
    keys is the list of keys (no need for preceeding -
    if keys has a special key called config, we use that file to load
    values
    """
    all_keys = [k+"=" for k in keys]
    all_keys.extend(flag_keys)
    opts, args = getopt.getopt(argv, flags, all_keys)
    opt_dict = {}
    for k,v in opts:
        opt_dict[k.lstrip("-")] = v
    if check_config and opt_dict.has_key('config') and config_first:
        tmp = {}
        tmp.update(load_config(opt_dict['config'], opt_dict.copy()))
        tmp.update(opt_dict)
        return tmp
    elif check_config and opt_dict.has_key('config'):
        opt_dict.update(load_config(opt_dict['config']))
    return opt_dict
    
 #######################################################



def load_scene_database(root_path, scene_list = None, scene_path = None):
    """Loads all of the scenes, which may be cumbersome if there is
    a lot of data.
    
    scene_list is a list of xml paths
    scenes_path is a directory
    
    Options are to load either from a list, or all xml files in a directory.
    """
    if scene_list == None:
        scene_list = ext_filter(scene_path, ['.xml'])
    
    scenes = {}
    forcelist_keys = ['object','view']
    for filename in scene_list: # fix, annotation might not be needed
        a, b = ops(filename)
        key = opj(ops(a)[1],b)
        scenes[key] = load_xml(filename, forcelist_keys, root_path = root_path)
        scenes[key]['xml_filename'] = key #BE CAREFUL
                            #ioutil.get_anndict(filename)['scene']

    return scenes  
if __name__ == "__main__":
    print load_config(sys.argv[1:])
 
    
    
