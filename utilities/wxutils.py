"""
Short

This modules contains some generic extensions for wx, tools that I may want to reuse,
 but also don't want to have cluttering up the more research part of my code base.
 
 I probably should document this further, but my knowlege is a bit hazy at the moment.

"""
import sys
sys.path.append("../")
import wx
from numpy import *
#from constants import *
import pdb
#import visual
imgexts = '(*.jpg;*.JPG;*.pgm;*.png)|*.jpg;*.JPG;*.pgm;*.png|All (*)|*'

IMAGE_PANEL_DIM = (700,750) #Used by the GridImage stuff


class VisualDatum(wx.Image):
    #NOTE: I ripped this from visual.py, so somethings may not work
    def __init__(self,imagename = None,offset=0, image = None): 
        if image == None:
            wx.Image.__init__(self,imagename)
            self.imagename = imagename
        else:
            self.__dict__.update(image.__dict__)
        self.offset =offset
        self.scale = 1
        self.viewable = wx.Rect(0,0,self.GetWidth(),self.GetHeight())
        self.maxX = 500
        self.maxY = 500

    def setOffset(self,offset):
        self.offset = offset    
    def setDisplayBounds(self,x,y):
        self.maxX = x
        self.maxY = y
    def getViewable(self):
        return self.viewable
    def getViewableImage(self):
    
        im = self.GetSubImage(self.viewable)
        im.Rescale(self.scale*self.viewable.GetWidth(),self.scale*self.viewable.GetHeight())
        return im
    def contains(self,point):
        p = self.getImageLoc(point)
        return self.viewable.Contains(p)
    def isVisable(self,arr):
        """Allows for array testing, maybe slower than optimal"""
        return array([self.viewable.Contains(f) for f in arr])
    def setViewable(self,p1=None,p2=None,maxX = None, maxY = None, magnify = True):
        if maxX == None:
            maxX = self.maxX
            maxY = self.maxY
        if p1 == None:
            
            rescale = min(maxX/float(self.GetWidth()),maxY/float(self.GetHeight()))
            self.viewable.Set(0,0,self.GetWidth(),self.GetHeight())
        else:
            p1[p1<0]=0
            p2[p2>=self.GetSize()] = (array(self.GetSize())-1)[p2>=self.GetSize()]
            
            self.viewable.Set(p1[0],p1[1],p2[0]-p1[0],p2[1]-p1[1])
            
            rescale = min(maxX/float(self.viewable.GetWidth()),maxY/float(self.viewable.GetHeight()))
        if magnify== False:
            if rescale>1:
                self.scale = 1.0
        if rescale<3:
            self.scale = rescale
        else:
            self.scale = 3.0
    def getBmpSize(self):
        return self.mybmp.GetSize()
    def getImageLoc(self,point):
        if hasattr(point,'Get'):
            point = array(point.Get())
        else:
            point = array(point)
    #    point[0] = point[0]-self.offset
        point[0] = point[0] - self.offset + self.scale*self.viewable.GetX()
        point[1] = point[1] + self.scale*self.viewable.GetY()
        return around(point/self.scale)
    def getDisplayLoc(self,x,asPoints = False):

        if x.__class__ != ndarray:
            x = array(x,ndmin=2)
            
        if x.ndim==2:
            val = x*self.scale
        else:
            val = x.reshape(1,-1)*self.scale
#
        val[:,0] += self.offset - self.scale*self.viewable.GetX()
        val[:,1] += -self.scale*self.viewable.GetY()
        val = around(val)
        
        if asPoints == True:
            val = [wx.Point(*val[i,:]) for i in range(x.shape[0])]
        return val
    def getScale(self):
        return self.scale


class ButtonPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
    def addButtonToSizer(self,mylabel,handler,sizer=None, wxid = wx.ID_ANY):
        "Adds a button, along with it's handler to a sizer"
        button = wx.Button(self,wxid,label = mylabel)
        button.Bind(wx.EVT_BUTTON,handler)
        if sizer == None: self.GetSizer().Add(button,1)
        else:    sizer.Add(button,1)
        return button 


