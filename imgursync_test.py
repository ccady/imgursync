# apt-get install python3-tk
# used for windowing
import tkinter as tk
#from tkinter import ttk # also import the themed tkinter for good looking widgets (not obligatory)
import sys

from tkinter.font import Font
#from tkinter.scrolledtext import ScrolledText
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory

# pip3 install imgurpython (NO! out-of-date, roken code)
# git clone https://github.com/ueg1990/imgurpython.git
# used for imgur access
import imgurpython

# does not need any installation 
# necessary to expand path for config file
import os.path

# does not need any installation 
import configparser

# does not need any installation 
# used to get authorization from imgur web site
import webbrowser
    
# does not need any installation 
# used to get current date and time
import datetime    
# does not need any installation 
# used to get authorization from imgur web site
import webbrowser

class ImgurClientEnhanced(imgurpython.ImgurClient):
    
    allowed_album_fields = {
        'ids', 'title', 'description', 'privacy', 'layout', 'cover', 'order'
    }
    
    def __init__(self, client_id, client_secret, access_token=None, refresh_token=None, mashape_key=None):
        super(ImgurClientEnhanced, self).__init__(client_id, client_secret, access_token, refresh_token, mashape_key)
    
    def update_image(self, image_id, fields):
        '''
        Note: Can only update title or description of image
        '''
        post_data = {field: fields[field] for field in set({'title', 'description'}).intersection(fields.keys())}
        return self.make_request('POST', 'image/%s' % image_id, data=post_data)
    
