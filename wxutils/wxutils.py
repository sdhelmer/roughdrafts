"""
Short

This modules contains some generic extensions for wx, tools that I may want to reuse,
 but also don't want to have cluttering up the more research part of my code base.
 
 I probably should document this further, but my knowlege is a bit hazy at the moment.

"""
import sys
import wx
from numpy import *
import pdb
imgexts = '(*.jpg;*.JPG;*.pgm;*.png)|*.jpg;*.JPG;*.pgm;*.png|All (*)|*'

IMAGE_PANEL_DIM = (700,750) #Used by the GridImage stuff

class ButtonPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        
    def add_button(self, mylabel, handler, sizer=None, wxid = wx.ID_ANY):
        "Adds a button, along with it's handler to a sizer"
        button = wx.Button(self,wxid,label = mylabel)
        button.Bind(wx.EVT_BUTTON, handler)
        if sizer == None: self.GetSizer().Add(button,1)
        else:    sizer.Add(button,1)
        return button

class BasicMenu(wx.Menu):
    """This class simply provides a simple way to addMenuItems"""
    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent
    def add_menu_item(self, label, handler, mytype = None, mygroup = None):
        'adds a menuitem and binds the handler'
        ID = wx.NewId()
        if mytype == None:
            menuItem = self.Append(ID, label)

        wx.EVT_MENU(self.parent, ID, handler)
        return menuItem

class FileSelector:
    """A simple extension class that contains a few file handling functions"""
    def __init__(self, parent=None):
        self.parent = parent
    def select_directory(self, mess = "Select a directory", defaultDir = ""):
        dir_dialog = wx.DirDialog(self.parent, message = mess, 
                                  defaultPath = defaultDir)
        dir_dialog.Fit()
        dir_dialog.Show(True)
        if dir_dialog.ShowModal() == wx.ID_OK:        
            dirname = dir_dialog.GetPath()
            return dirname
        else: 
            return None
        
    def select_file(self,message = "Select a file",
                    wildcard = wx.FileSelectorDefaultWildcardStr,
                    style = wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
                    defaultFile = "", defaultDir = ""):
        file_dialog = wx.FileDialog(self.parent, message=message,
                                     defaultDir = defaultDir, 
                                     defaultFile = defaultFile, 
                                     wildcard=wildcard, style = style)
    
        file_dialog.Fit()
        file_dialog.Show(True)
        if file_dialog.ShowModal() == wx.ID_OK:
            if style == wx.FD_MULTIPLE:
                return file_dialog.GetPaths()
            else:
                return file_dialog.GetPath()
        else: 
            return None

class ImageFrame(wx.Frame):
    """This class provides a way to select from a set of images and to do something with them"""
    def __init__(self, parent, image_paths, image_handlers =  None, 
                 sizer_width = 4, size = (615,500)):
        wx.Frame.__init__(self,parent,wx.ID_ANY)
        
        self.image_paths = image_paths
        self.image_handlers = image_handlers
        self.sizer_width = sizer_width
        self.SetSize(size)
        self.size = size
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        self._id2img = self.populate()
#        self.Show(True)
        
    def populate(self):
        panel = wx.ScrolledWindow(self, wx.ID_ANY, size= self.size)
        panel.EnableScrolling(True,True)
        panel.SetScrollbars(5,5,50,50)
        sizer = wx.GridSizer()
        id2img = dict()
#        for img, imhandler in zip(self.img_list, self.image_handlers):
        panel_images = []
        for image_path in self.image_paths:
            img = wx.Image(image_path).ConvertToBitmap()
            tmpim = wx.StaticBitmap(panel, bitmap =  img)
            id2img[tmpim.GetId()] = image_path
            sizer.Add(tmpim)
            panel_images.append(tmpim)
            if self.image_handlers is None:
                continue
            for evt_type, handler in self.image_handlers[image_path]:
                tmpim.Bind(evt_type, handler)

        sizer.SetCols(self.sizer_width)
        sizer.SetRows(1+len(self.image_paths)/self.sizer_width)
        panel.SetSizer(sizer)
        panel.SetSize(self.size)
        self.GetSizer().Add(panel)
        return id2img
    def get_selected_image(self, event):
        return self._id2img[event.GetEventObject().GetId()]
    
    def get_img_from_id(self, id):
        return self._id2img[id]