class ActivePanel(wx.Panel):
    def __init__(self,parent,mysize):
        wx.Panel.__init__(self,parent,size = mysize)
        self.drawObjects = {} #a dictionary that should contain key, values, where values are value[0] is a handler, and value[1] is it's arguments
        self.__tmpCanvas = None
        self.mouseData =[]
        self.scale = 1
    def drawSelf(self,event = None):
        self.__tmpCanvas = wx.PaintDC(self)        
        #Assumes 6 layers
        layers = [[],[],[],[],[],[]]
        n=0
        for key,value in self.drawObjects.iteritems():
            if len(value)<3:
                layers[2].append(value)
            else:
                layers[abs(value[2])].append(value)
            n=n+1    
    
        drawers=[]
        for layer in layers:
            drawers.extend(layer)        
        #for key,value in self.drawObjects.iteritems():
            
        for value in drawers:
        #    print value[0],value[1]
            if value[1]==None:
                value[0](canvas = self.__tmpCanvas)
            else:
            #    if not key == 'masterImage':
                value[0](canvas = self.__tmpCanvas,*value[1])
        old = self.__tmpCanvas
        self.__tmpCanvas = None
    def drawAsImage(self, event = None):
        """Don't use this, it doesn't work"""
        #pdb.set_trace()
        #draw_bmp = wx.EmptyBitmap(self.drawObjects['masterImage'][1].GetSize())
    #    canvas = wx.MemoryDC(draw_bmp)
        self.__tmpCanvas = wx.MemoryDC(self.drawObjects['masterImage'][1][0])
    #    self._tmpCanvas = wx.MemoryDC(draw_bmp)
        #pdb.set_trace()
        #self.__tmpCanvas.SelectObject(self.drawObjects['masterImage'][1])        
        #Assumes 6 layers
        layers = [[],[],[],[],[],[]]
        n=0
        for key,value in self.drawObjects.iteritems():
            if key == 'masterImage': continue
            if len(value)<3:
                layers[2].append(value)
            else:
                layers[abs(value[2])].append(value)
            n=n+1    
    
        drawers=[]
        for layer in layers:
            drawers.extend(layer)        
        #for key,value in self.drawObjects.iteritems():
            
        for value in drawers:
        #    print value[0],value[1]
            if value[1]==None:
                value[0](canvas = self.__tmpCanvas)
            else:
            #    if not key == 'masterImage':
                value[0](canvas = self.__tmpCanvas,*value[1])
        del self.__tmpCanvas
        return self.drawObjects['masterImage'][1][0].ConvertToImage()
        #wx.StaticBitmap(self, bitmap = self.drawObjects['masterImage'][1])    
        #self.Fit()
    def clearTmpDrawObjects(self):
        for key,value in self.drawObjects.iteritems():
            if len(value)==3:
                if value[2]<0:
                    del self.drawObjects[key]
                    
    def drawRectangle(self,start,end, pen = wx.WHITE_PEN,canvas=None):
        if canvas==None: canvas  = self.__tmpCanvas
