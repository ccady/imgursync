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
        self.string_pin = tk.StringVar()
        self.string_access_token = tk.StringVar()
        self.string_refresh_token = tk.StringVar()

        self.frame_pin = tk.Frame(parent)
        self.frame_pin.pack(anchor = tk.W)

        self.label_pin = tk.Label(self.frame_pin, text = "PIN: ")
        self.label_pin.pack(side = tk.LEFT)

        self.entry_pin = tk.Entry(self.frame_pin, width = 12, textvariable = self.string_pin)
        self.entry_pin.pack(side = tk.LEFT)
        
        self.frame_tokens = tk.Frame(parent)
        self.frame_tokens.pack(anchor = tk.W)

        self.label_access_token = tk.Label(self.frame_tokens, text = "Access Token: ")
        self.label_access_token.pack(side = tk.LEFT)

        self.entry_access_token = tk.Entry(self.frame_tokens, width = 12, textvariable = self.string_access_token)
        self.entry_access_token.pack(side = tk.LEFT)

        self.label_refresh_token = tk.Label(self.frame_tokens, text = "Refresh Token: ")
        self.label_refresh_token.pack(side = tk.LEFT)

        self.entry_refresh_token = tk.Entry(self.frame_tokens, width = 12, textvariable = self.string_refresh_token)
        self.entry_refresh_token.pack(side = tk.LEFT)

        self.frame_buttons = tk.Frame(parent)
        self.frame_buttons.pack(anchor = tk.W)

        self.button_authorize = tk.Button(self.frame_buttons, text = "Read config", command = self.read_config)
        self.button_authorize.pack(side = tk.LEFT)

        self.button_authorize = tk.Button(self.frame_buttons, text = "Get new PIN", command = self.get_pin)
        self.button_authorize.pack(side = tk.LEFT)

        self.button_authorize = tk.Button(self.frame_buttons, text = "Get access tokens from PIN", command = self.get_tokens)
        self.button_authorize.pack(side = tk.LEFT)

        self.button_authorize = tk.Button(self.frame_buttons, text = "Authorization", command = self.authorize)
        self.button_authorize.pack(side = tk.LEFT)

        self.button_authorize = tk.Button(self.frame_buttons, text = "Write config", command = self.write_config)
        self.button_authorize.pack(side = tk.LEFT)

        self.label_status = tk.Label(parent, textvariable = self.string_status)
        self.label_status.pack(anchor = tk.W)

        self.lock_minimum_size()
        
        self.read_config()
                
    def open_url(self, url):
        webbrowser.open(url, new = 0, autoraise = True)

    def set_status(self, message):
        print(message)
        self.string_status.set(message)
            
    def lock_minimum_size(self):
        self.parent.update() # make sure all the info from previous widget placements has been recalculated
        self.parent.minsize(self.parent.winfo_width(), self.parent.winfo_height())

    def get_pin(self):
        self.open_url(self.client.get_auth_url('pin'))
        self.set_status('Enter PIN, then re-authorize.')
        return True

    def get_tokens(self):
        # presume self.client has been correctly created.
        try:
            credentials = self.client.authorize(self.string_pin.get(), 'pin')
            # now credentials object should contain both an access tokens and a refresh token
        except:
            self.set_status('Authorization using PIN failed.')
            print(sys.exc_info(), file = sys.stderr)
            return False

        self.string_access_token.set(credentials['access_token'])
        self.string_refresh_token.set(credentials['refresh_token'])
        
        self.set_status('Retrieved new tokens.  Try authorization now.')
        return True

    def authorize(self):
        try:
            self.client.set_user_auth(self.string_access_token.get(), self.string_refresh_token.get())
        except:
            self.set_status('Failed to authorize using given tokens.')
            print(sys.exc_info(), file = sys.stderr)
            return False

        # the tokens worked.  Save them to the configuration
        if not self.config.has_section('credentials'):
            self.config.add_section('credentials')
        self.config['credentials']['access_token'] = self.string_access_token.get()
        self.config['credentials']['refresh_token'] = self.string_refresh_token.get()
        
        self.set_status('Authorization was successful.  Write config file.')
        return True
    
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
        
        # we need to make sure that the client is creatable using id and secret from configuration.  complain if not.

        try:
            self.client = ImgurClient(self.config['client']['id'], self.config['client']['secret'])
            # enable re-authorize button
        except:
            self.set_status('Failed to create client using saved credentials. Run register script first.')
            print(sys.exc_info(), file = sys.stderr)
            return False
        
        # set access_token and refresh_token on screen
        try:
            self.string_access_token.set(self.config['credentials']['access_token'])
            self.string_refresh_token.set(self.config['credentials']['refresh_token'])
        except:
            self.set_status('Config did not contain tokens.  Get a new PIN.')
            print(sys.exc_info(), file = sys.stderr)
            return False
        
        self.set_status('Tokens exist in config file.  Try authorization now.')

        return True
        
if __name__ == '__main__':
    root = tk.Tk()
    my_gui = MainWindow(root)
    root.mainloop()
