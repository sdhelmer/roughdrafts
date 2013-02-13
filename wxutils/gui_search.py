import pdb
import os
import sys

import wx
import wxutils as wxu
import numpy as np

sys.path.append('../oai')
import oai_tools

opj = os.path.join

max_dim = 1024

class ImageFlash:
    def __init__(self, img_name):
        self.img_name = img_name
        
    def flash(self, event = None):
        self.frame = wx.Frame(None)
#        sizer = wx.BoxSizer(wx.VERTICAL)
        img = wx.Image(self.img_name)
        size = np.array(img.GetSize(), dtype = np.float32)
        size = size * (max_dim/max(size))
        img.Rescale(*list(np.int32(size)))
        bitmap = wx.StaticBitmap(self.frame, 
                 bitmap = img.ConvertToBitmap())
        self.frame.Fit()
        self.frame.Show(True)


class CheckList(wx.Panel):
    """Provides a panel that includes a set of check list boxes."""
    def __init__(self, parent, txt_list = None, txt_checks = None):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.check_boxes = []
        self.populate(txt_list, txt_checks)
        
    def populate(self, txt_list = None, txt_checks = None):
        if txt_list is None: return
        if txt_checks is None:
            txt_checks = [True]*len(txt_list)
 
        for txt, check in zip(txt_list, txt_checks):
            check_box = wx.CheckBox(self, label = txt)
            check_box.SetValue(check)
            self.GetSizer().Add(check_box)
            self.check_boxes.append(check_box)
            
    def add_txt(self, txt):
        """Add a new check box with the txt to the list"""
        check_box = wx.CheckBox(self, label = txt)
        check_box.SetValue(True)
        self.GetSizer().Add(check_box)
        self.check_boxes.append(check_box)
        self.parent.Fit()
        
    def get_checked_entries(self, event = None):
        """Returns a list containing the txt of the checkboxes if they are 
        checked."""
        txt_list = []
        for check_box in self.check_boxes:
            if check_box.GetValue():
                txt_list.append(check_box.GetLabel())
        return txt_list
    
    def get_all_entries(self, event = None):
        """Returns a dictionary, where the keys are the txt and the values
        are booleans according to the checkmarks."""
        check_dict = {}
        for check_box in self.check_boxes:
            check_dict[check_box.GetLabel()] = check_box.GetValue()
        return check_dict
    
class TagFrame(wx.Frame):
    """Provides a frame that includes a window to add new tags and the ability
    to delete old ones"""
    def __init__(self, current_tags = None, set_tags_func = None, current_checks = None,
                 add_tags = False):
        wx.Frame.__init__(self, None)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
#        self.tags = [] if current_tags is None else current_tags
        self.set_tags = set_tags_func 
        if add_tags:
            self.text_box = wx.TextCtrl(self, size = (300,50), 
                                    style = wx.TE_PROCESS_ENTER)
            self.text_box.Bind(wx.EVT_TEXT_ENTER, self.txt_handler)
            self.GetSizer().Add(self.text_box)
        self.check_list = CheckList(self, current_tags, current_checks)
        self.GetSizer().Add(self.check_list)
        button_panel = wxu.ButtonPanel(self)
        button_panel.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        button_panel.add_button("", self.ok_handler, wxid = wx.ID_OK)
        button_panel.add_button("", self.Close, wxid = wx.ID_CANCEL)
        self.GetSizer().Add(button_panel, flag = wx.ALIGN_CENTER)
        self.Fit()
    def txt_handler(self, event):
        """Adds a new check box to our list of tags."""
        self.check_list.add_txt(self.text_box.GetValue())
        self.text_box.SetValue("")
    def ok_handler(self, event):
        """Closes the window and sets the parents tags"""
#        txt_list = self.check_list.get_checked_entries()
#        self.parent.set_tags(txt_list) #Maybe I should pass in the function
        self.set_tags(self.check_list.get_checked_entries())
        self.Close()

  
class SearchApp(wxu.ImageFrame, oai_tools.Searcher):
    
    def __init__(self, parent, query_paths, db_paths, 
                 image_ext = 'cropped_thumbnail'):
        oai_tools.Searcher.__init__(self, db_paths)
        self.queries = self.load_queries(query_paths)
        for query in self.queries.itervalues():
            query['tags'] = []
        self.handlers = {}
        self.image_ext = image_ext
        
        image_paths = []
        image2query = {}
        for query_path in query_paths:
            image_path = opj(query_path, self.image_ext)
            self.handlers[image_path] = [(wx.EVT_LEFT_DOWN, self.search),
                    (wx.EVT_RIGHT_DOWN, self.tag_image)]
            image_paths.append(image_path)
            image2query[image_path] = query_path
        self.image2query = image2query
        wxu.ImageFrame.__init__(self, parent, image_paths, self.handlers)
        self.tags = ['bad_all', 'bad_colour']
        self.set_menu()
        self.Show(True)
    
    def set_menu(self):
        menu_bar = wx.MenuBar()
        menu = wxu.BasicMenu(self)
        menu.add_menu_item('Add tags', self.add_tag )
        menu.add_menu_item('Save tags', self.save_tags)
        menu_bar.Append(menu,'Options')
        self.SetMenuBar(menu_bar)

    def save_tags(self, event):
        dialog = wxu.FileSelector()
        directory = dialog.select_directory()
        for tag in self.tags:
            fp = open(opj(directory,tag),'w') #maybe should be append
            for query_key, query_data in self.queries.iteritems():
                if tag in query_data['tags']:
                    q_id = os.path.split(query_key)[1]
                    fp.write(q_id + '\n')
            fp.close()
                    
    
    def add_tag(self, event):
        tag_frame = TagFrame(self.tags, self.set_tags, add_tags = True)
        tag_frame.Show(True)
        
    def set_tags(self, tags):
        self.tags = tags
    
    def tag_image(self, event):
        query_key = self.image2query[self.get_selected_image(event)]
        query = self.queries[query_key]
        tag_checks = [tag in query['tags'] for tag in self.tags]
        print "OLD: ", query['tags']
        def change_tags(new_tags):
            query['tags'] = new_tags
            print "New: ", query['tags'] 
            
        tag_frame = TagFrame(self.tags, change_tags, tag_checks)
        tag_frame.SetPosition(
                    np.int32( event.GetEventObject().GetScreenPosition()) +
                    np.int32(event.GetPosition()) + [20,0])
        tag_frame.Show(True)
      
    def popup(self, event):
        query_key = self.image2query[self.get_selected_image(event)]
        query = self.queries[query_key]
        
#        self.PopupMenu(menu)
        
    def search(self, event):
        query = self.image2query[self.get_selected_image(event)]
        results = oai_tools.Searcher.search(self, self.queries[query])
#        result_frame = wxu.ImageFrame(None)
        db_image_paths = []
        for i in range(20):
            score, db_path = results[i]
            db_image_paths.append(opj(db_path, self.image_ext))
        result_frame = wxu.ImageFrame(None, db_image_paths)
        result_frame.Show(True)
            
  
def abs_listdir(source):
    return [opj(source, p) for p in os.listdir(source)]          
        
if __name__ == '__main__':
    
#    ~/OculusAI/Datasets/data_trans/oaidata/
#    ~/OculusAI/Datasets/data_trans/queries
    db_source = sys.argv[1]
    query_source = sys.argv[2]
    
    db_paths = abs_listdir(db_source)[:1000]
    query_paths = abs_listdir(query_source)
    
    app = wx.PySimpleApp()
    frame = SearchApp(None, query_paths, db_paths)
#    frame.Show(True)
    app.MainLoop()
    
    
    