#        print start, end
        canvas.SetPen(pen)
        canvas.SetBrush(wx.TRANSPARENT_BRUSH)
        canvas.DrawRectangle(start[0],start[1],end[0]-start[0],end[1]-start[1])
    def drawBitmap(self,bitmap,pos = None,canvas=None):
        if canvas == None: canvas = self.__tmpCanvas
        if pos==None:
            canvas.DrawBitmap(bitmap,0,0)
        else:
            canvas.DrawBitmap(bitmap,*pos)
            
    def drawLines(self,lines, pen = wx.WHITE_PEN, canvas=None):
        canvas.SetPen(pen)
        canvas.DrawLineList(lines)
    
    def drawLine(self,start,end,pen = wx.WHITE_PEN,canvas=None):
        canvas.SetPen(pen)
        canvas.DrawLine(start[0],start[1],end[0],end[1])
        
    def drawPointList(self,points,pen = wx.CYAN_PEN,canvas=None):
        canvas.SetPen(pen)
        canvas.DrawPointList(points)
    def setMouseHandlerData(self,mytype,myhandlers):
        self.mouseData = [mytype]
        if self.mouseData[0]=="DRAG":
            self.mouseData.extend([None,None]).extend(myhandlers)
        elif self.mouseData[1]=="POINT":
            self.mouseData.extend([None,myhandlers[0]])
    def resetMouseData(self,event=None):
        self.mouseData=[]
    def drawCrossHair(self,centre, pen = wx.WHITE_PEN, canvas= None):
        canvas.SetPen(pen)
        canvas.DrawLine(centre[0],0,centre[0],self.GetSize().GetHeight())
        canvas.DrawLine(0,centre[1],self.GetSize().GetWidth(),centre[1])
        
    def draw3DVolume(self, c1,c2,c3,c4,c5,c6,c7,c8, pen = wx.WHITE_PEN, canvas = None):
        """
        Implements drawing functionality to display a 3D bounding volume. This function deals only with image-
        space coordinates.
        
        @param corners: A 8 element list where each element is a 2 element list of (x,y) position in image space
        and the convention applied for the ordering are that the 2D points correspond to 3D points as follows:
        (x,y,z), (x,y,Z), (x,Y,z), (x,Y,Z), (X,y,z), (X,y,Z), (X,Y,z), (X,Y,Z) - please read this carefully
        if you want things to draw correctly.
        """
    
        print 'Draw3DVolume called with corners: '
        point_list = [ [c1[0], c1[1]], [c2[0], c2[1]], [c3[0], c3[1]], [c4[0], c4[1]], [c5[0], c5[1]], [c6[0], c6[1]], [c7[0], c7[1]], [c8[0], c8[1]] ]
        connection_list = [ [0,1], 
                            [0,2],
                            [0,4],
                            [1,3], 
                            [1,5],
                            [2,3],
                            [2,6],
                            [3,7],
                            [4,5],
                            [4,6],
                            [5,7],
                            [6,7] ]
        
        if canvas==None: canvas  = self.__tmpCanvas
        canvas.SetPen(pen)
        canvas.SetBrush(wx.TRANSPARENT_BRUSH)
        
        for line in connection_list:
            canvas.DrawLine(point_list[line[0]][0],point_list[line[0]][1],point_list[line[1]][0],point_list[line[1]][1])
        
    def addCrossHair(self, centre):
        self.drawObjects['cross'] = [self.drawCrossHair,(centre,)]
        self.drawSelf()
    def delCrossHair(self, centre = None):
        if self.drawObjects.has_key('cross'):
            del self.drawObjects['cross']
            
    def addDragRect(self,start,end):
        self.drawObjects['drag'] = [self.drawRectangle,(start,end)]
        self.drawSelf()
    def delDragRect(self):
        if self.drawObjects.has_key('drag'):
            del self.drawObjects['drag']
    def mouseHandler(self,event):
        if event.ButtonDown(wx.MOUSE_BTN_RIGHT):
            if hasattr(self,'popup') and callable(self.popup):
                self.popup(event.GetPosition().Get())
        if len(self.mouseData)==0:
            return None
        
        #if wx.self.mouseData[0] == "SELECT":
        #    self.mouseData[1](event.GetPosition.Get())
            
        if self.mouseData[0] == "CROSS":
            if not event.ButtonDown(wx.MOUSE_BTN_LEFT):
                self.addCrossHair(event.GetPosition().Get())
            else:
                self.delCrossHair(event.GetPosition().Get())
                self.mouseData = self.mouseData[1]
        if event.ButtonDown(wx.MOUSE_BTN_LEFT):
            #mouseData = ["DRAG" p1 p2 dragDrawHandler finalHandler]
            #mouseData = 
            if self.mouseData[0]=="DRAG":
                if self.mouseData[1] == None:
                    self.mouseData[1] = event.GetPosition().Get()
            elif self.mouseData[0] == "POINT":
                self.mouseData[1] = event.GetPosition().Get()
                self.mouseData[2](event.GetPosition().Get())
        if event.ButtonIsDown(wx.MOUSE_BTN_LEFT):
            if self.mouseData[0]=="DRAG":
                self.mouseData[3](self.mouseData[1],event.GetPosition().Get())    
        if event.ButtonUp(wx.MOUSE_BTN_LEFT):
            if self.mouseData[0]=="DRAG":
                self.mouseData[2] = event.GetPosition().Get()
                self.delDragRect()
                self.drawSelf()
                self.mouseData[4](*self.mouseData[1:3])
            elif self.mouseData[0] == "SELECT":
                self.mouseData[1](event.GetPosition().Get())
                