class MainWindow:

    def __init__(self, parent):
        
        font_default = Font(family = "default", size = "10")
        font_status = Font(family = "default", size = "10", slant = 'italic')
        font_contents = font_default
        
        parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.images = {}
        self.albums = {}

        self.parent = parent
        self.parent.title(os.path.basename(__file__))
        
        self.string_status = tk.StringVar()
        
        if self.read_config():
            if self.create_client():
                self.authorize()
                
        self.parent.geometry(self.config.get('gui', 'geometry', fallback = '526x300+275+191'))

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
        #self.treeview.bind('<Double-Button-1>', self.treeview_doubleclick)
        self.treeview.bind('<Button-3>', self.treeview_rightclick)
        #self.treeview.bind('<Button-1>', self.treeview_click)
        self.treeview.bind('<<TreeviewOpen>>', self.populate_album)
        for columnname in columnnames:
            self.treeview.heading(columnname, text = columnname)
            self.treeview.column(columnname, stretch = True)
        self.treeview.pack(anchor = tk.W, fill = tk.BOTH, expand = True)
        
        # immediately populate tree
        self.populate_albums()

        # create an album context menu
        self.menu_album_context = tk.Menu(parent, tearoff = 0)
        self.menu_album_context.add_command(label="Get Info", command = self.get_album_info)
        self.menu_album_context.add_command(label="View", command = self.view_album)
        self.menu_album_context.add_command(label="Edit", command = self.edit_album)
        self.menu_album_context.add_command(label="Delete", command = self.delete_album)
        self.menu_album_context.add_command(label="Upload Image", command = self.upload_image)
        self.menu_album_context.add_separator()
        self.menu_album_context.add_command(label="Upload Album", command = self.upload_album)
        self.menu_album_context.bind("<FocusOut>", lambda event: self.menu_album_context.unpost()) # keyboard focus
        self.menu_album_context.bind("<Leave>", lambda event: self.menu_album_context.unpost()) # mouse focus

        # create an image context menu
        self.menu_image_context = tk.Menu(parent, tearoff = 0)
        self.menu_image_context.add_command(label="Get Info", command = self.get_image_info)
        self.menu_image_context.add_command(label="View", command = self.view_image)
        self.menu_image_context.add_command(label="Edit", command = self.edit_image)
        self.menu_image_context.add_command(label="Delete", command = self.delete_image)
        self.menu_image_context.bind("<FocusOut>", lambda event: self.menu_image_context.unpost()) # keyboard focus
        self.menu_image_context.bind("<Leave>", lambda event: self.menu_image_context.unpost()) # mouse focus

    def on_closing(self):
        if not 'gui' in self.config.sections():
            self.config.add_section('gui')
        self.config['gui']['geometry'] = self.parent.geometry()
        self.write_config()
        self.parent.destroy()

    def treeview_click(self, event):
        #print("geometry!")
        #print(self.parent.geometry())
        bob = 'you uncle'

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
            type = self.treeview_item()['type']
            if type == 'album':
                self.menu_album_context.post(event.x_root - 5, event.y_root - 5)
            if type == 'image':
                self.menu_image_context.post(event.x_root - 5, event.y_root - 5)
        else:
            # clear selection
            #self.treeview.selection_clear()
            if len(self.treeview.selection()) > 0:
                self.treeview.selection_remove(self.treeview.selection()[0])
                self.menu_other_context.post(event.x_root - 5, event.y_root - 5)

    def get_album_info(self):
        tk.messagebox.showinfo("album info", vars(self.albums[self.treeview_item()['id']]))

    def get_image_info(self):
        tk.messagebox.showinfo("image info", vars(self.images[self.treeview_item()['id']]))

    def treeview_node(self):
        return self.treeview.selection()[0] # iid

    def treeview_item(self):
        iid = self.treeview.selection()[0]
        return self.treeview.set(iid)

    def treeview_delete(self):
        iid = self.treeview.selection()[0]
        self.treeview.delete(iid)

    def view_album(self):
        self.open_url(self.client.get_album(self.treeview_item()['id']).link)

    def view_image(self):
        self.open_url(self.client.get_image(self.treeview_item()['id']).link)

    def edit_album(self):
        AlbumEditor(self.parent, self.albums[self.treeview_item()['id']], self.client, self.config)

    def edit_image(self):
        ImageEditor(self.parent, self.images[self.treeview_item()['id']], self.client)

    def upload_album(self):
        defaultdirectory = self.config.get('gui', 'lastopendir', fallback = '.')
        directory = askdirectory(initialdir = defaultdirectory)
        if directory:
            prefixdirectory, basedirectory = os.path.split(directory)

            if not 'gui' in self.config.sections():
                self.config.add_section('gui')
            self.config['gui']['lastopendir'] = directory
            
            # give warning if album may already exist
            
            newalbum = self.create_album(directory)
            
            filenames = os.listdir(directory)
            for filename in filenames:
                baseprefix, baseext = os.path.splitext(filename)
                if baseext in ('.jpg', '.png'):
                    self.set_status('Uploading ' + filename)
                    newimage = self.upload_image_to_album(newalbum.id, directory + '/' + filename)                
                    self.set_status('Done uploading ' + filename)

    def upload_image(self):
        id = self.treeview_item()['id']
        directory = self.config.get('gui', 'lastopendir', fallback = '.')
        filename = askopenfilename(initialdir = directory) # show an "Open" dialog box and return the path to the selected file
        if filename:
            directory, basename = os.path.split(filename)
            baseprefix, baseext = os.path.splitext(basename)

            if not 'gui' in self.config.sections():
                self.config.add_section('gui')
            self.config['gui']['lastopendir'] = directory

            newimage = self.upload_image_to_album(id, filename)
                
            # add to internal collection
            self.images[newimage.id] = newimage
            # add to treeview
            image_name = newimage.name if newimage.name else 'Unnamed'
            self.treeview.insert(self.treeview_node(), tk.END, text = image_name, values = [newimage.id, 'image'])
            return True

    def upload_image_to_album(self, album_id, filepath):

        directory, basename = os.path.split(filepath)
        baseprefix, baseext = os.path.splitext(basename)

        imageconfig = { "album": album_id, "name": basename, "title": baseprefix, "description": baseprefix }
        try:
            self.parent.config(cursor = 'watch')
            self.parent.update()
            newimage = imgurpython.imgur.models.image.Image(self.client.upload_from_path(path = filepath, config = imageconfig, anon = False))
        except ImgurClientError as e:
            self.set_status('Failed to upload image.')
            print(sys.exc_info(), file = sys.stderr)
            raise
        finally:
            self.parent.config(cursor = '')

        return newimage

    def create_album(self, directory):

        prefixdirectory, basedirectory = os.path.split(directory)

        albumfields = { "title": basedirectory, "description": basedirectory }
        try:
            self.parent.config(cursor = 'watch')
            self.parent.update()
            newalbum = imgurpython.imgur.models.album.Album(self.client.create_album(fields = albumfields))
        except ImgurClientError as e:
            self.set_status('Failed to upload image.')
            print(sys.exc_info(), file = sys.stderr)
            raise
        finally:
            self.parent.config(cursor = '')

        return newalbum

    def delete_image(self):
        id = self.treeview_item()['id']
        if messagebox.askyesno('Deleting image ' + id, 'Are you sure?'):
            try:
                self.parent.config(cursor = 'watch')
                self.parent.update()
                self.client.delete_image(id)
            except imgurpython.ImgurClientError as e:
                self.set_status('Failed to delete image.')
                print(sys.exc_info(), file = sys.stderr)
                return False
            finally:
                self.parent.config(cursor = '')

            # remove from internal collection
            self.images.pop(id, None)
            # remove from treeview
            self.treeview_delete()
            return True

    def delete_album(self):
        id = self.treeview_item()['id']
        if messagebox.askyesno('Deleting album ' + id, 'Are you sure?'):
            try:
                self.parent.config(cursor = 'watch')
                self.parent.update()
                self.client.album_delete(id)
            except imgurpython.ImgurClientError as e:
                self.set_status('Failed to delete album.')
                print(sys.exc_info(), file = sys.stderr)
                return False
            finally:
                self.parent.config(cursor = '')

            # remove from internal collection
            self.albums.pop(id, None)
            # remove from treeview
            self.treeview_delete()
            return True

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
            self.parent.config(cursor = 'watch')
            self.parent.update()
            self.client = ImgurClientEnhanced(self.config['client']['id'], self.config['client']['secret'])
            return True
        except ImgurClientError as e:
            print(e)
            self.set_status('ImgurClientError.')
            print(sys.exc_info(), file = sys.stderr)
            return False
        except:
            self.set_status('Failed to create client using saved credentials. Run register program.')
            print(sys.exc_info(), file = sys.stderr)
            return False
        finally:
            self.parent.config(cursor = '')


    def authorize(self):
        try:
            self.parent.config(cursor = 'watch')
            self.parent.update()
            self.client.set_user_auth(self.config['credentials']['access_token'], self.config['credentials']['refresh_token'])
            return True
        except:
            self.set_status('Failed to authorize using saved credentials. Run authorize program.')
            print(sys.exc_info(), file = sys.stderr)
            return False
        finally:
            self.parent.config(cursor = '')

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

    def populate_albums(self):
        tempalbums = sorted(self.client.get_account_albums('me'), key = lambda album: album.order)
        for album in tempalbums:
            self.albums[album.id] = album
            album_title = album.title if album.title else 'Untitled'
            rowid = self.treeview.insert('', tk.END, text = album_title, values = [album.id, 'album'])
            self.treeview.insert(rowid, tk.END, text = 'dummy', values = ['', 'dummy']) # makes the item "openable"
                
    def populate_album(self, event):
        try:
            
            self.parent.config(cursor = 'watch')
            self.parent.update()

            selectednode = self.treeview.focus()
            if self.treeview.set(selectednode, 'type') == 'album':
                for child in self.treeview.get_children(selectednode):
                    if self.treeview.set(child, 'type') == 'dummy':
                        self.treeview.delete(*self.treeview.get_children(selectednode))
                        for image in self.client.get_album_images(self.treeview.set(selectednode, 'id')):
                            self.images[image.id] = image
                            image_name = image.name if image.name else 'Unnamed'
                            self.treeview.insert(selectednode, tk.END, text = image_name, values = [image.id, 'image'])
        finally:
            self.parent.config(cursor = '')

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
            return True

        except:
            self.set_status('Failed to read config file.')
            print(sys.exc_info(), file = sys.stderr)
            return False
        
