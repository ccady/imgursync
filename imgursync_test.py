# apt-get install python3-tk
# used for windowing
import tkinter as tk
#from tkinter import ttk # also import the themed tkinter for good looking widgets (not obligatory)
import sys

from tkinter.font import Font
#from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from tkinter import messagebox

# pip3 install imgurpython
# used for imgur access
from imgurpython import ImgurClient

# does not need any installation 
# necessary to expand path for config file
import os.path

# does not need any installation 
import configparser

# does not need any installation 
# used to get authorization from imgur web site
import webbrowser
    
class MainWindow:
    def __init__(self, parent):
        
        font_default = Font(family = "default", size = "10")
        font_status = Font(family = "default", size = "10", slant = 'italic')
        font_contents = font_default
        
        self.images = {}
        self.albums = {}

        self.parent = parent
        self.parent.title(os.path.basename(__file__))
        
        self.string_status = tk.StringVar()
        
        self.read_config()

        self.frame_id = tk.Frame(parent)
        self.frame_id.pack(anchor = tk.W)

        #self.frame_buttons = tk.Frame(parent)
        #self.frame_buttons.pack(anchor = tk.W)

        #self.button_readconfig = tk.Button(self.frame_buttons, text = "Do work", command = self.do_work)
        #self.button_readconfig.pack(side = tk.LEFT, padx = 5, pady = 2)

        # this should come before the contents, so that it does not shrink first when resizing windows
        # put this into the pack manager before the contents so it does not resize until the contents have
        self.label_status = tk.Label(parent, textvariable = self.string_status, font = font_status, bd = 1, relief = tk.SUNKEN, justify = tk.LEFT, anchor = tk.W)
        self.label_status.pack(side = tk.BOTTOM, fill = tk.BOTH)        

        # contents
        columnnames = ['id', 'type']
        displaycolumnnames = []

        self.treeview = ttk.Treeview(parent, selectmode = 'browse', columns = columnnames, displaycolumns = displaycolumnnames) # , height = 10, show = 'headings'
        self.treeview.bind('<Double-Button-1>', self.treeview_doubleclick)
        self.treeview.bind('<Button-3>', self.treeview_rightclick)
        self.treeview.bind('<<TreeviewOpen>>', self.populate_album)
        for columnname in columnnames:
            self.treeview.heading(columnname, text = columnname)
            self.treeview.column(columnname, stretch = True)
        self.treeview.pack(anchor = tk.W, fill = tk.BOTH, expand = True)
        
        # immediately populate tree
        self.do_work()

        # create a menu
        self.menu_popup = tk.Menu(parent, tearoff = 0)
        self.menu_popup.add_command(label="Get Info", command = self.get_info)
        self.menu_popup.add_command(label="View", command = self.view)
        self.menu_popup.add_command(label="Edit", command = self.edit)

        self.menu_popup.bind("<FocusOut>", self.menu_close) # keyboard focus
        self.menu_popup.bind("<Leave>", self.menu_close) # mouse focus
        

    def treeview_doubleclick(self, event):
        item = self.treeview.selection()[0]
        #print("you double-clicked ", self.treeview.item(item, "values"))
        iid = self.treeview.identify_row(event.y)
        if iid:
            # mouse pointer over item
            self.treeview.selection_set(iid)
            item = self.treeview.selection()[0]
            print("{0} {1} you double-clicked {2}".format(event.x, event.y, self.treeview.item(item, "values")))
        else:
            # clear selection
            #self.treeview.selection_clear()
            if len(self.treeview.selection()) > 0:
                self.treeview.selection_remove(self.treeview.selection()[0])

    def treeview_rightclick(self, event):
        # select row under mouse
        iid = self.treeview.identify_row(event.y)
        if iid:
            # mouse pointer over item
            self.treeview.selection_set(iid)
            item = self.treeview.selection()[0]
            print("{0} {1} you right-clicked {2}".format(event.x, event.y, self.treeview.item(item, "values")))
            self.menu_popup.post(event.x_root - 5, event.y_root - 5)
        else:
            # clear selection
            #self.treeview.selection_clear()
            if len(self.treeview.selection()) > 0:
                self.treeview.selection_remove(self.treeview.selection()[0])

    def get_info(self):
        item = self.treeview.selection()[0]
        id = self.treeview.set(item, 'id')
        if self.treeview.set(item, 'type') == 'album':        
            tk.messagebox.showinfo("album info", vars(self.albums[id]))
        if self.treeview.set(item, 'type') == 'image':
            tk.messagebox.showinfo("image info", vars(self.images[id]))

    def view(self):
        item = self.treeview.selection()[0]
        id = self.treeview.set(item, 'id')
        if self.treeview.set(item, 'type') == 'album':        
            self.open_url(self.client.get_album(id).link)
        if self.treeview.set(item, 'type') == 'image':        
            self.open_url(self.client.get_image(id).link)

    def edit(self):
        item = self.treeview.selection()[0]
        id = self.treeview.set(item, 'id')
        if self.treeview.set(item, 'type') == 'album':
            print(vars(self.albums[id]))
            AlbumEditor(self.parent, self.albums[id])
        if self.treeview.set(item, 'type') == 'image':        
            print(vars(self.images[id]))
            ImageEditor(self.parent, self.images[id])

    def menu_close(self, event):
        self.menu_popup.unpost()

    def open_url(self, url):
        webbrowser.open(url, new = 0, autoraise = True)

    def set_status(self, message):
        print(message)
        self.string_status.set(message)
            
    def lock_minimum_size(self):
        self.parent.update() # make sure all the info from previous widget placements has been recalculated
        self.parent.minsize(self.parent.winfo_width(), self.parent.winfo_height())

    def create_client(self):
        try:
            self.client = ImgurClient(self.config['client']['id'], self.config['client']['secret'])
            return True
        except:
            self.set_status('Failed to create client using saved credentials. Run register program.')
            print(sys.exc_info(), file = sys.stderr)
            return False

    def authorize(self):
        try:
            self.client.set_user_auth(self.config['credentials']['access_token'], self.config['credentials']['refresh_token'])
            return True
        except:
            self.set_status('Failed to authorize using saved credentials. Run authorize program.')
            print(sys.exc_info(), file = sys.stderr)
            return False

    def write_config(self):
        try:
            # write the configuration back to the file it came from
            with open(self.configfilename, 'w') as configfile:    # save
                self.config.write(configfile)
            self.set_status('Successfully wrote config file.')
            return True

        except:
            self.set_status('Failed to write config file.')
            print(sys.exc_info(), file = sys.stderr)
            return False

    def do_work(self):
        for album in self.client.get_account_albums('me'):
            self.albums[album.id] = album
            album_title = album.title if album.title else 'Untitled'
            rowid = self.treeview.insert('', tk.END, text = album_title, values = [album.id, 'album'])
            self.treeview.insert(rowid, tk.END, text = 'dummy', values = ['', 'dummy']) # makes the item "openable"
                
    def populate_album(self, event):
        selectednode = self.treeview.focus()
        if self.treeview.set(selectednode, 'type') == 'album':
            for child in self.treeview.get_children(selectednode):
                if self.treeview.set(child, 'type') == 'dummy':
                    self.treeview.delete(*self.treeview.get_children(selectednode))
                    for image in self.client.get_album_images(self.treeview.set(selectednode, 'id')):
                        self.images[image.id] = image
                        image_name = image.name if image.name else 'Unnamed'
                        self.treeview.insert(selectednode, 0, text = image_name, values = [image.id, 'image']) # makes the item "openable"

    def read_config(self):
        try:
            self.config = configparser.ConfigParser() # don't know what to do if this fails.
            configfiles = self.config.read(['.imgursyncconfig', os.path.expanduser('~/.imgursyncconfig')])
            # Save the name of the first file that was successfully read
            if len(configfiles) > 0:
                self.configfilename = configfiles[0]
            else:
                self.configfilename = '.imgursyncconfig'
            self.set_status('Successfully read config file. File is ' + self.configfilename)

        except:
            self.set_status('Failed to read config file.')
            print(sys.exc_info(), file = sys.stderr)
            return False

        # config file has been read.  test creation and authorization of client.
        if self.create_client():
            self.authorize()
            