class DualImagePanel(ActivePanel):
    def __init__(self,parent,mysize):
        ActivePanel.__init__(self,parent,mysize)
        self.images = [None,None]
        self.offset = None
        self.magnify = True
    def whichImageAt(self,x):
        if x[0]<self.offset: return self.images[0]
        else: return self.images[1]
    def whichImageIndex(self,x):
        if x[0]<self.offset: return 0
        else: return 1
    def trueAt(self,x):
        if x[0]<self.offset: return self.images[0].getImageLoc(x)
        else: return self.images[1].getImageLoc(x)
    def setZoom(self,event=None):
        self.mouseData=["DRAG",None,None,self.addDragRect,self.zoom]
        return True
    def resetMaster(self,event=None):
        self.setImageDisplaySizes()
        self.setMasterImage()
        self.drawSelf()
        self.Refresh()
        self.Show(True)
        #self.Fit()
        self.SetSize(self.masterImage.GetSize())

    
    def fitAndDraw(self):
        self.drawSelf()
    #    self.Fit()
        self.SetSize(self.masterImage.GetSize())
        self.Show(True)
    
    def zoom(self,start,end):
        im = self.whichImageAt(start)
        im.setViewable(im.getImageLoc(start),im.getImageLoc(end))
        self.mouseData[1:3] = None,None
        self.delDragRect()
        self.setMasterImage()
        self.drawSelf()
        self.Refresh()
        self.SetSize(self.masterImage.GetSize())

        return True

    def setImageDisplaySizes(self):
        "Resets the images so that each image is visible in the panel"
        #All images are defined
        if len([im for im in self.images if im==None]) == 0:
            sizes = self.optimalRescale(*self.images)
            for i in range(len(self.images)):
                self.images[i].setDisplayBounds(*sizes[i])
                if i>0:
                    self.images[i].setOffset(sizes[i-1][0])
                else:
                    self.images[i].setOffset(0)
                self.images[i].setViewable()
            self.offset = sizes[0][0]
        else:
            im = [im for im in self.images if im!=None][0]
            im.setDisplayBounds(*self.GetSize().Get())
            im.setViewable(magnify = self.magnify)
            self.offset = im.GetSize().GetWidth()*im.scale
            
    def setMasterImage(self):
        ims = [im.getViewableImage() for im in self.images if im!=None] 
        masterImage = wx.EmptyImage(sum([im.GetWidth() for im in ims]),max([im.GetHeight() for im in ims]))
        masterImage.Paste(ims[0],0,0)
        if len(ims)>1:
            masterImage.Paste(ims[1],ims[0].GetWidth(),0)
            self.images[1].setOffset(ims[0].GetWidth())
        self.masterImage = masterImage.ConvertToBitmap()
        self.SetSize(self.masterImage.GetSize())
        self.drawObjects['masterImage'] = [self.drawBitmap,[self.masterImage],0]
        
    def displaySingleImage(self):
        im = [im for im in self.images if im!=None][0]
        
        im.setDisplayBounds(*self.GetSize().Get())
        im.setViewable()
        self.drawObjects['masterImage'] = [self.drawBitmap,[im.getViewableImage().ConvertToBitmap()],0]
        self.fitAndDraw()
    def optimalRescale(self,im1,im2,maxX = None,maxY = None):
        'Takes the two images (wxImage), and returns a (size1,size2) where the sizes are such that concat horizontally the sum is less than maxX and neither are greater maxY'
        
        if maxX==None:
            maxX,maxY = self.GetSize().Get()
        
        x = array((im1.GetWidth(),im2.GetWidth()),dtype = float32)
        y = array((im1.GetHeight(),im2.GetHeight()),dtype = float32)
        rescale = amin(vstack((0.5*maxX/x,maxY/y)),0)
        rescale[rescale>1] = 1
        if prod(rescale)<1 & (rescale==1).any() :
            bigi = where(rescale<1)[0][0]
            smalli = mod(bigi+1,2)
            maxX = maxX-x[smalli]
            rescale[bigi] = min(maxX/x[bigi],maxY/y[bigi])

        return ((rescale[0]*im1.GetWidth(),rescale[0]*im1.GetHeight()),(rescale[1]*im2.GetWidth(),rescale[1]*im2.GetHeight()))
    
    def getImagesDisplayFuncs(self):
        return (self.images[0].getDisplayLoc,self.images[1].getDisplayLoc)
    def getImageScales(self):
        return (self.images[0].getScale,self.images[1].getScale)
    def clearImages(self):
        self.images = []

    
class CheckItem(wx.MenuItem):
    """This class adds a radio type MenuItem, but with ability to 
    have no items checked"""
    def __init__(self,parent,ID,label,mygroup=None,realhandler=None):
        """mygroup is a dictionary that contains all of the CheckItems that belong to the group"
        realhandler is what is called after the item is checked"""
        wx.MenuItem.__init__(self,parent,ID,label,kind = 1)
        self.mygroup = mygroup
        if self.mygroup!=None:
            self.mygroup[ID] = self
        self.realhandler  = realhandler

    def checkItem(self,event):
        'This handler should be bound to the menu event'
        if self.mygroup != None:
            for item in self.mygroup.values(): item.Check(False)
        self.Check(True)
        if self.realhandler!=None:
            if self.realhandler(event)==None:
                self.Check(False)

