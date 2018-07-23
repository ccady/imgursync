# apt-get install python3-tk
# used for windowing
import tkinter as tk
#from tkinter import ttk # also import the themed tkinter for good looking widgets (not obligatory)
import sys

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
        
        self.parent = parent
        self.parent.title(os.path.basename(__file__))
        
        self.string_status = tk.StringVar()
        self.string_id = tk.StringVar()
        self.string_secret = tk.StringVar()
        
        #self.read_config()

        self.frame_id = tk.Frame(parent)
        self.frame_id.pack(anchor = 'w')

        self.label_id = tk.Label(self.frame_id, text = "Client ID: ")
        self.label_id.pack(side = tk.LEFT, padx = 5, pady = 2)

        self.entry_id = tk.Entry(self.frame_id, width = 20, textvariable = self.string_id)
        self.entry_id.pack(side = tk.LEFT, padx = 5, pady = 2)

        self.frame_secret = tk.Frame(parent)
        self.frame_secret.pack(anchor = tk.W)

        self.label_secret = tk.Label(self.frame_secret, text = "Client Secret: ")
        self.label_secret.pack(side = tk.LEFT, padx = 5, pady = 2)

        self.entry_secret = tk.Entry(self.frame_secret, width=40, textvariable = self.string_secret)
        self.entry_secret.pack(side = tk.LEFT, padx = 5, pady = 2)
        
        self.frame_buttons = tk.Frame(parent)
        self.frame_buttons.pack(anchor = tk.W)

        self.button_readconfig = tk.Button(self.frame_buttons, text = "Read config", command = self.read_config)
        self.button_readconfig.pack(side = tk.LEFT, padx = 5, pady = 2)

        self.button_credentials = tk.Button(self.frame_buttons, text = "Get credentials from site", command = self.get_credentials)
        self.button_credentials.pack(side = tk.LEFT, padx = 5, pady = 2)

        self.button_configure = tk.Button(self.frame_buttons, text = "Test credentials", command = self.test_credentials)
        self.button_configure.pack(side = tk.LEFT, padx = 5, pady = 2)

        self.button_writeconfig = tk.Button(self.frame_buttons, text = "Write config", command = self.write_config)
        self.button_writeconfig.pack(side = tk.LEFT, padx = 5, pady = 2)

        self.label_status = tk.Label(parent, textvariable = self.string_status)
        self.label_status.pack(anchor = tk.W)

        self.lock_minimum_size()
        
    def open_url(self, url):
        webbrowser.open(url, new = 0, autoraise = True)

    def set_status(self, message):
        print(message)
        self.string_status.set(message)
            
    def lock_minimum_size(self):
        self.parent.update() # make sure all the info from previous widget placements has been recalculated
        self.parent.minsize(self.parent.winfo_width(), self.parent.winfo_height())

    def get_credentials(self):
        self.open_url('https://api.imgur.com/oauth2/addclient')
        sel.set_status('Enter id and secret, then test credentials.')
        return True

    def create_client(self):
        try:
            self.client = ImgurClient(self.config['client']['id'], self.config['client']['secret'])
        except:
            self.set_status('Failed to create client using given credentials.')
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
        
        if not 'client' in self.config.sections():
            self.config.add_section('client')
        self.string_id.set(self.config['client']['id'])
        self.string_secret.set(self.config['client']['secret'])
        return True

        
if __name__ == '__main__':
    root = tk.Tk()
    my_gui = MainWindow(root)
    root.mainloop()
