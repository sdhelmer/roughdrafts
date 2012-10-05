import xml.dom.minidom



TEXT_NODE = xml.dom.minidom.Node.TEXT_NODE


def get_anndict(filename, forcelist_keys = []):
    """Returns an dictionary, the relevant data being in result['annotation']"""
    doc = xml.dom.minidom.parse(open(filename,"r"))
    return xml2dict(doc.childNodes, forcelist_keys)

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
        
def mywriter(nodes,fp,depth):
    """Cause pythons minidom writer sucks. But I don't use this either"""

    
    for node in nodes:
        if len(node.childNodes)==1 and node.childNodes[0].nodeType == TEXT_NODE:
            val = str(node.childNodes[0].nodeValue)
            fp.write("\t"*depth+"<"+node.nodeName+">"+str(val)+"</"+node.nodeName+">\n")
            
            
        else:
            fp.write("\t"*depth+"<"+node.nodeName+">\n")
            mywriter(node.childNodes, fp, depth+1)
            fp.write("\t"*depth+"</"+node.nodeName+">\n")
            #child_dict = xml2dict(node.childNodes)        
            
def save_as_xml(mydict, filename):
    xmldata = CreateXML()
    xmldata.create_annotation(mydict)
    xmldata.save(filename)
    
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
    
#####################################
#This section is for csv stuff
######################################
    
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

def output_csv(file, data, keys = None, use_first = False):
    """Saves the contents of the dictionary data into file in csv format
    
    keys is an optional argument that specifies which keys are saved, otherwise
    all of data is saved.
    """
    
    if keys == None and not use_first:
        keys = set(())
        for item in data:
            set.update(item.keys())
        keys = sorted(list(keys))
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

    
    
    