class BasicMenu(wx.Menu):
    """This class simply provides a simple way to addMenuItems"""
    def __init__(self,parent):
        wx.Menu.__init__(self)
        self.parent = parent
    def addMenuItem(self,label,handler,mytype = None,mygroup = None):
        'adds a menuitem and binds the handler'
        ID = wx.NewId()
        if mytype == None:
            menuItem = self.Append(ID,label,"helpme")
        elif mytype == 'CHECK_ITEM':
            #menuItem = self.AppendRadioItem(ID,label)    
            menuItem = CheckItem(self,ID,label,mygroup,handler)
            self.AppendItem(menuItem)
            menuItem.Check(False)
            handler = menuItem.checkItem
        wx.EVT_MENU(self.parent,ID,handler)
        return menuItem

class FileSelector:
    """A simple extension class that contains a few file handling functions"""
    #def __init__(self,parent = None):
    #    wx.Frame.__init__(self,parent,wx.ID_ANY,title = title)
    def selectDirectory(self, mess = "Select a directory", defaultDir = ""):
        dirDialog = wx.DirDialog(self, message = mess, defaultPath = defaultDir)
        dirDialog.Fit()
        dirDialog.Show(True)
        if dirDialog.ShowModal() == wx.ID_OK:        
            dirname = dirDialog.GetPath()
            return dirname
        else: 
            return None
        
    def selectFile(self,message = "Select a file",
                    wildcard = wx.FileSelectorDefaultWildcardStr,
                    style = wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
                    defaultFile = "", defaultDir = ""):
        fileDialog = wx.FileDialog(self,message=message,defaultDir = defaultDir,defaultFile = defaultFile,wildcard=wildcard,style = style)
    
        fileDialog.Fit()
        fileDialog.Show(True)
        if fileDialog.ShowModal() == wx.ID_OK:
            if style == wx.FD_MULTIPLE:
                return fileDialog.GetPaths()
            else:
                return fileDialog.GetPath()
        else: 
            return None

class ImgFrame(wx.Frame):
    """This class provides a way to select from a set of images and to do something with them"""
    def __init__(self,parent,imgList,imageSelectHandlers =  None, sizer_width = 4, size = (415,400)):
        wx.Frame.__init__(self,parent,wx.ID_ANY)
        self.imgList = imgList
        
        self.imageSelectHandlers = imageSelectHandlers
        self.sizer_width = sizer_width
        self.SetSize(size)
        #self.Fit()
        self.size = size
        self.__id2img = self.populate()
        self.Show(True)
    def populate(self):
        panel = wx.ScrolledWindow(self,wx.ID_ANY,size= self.size)
        panel.EnableScrolling(True,True)
        panel.SetScrollbars(5,5,50,50)
        sizer = wx.GridSizer()
        id2img = dict()
        for img,imhandler in zip(self.imgList, self.imageSelectHandlers):
            tmpim = wx.StaticBitmap(panel,wx.ID_ANY,img)
            id2img[tmpim.GetId()] = img
            sizer.Add(tmpim)
            #if hasattr(self.imageSelectHandlers,'len'):
            #    tmpim.Bind(wx.EVT_LEFT_DOWN,self.imageSelectHandlers[0])
            #    tmpim.Bind(wx.EVT_RIGHT_DOWN,self.imageSelectHandlers[1])
            #else:
            tmpim.Bind(wx.EVT_LEFT_DOWN, imhandler)
        sizer.SetCols(self.sizer_width)
        sizer.SetRows(1+len(self.imgList)/self.sizer_width)
        panel.SetSizer(sizer)
        panel.SetSize(self.size)
        return id2img
    def getImgFromId(self,Id):
        return self.__id2img[Id]


def unravel_dict(mydict, mylist, label=""):
    """Returns a list of [(label, value)], which is an unravelling of a 
    dictionary that may contain dicts.
    
    ((a.b.c),value) is mydict[a][b][c]
    """
    for key, value in mydict.iteritems():
        if len(label) == 0:
            tlabel = key
        else:
            tlabel = label + "." + key
        if isinstance(value, dict):
            unravel_dict(value,mylist,tlabel)
        else:
            mylist.append((tlabel, value))