class AlbumEditor:
    def __init__(self, parent, album, client, config):

        self.album = album
        self.client = client
        self.config = config

        self.parent = tk.Toplevel(parent)
        self.parent.title("album " + album.id)
        
        self.parent.geometry(self.config.get('gui', 'geometry.album', fallback = '526x150+604+529'))

        # configure the "data" column to be the one that stretches.
        self.parent.columnconfigure(1, weight = 1)
        
        # 'layout' is deprecated and can be changed, but has no effec on the site, so we don;t bother to change it.
        self.editfields = ['title', 'description', 'privacy', 'cover', 'order']
        self.editvalues = {}
        for editfield in self.editfields:
            editvalue = tk.StringVar()    
            editvalue.set(str(getattr(album, editfield)))    
            self.editvalues[editfield] = editvalue
        
        row = 0
        for editfield in self.editfields:
            row = row + 1
            label = tk.Label(self.parent, text = editfield)
            label.grid(sticky = tk.W, row = row, column = 0)
            entry = tk.Entry(self.parent, textvariable = self.editvalues[editfield])
            entry.grid(sticky = (tk.W + tk.E), row = row, column = 1)       

        row = row + 1

        self.frame_buttons = tk.Frame(self.parent, bd = 2)
        self.button_apply = tk.Button(self.frame_buttons, text = 'Apply', command = self.apply)
        self.button_apply.pack(side = tk.LEFT)
        self.button_done = tk.Button(self.frame_buttons, text = 'Done', command = self.done)
        self.button_done.pack(side = tk.LEFT)

        self.frame_buttons.grid(sticky = tk.W, row = row, column = 0, columnspan = 2)
    
    def done(self):
        if not 'gui' in self.config.sections():
            self.config.add_section('gui')
        self.config['gui']['geometry.album'] = self.parent.geometry()

        self.parent.destroy()

    def apply(self):
        # write the changed fields back to the album object, and write to imgur, too
        fieldstoupdate = { 'ids': None }
        for editfield in self.editfields:
            newvalue = self.editvalues[editfield].get()
            fieldstoupdate[editfield] = newvalue
            setattr(self.album, editfield, newvalue)

        # Bug in update_album function requires that ids be set.  If not a list, then it is not considered.
        self.client.update_album(album_id = self.album.id, fields = fieldstoupdate)
        
        # try re-reading now, debug code
        temp = self.client.get_album(self.album.id)
        print(temp)
        print(vars(temp))