class AlbumEditor:
    def __init__(self, parent, album):

        self.album  = album
        self.parent = tk.Toplevel(parent)
        self.parent.title("album " + album.id)
        
        editfields = ['title', 'description', 'link']
        
        row = 0
        for editfield in editfields:
            row = row + 1
            label = tk.Label(self.parent, text = editfield)
            label.grid(sticky = tk.W, row = row, column = 0)
            entry = tk.Entry(self.parent)
            entry.insert(0, str(getattr(album, editfield)))
            entry.grid(sticky = (tk.W + tk.E), row = row, column = 1)
            
        self.button_done = tk.Button(self.parent, text = 'Done', command = self.done)
        row = row + 1
        self.button_done.grid(sticky = tk.W, row = row, column = 0)
    
    def done(self):
        self.parent.destroy()

class ImageEditor:
    def __init__(self, parent, image):

        self.image = image
        self.parent = tk.Toplevel(parent)
        self.parent.title("image " + image.id)
        
        editfields = ['title', 'description', 'link', 'name', 'type']
        
        row = 0
        for editfield in editfields:
            row = row + 1
            label = tk.Label(self.parent, text = editfield)
            label.grid(sticky = tk.W, row = row, column = 0)
            entry = tk.Entry(self.parent)
            entry.insert(0, str(getattr(image, editfield)))
            entry.grid(sticky = (tk.W + tk.E), row = row, column = 1)
            
        self.button_done = tk.Button(self.parent, text = 'Done', command = self.done)
        row = row + 1
        self.button_done.grid(sticky = tk.W, row = row, column = 0)
    
    def done(self):
        self.parent.destroy()

#        self.label_id = tk.Label(self.parent, text = image.id)
#        self.label_id.pack()
        
#        self.entry_name = tk.Entry(self.parent, text = image.name)
#        self.entry_name.pack()

if __name__ == '__main__':
    root = tk.Tk()
    my_gui = MainWindow(root)
    root.mainloop()