def ravel_list(lst):
    """Takes a list of (key,value) tuples and returns a dictionary, that is possibly
    nested if key contains periods.
    """
    mydict = {}
    for label, value in lst:
        keys = label.split(".")
        tdict = mydict
        for key in keys[:-1]:
            try:
                tdict = tdict[key]
            except:
                tdict[key] = {}
                tdict = tdict[key]
                
        tdict[keys[-1]] = value
    return mydict

#def set_last_name( name ):
#    global last_name
#    last_name = name
#            
class ParameterPanel(wx.Panel):
    """Provides a panel to input default_parameters
    """
    def __init__(self,parent,parameters,whendone=None,master =None , box_size = 90):
        """parameters is a dictionary, whendone is what to do when the default_parameters
         have been input correctly 
    
        master allows sets of default_parameters choices, and be the dictionary of dictionaries {label:dict1,label:dict2}
        """
        wx.Panel.__init__(self,parent)
        self.default_parameters = parameters
        panelsizer = wx.BoxSizer(wx.VERTICAL)
        parasizer = wx.FlexGridSizer(len(parameters), 2, vgap=3)
        self.getValue = {} #This is a list of functions that access txtctrl values
        self.setValue = {}
        
        #for i,p in enumerate(default_parameters):
        self.paralist =[]
        unravel_dict(self.default_parameters, self.paralist,"")
        for label,value in self.paralist:
            parasizer.Add(wx.StaticText(self,label = label))
            
#            if label == 'name':
#                value = [ 'bottle', 'stapler', 'mug', 'shoe', 'bowl','mouse', 'keyboard', 'monitor' ]
#            
            if isinstance(value,list):
#                if label == 'name':
#                    global last_name
#                    lstbox = wx.ComboBox(self,choices =  [str(v) for v in value], style = wx.CB_DROPDOWN, value=last_name)
#                else:
                lstbox = wx.ComboBox(self,choices =  [str(v) for v in value],
                            style = wx.CB_DROPDOWN, value = str(value[0]))
                #self.Bind(wx.EVT_COMBOBOX, lambda x: self.)
                self.getValue[label] = lstbox.GetValue
                parasizer.Add(lstbox)
            else:
                txtctrl = wx.TextCtrl(self,value = str(value),size = wx.Size(box_size,-1))
                self.getValue[label] = txtctrl.GetValue
                self.setValue[label] = txtctrl.SetValue
                parasizer.Add(txtctrl)
        if not master==None:
            #This if for an older version of code, it might not work
            lstbox = wx.ComboBox(self,choices = master.keys(),style = wx.CB_DROPDOWN)
            parasizer.Add(lstbox)
            
            self.Bind(wx.EVT_COMBOBOX,self.changeParameterDefault)
            self.combobox = lstbox
        #parasizer.SetFlexibleDirection(wx.HORIZONTAL)
        self.master = master    
        if whendone == None:
            whendone = lambda x: x
        panelsizer.Add(parasizer)    
        self.whendone = whendone
        self.SetSizer(panelsizer)
        self.Fit()
        self.Show(True)    
        
    def changeParameterDefault(self,event=None):
        value = self.combobox.GetValue()
        newparalist = unravel_dict(self.master[value])
        for label, value in newparalist:
            try:
                self.setValue[label] = value
            except:
                pass
            
#        for k,v in self.master[value].iteritems():
#            self.setValue[k]( str(v))
        
    def addButtons(self):
        buttons = ButtonPanel(self)
        buttons.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        buttons.addButtonToSizer("Ok",self.checkAndReturn)
        buttons.addButtonToSizer("Cancel",self.cancel)
        
        self.GetSizer().Add(buttons)
        self.Fit()
        self.Show(True)    
    
    def getParameters(self):
        """Returns a dictionary, possible nested, from the panel
        """
        newlist =  [(k, self.getValue[k]()) for k,v in self.paralist]
        return ravel_list(newlist)
    
    def checkAndReturn(self,event = None):
        """Checks to see if the values are valid and returns them if true"""
        values = range(len(self.default_parameters))
        for i,p in enumerate(self.default_parameters):
            value = self.getValue[p[0]]()
            if len(p)>2:
                isok = p[2](p[0],value)
                if not isok==True:
                    wx.MessageDialog(self,message = isok,style = wx.OK | wx.CENTRE).ShowModal()
                    print isok
                    return None
        return self.whendone(True)    
            
    def cancel(self,event):
        return self.whendone(False)
        