class ActivePanel(wx.Panel):
    def __init__(self, parent, img, size = wx.DefaultSize):
        wx.Panel.__init__(self, parent, size = img.GetSize())
        self.draw_objects = {} #a dictionary that should contain key, values, where values are value[0] is a handler, and value[1] is it's arguments
        self.add_base_image(img)
        self._canvas = None
        self.mouse_data = None
        self.Bind(wx.EVT_PAINT, self.draw_self)
        self.Bind(wx.EVT_LEFT_DOWN, self.drag_line )
        self.Bind(wx.EVT_MOTION, self.drag_line)
        
    def add_base_image(self, img):
        bitmap_img = img.ConvertToBitmap()
        self.draw_objects['master'] = (self.draw_bitmap, (bitmap_img,), 0)
        
    def draw_self(self, event = None):
        self._canvas = wx.PaintDC(self)
        layers = [[],[],[],[]]
        
        for key, value in self.draw_objects.iteritems():
            if len(value) < 3:
                layers[1].append(value)
            else:
                layers[abs(value[2])].append(value)
                
        all_layers =[]
        for layer in layers: all_layers.extend(layer)
        
        for value in all_layers:
            if value[1] is None:
                value[0]()
            else:
                value[0](*value[1])
        self._canvas = None
        
    def draw_handler_map(self, event):
        w,h = self.GetSize()
        bmp = wx.EmptyBitmap(w,h)
        
        self._canvas = wx.MemoryDC()
        self._canvas.SelectObject(bmp)
        layers = [[],[],[],[]]
        
        for key, value in self.draw_objects.iteritems():
            if key == 'master': continue
            if len(value) < 3 or value[2] == None:
                layers[1].append(value)
            else:
                layers[abs(value[2])].append(value)
                
        all_layers =[]
        for layer in layers: all_layers.extend(layer)
        
        for value in all_layers:
            if value[1] is None:
                value[0]()
            else:
                value[0](*value[1])
        self._canvas.SelectObject(wx.NullBitmap)
        bmp.SaveFile('my_test.png',wx.BITMAP_TYPE_PNG)
        
    def draw_line(self, start, end, pen = wx.WHITE_PEN):
        self._canvas.SetPen(pen)
        self._canvas.DrawLine(start[0], start[1], end[0], end[1])
        
    def draw_circle(self, centre, radius, pen = wx.WHITE_PEN):
        self._canvas.SetPen(pen)
        self._canvas.DrawCirlce(centre[0], centre[1], radius)
        
    def draw_bitmap(self, bitmap, pos = None):
        if pos is None:
            self._canvas.DrawBitmap(bitmap, 0, 0)
        else:
            self._canvas.DrawBitmap(bitmap, *pos)
            
    def drag_line(self, event):
        if not event.ButtonIsDown(wx.MOUSE_BTN_LEFT): 
            return
        if self.mouse_data is None:
            self.draw_objects['drag'] = [self.draw_line, 
                    (event.GetPosition().Get(), event.GetPosition().Get())]
            self.mouse_data = event.GetPosition().Get()
        else:
            self.draw_objects['drag'] = [self.draw_line, 
                    (self.mouse_data, event.GetPosition().Get())]
        self.Refresh()
                        
def numpy2wx(im):    
    """Takes a 2d numpyarray and produces a wx im by spreading the values over
    the entire range 0 to 255. Can take a 3 array as well that specifies the 
    values for each colour channel."""
    buff = uint8(255*float32(im.flatten())/float32(im.max()))
    if im.ndim == 2: #Resumeably a grey-level image
        buff = vstack((buff,buff,buff)).T.copy()
        return wx.ImageFromData(im.shape[1], im.shape[0], buff)
    if im.ndim==3:
        return  wx.ImageFromData(im.shape[1], im.shape[0], buff)



if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = wx.Frame(None)
    sizer = wx.BoxSizer(wx.VERTICAL)
    frame.SetSizer(sizer)
    img = wx.Image('/Users/loon/Desktop/ScottHelmer.jpeg')

    panel = ActivePanel(frame, img, size = img.GetSize())
    panel.add_base_image(img)
    sizer.Add(panel)
    button = wx.Button(frame, wx.ID_ANY, label = 'Save' )
    button.Bind(wx.EVT_BUTTON, panel.draw_handler_map)
    sizer.Add(button)
    frame.Fit()
    frame.Show(True)
    
    frame.SetSizer(sizer)
    app.MainLoop()
    