class ImageEditor:
    def __init__(self, parent, image, client):

        self.image = image
        self.client = client
        self.parent = tk.Toplevel(parent)
        self.parent.title("image " + image.id)
        
        # configure the "data" column to be the one that stretches.
        self.parent.columnconfigure(1, weight = 1)
        
        self.editfields = ['title', 'description']
        self.editvalues = {}
        for editfield in self.editfields:
            editvalue = tk.StringVar()    
            editvalue.set(str(getattr(image, editfield)))    
            self.editvalues[editfield] = editvalue
            
        row = 0
        for editfield in self.editfields:
            row = row + 1
            label = tk.Label(self.parent, text = editfield)
            label.grid(sticky = tk.W, row = row, column = 0)
            entry = tk.Entry(self.parent, textvariable = self.editvalues[editfield])
            entry.grid(sticky = (tk.W + tk.E), row = row, column = 1)       
            
        row = row + 1

        self.frame_buttons = tk.Frame(self.parent, bd = 2)
        self.button_apply = tk.Button(self.frame_buttons, text = 'Apply', command = self.apply)
        self.button_apply.pack(side = tk.LEFT)
        self.button_done = tk.Button(self.frame_buttons, text = 'Done', command = self.done)
        self.button_done.pack(side = tk.LEFT)

        self.frame_buttons.grid(sticky = tk.W, row = row, column = 0, columnspan = 2)

    def done(self):
        self.parent.destroy()
        
    def apply(self):
        # write the changed fields back to the image object, and write to imgur, too
        fieldstoupdate = {}
        for editfield in self.editfields:
            newvalue = self.editvalues[editfield].get()
            fieldstoupdate[editfield] = newvalue
            setattr(self.image, editfield, newvalue)

        self.client.update_image(image_id = self.image.id, fields = fieldstoupdate )

if __name__ == '__main__':
    root = tk.Tk()
    my_gui = MainWindow(root)
    root.mainloop()