class ParameterFrame(wx.Frame):
    def __init__(self,parent,parameters):
    
        wx.Frame.__init__(self,parent,pos = parent.GetScreenPosition() +(100,100))
        panel = ParameterPanel(self,parameters,self.whendone)
        panel.addButtons()

        self.Fit()
        self.Show(True)
    def whendone(self,state):
        
        self.Destroy()
            

class GridImage(wx.Image):    
    def __init__(self, imagename, scale = 1):
        wx.Image.__init__(self,imagename)
        self.imagename = imagename
        self.scale = scale
        if scale != 1:
            self.Rescale(int(self.GetWidth()*scale),int(self.GetHeight()*scale))
  
        
class GridImagePanel(wx.ScrolledWindow):
    """This takes takes an image set and produces a tiled window
    
    Members:
    panels is a list of ActivePanels, panel[i] has resized image of imagenames
    img_dict is the actual images if they are already loaded (saves expensive loading
    and resizing if images are large)
    
    """
    ncols = 2
    def __init__(self, parent, imagenames = None, 
                 size  = IMAGE_PANEL_DIM, img_dict = {}, ncols = 2):
        
        wx.ScrolledWindow.__init__(self, parent)
        self.EnableScrolling(True,True)
       
        self.imagenames = imagenames
        if not isinstance(size, wx.Size):
            size = wx.Size(*size)
        self.size = size
       # self.SetClientSize(size)
        self.panels = []
        self.img_dict = img_dict
#        print "1 ",self.GetSize(), self.GetClientSize()
        self.ncols = ncols
        self.populate()
        
    def populate(self):

        self.EnableScrolling(False,True)
       # self.SetScrollbars(0,5,0,50)
        def rescale(imsize, maxsize = self.size.GetWidth()/self.ncols):
            rs  = max(imsize[0]/float(maxsize), 1)
            return 1/rs, (int(imsize[0]/rs), int(imsize[1]/rs))
        panels = []
        sizer = wx.GridSizer(vgap = 0,hgap =0)
        for imagename in self.imagenames:
            if self.img_dict.has_key(imagename):
                im = self.img_dict[imagename]
                rs = im.scale
            else:    
                tmpim = wx.Image(imagename)
                rs, thesize = rescale(tmpim.GetSize().Get())
                im = GridImage(imagename, rs)
                self.img_dict[imagename] = im
            bitmap = im.ConvertToBitmap()
            panel = ActivePanel(self,bitmap.GetSize().Get())
            panel.scale = rs
            panel.drawObjects['masterImage'] = [panel.drawBitmap,[bitmap],0]
            panel.Bind(wx.EVT_PAINT,panel.drawSelf)
            panel.SetMinSize(bitmap.GetSize())
            sizer.Add(panel)
            panels.append(panel)
        sizer.SetCols(self.ncols)
        self.SetSizer(sizer)
        #NOTE: This was tough to get right, so think about it before changing
        self.Fit()
        self.SetClientSize(map(min, self.size.Get(), sizer.GetSizeTuple()))
        size = self.GetClientSize()
        if self.GetClientSize().GetHeight() < sizer.GetSize().GetHeight():
            self.SetScrollbars(0,5,0,50)
            self.Fit()
            self.SetClientSize(size)
        self.panels = panels
        return panels
    
#These are functions that I frequently need that involve wx


#def indicesAsImage(index):
#    """Returns a a visual datum image, where only those index[i,j] are set to 1"""
#    dim = index.max(axis=0)+5
#    arr = zeros(dim)
#    arr[index[:,0],index[:,1]] = 1
#    return visual.VisualDatum(image = numpy2wx(arr))
#            
def numpy2wx(im):    
    """Takes a 2d numpyarray and produces a wx im by spreading the values over the entire range 0 to 255. Can take a 3 array as well that specifies the values for each colour channel."""
    buff = uint8(255*float32(im.flatten())/float32(im.max()))
    if im.ndim == 2: #Resumeably a grey-level image
        
        buff = vstack((buff,buff,buff)).T.copy()
        return wx.ImageFromData(im.shape[1],im.shape[0],buff)
    if im.ndim==3:
        return  wx.ImageFromData(im.shape[1],im.shape[0],buff)




