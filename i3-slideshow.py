#!/usr/bin/python2
import gtk
import os
import time
from math import floor
import glob
#os.system("gsettings set org.gnome.desktop.background picture-uri file:///home/user/Pictures/wallpaper/Stairslwallpaper.png")

# Gnome / Unity
# CHANGE_BG_COMMAND_PREFIX = 'gsettings set org.gnome.desktop.background picture-uri file:///'
# i3
CHANGE_BG_COMMAND_PREFIX = 'feh --bg-fill '


ICON_NAME = 'preferences-wallpaper'
TRAY_TITLE = 'Wallpaper-Changer'
CONFIG_FILE_PATH = os.path.expanduser(
    "~") + '/.config/wallpaper_changer/config'
CONFIG_FILE_FOLDER = os.path.expanduser("~") + '/.config/wallpaper_changer/'
DEFAULT_TIME = 120
DEFAULT_FOLDER = os.path.expanduser("~")


class Wallpaper_Changer_Indicator:
    def __init__(self):
        # create the system tray icon
        self.status_icon = gtk.StatusIcon()
        self.status_icon.set_from_icon_name(ICON_NAME)
        self.status_icon.set_title(TRAY_TITLE)
        self.status_icon.set_tooltip(TRAY_TITLE)
        self.status_icon.set_visible(True)

        # Show the menu
        self.status_icon.connect('activate', self.activate)
        self.status_icon.connect('popup-menu', self.build_menu)

        # Init other things..
        # Number of seconds between one wallpaper and another
        try:
            filein = open(CONFIG_FILE_PATH, 'r')
            self.time = int(filein.readline())
            self.bg_folder = filein.readline()
            filein.close()
        except:
            self.time = DEFAULT_TIME
            self.bg_folder = DEFAULT_FOLDER
        self.window = None

        print 'Time set to ' + str(self.time)
        print 'BG folder set to ' + self.bg_folder

        # Wallpaper_Changer object
        self.wallpaper_changer = Wallpaper_Changer(self.time, self.bg_folder)

    def activate(self, widget, param=None):
        # Create window
        if self.window is not None:
            return
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect('delete_event', self.close_win)
        self.window.set_border_width(20)
        self.slider = gtk.SpinButton(adjustment=gtk.Adjustment(
            value=120, lower=1, upper=500, step_incr=1, page_incr=2, page_size=0))
        self.slider.set_digits(0)
        self.slider.set_value(self.time)
        self.file_selector_dialog = gtk.FileChooserDialog(title='Chose a background folder',
                                                          action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                                          buttons=(
                                                              gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
                                                          )
        self.file_selector_button = gtk.FileChooserButton(
            self.file_selector_dialog)
        self.file_selector_button.set_current_folder(self.bg_folder)

        # First hbox: seconds
        self.hbox_secs = gtk.HBox()
        self.hbox_secs.add(gtk.Label('Seconds'))
        self.hbox_secs.add(self.slider)

        # Second hbox: wallpaper folder
        self.hbox_folder = gtk.HBox()
        self.hbox_folder.add(gtk.Label('Background folder'))
        self.hbox_folder.add(self.file_selector_button)

        # Apply button
        self.apply_button = gtk.Button('Apply')
        self.apply_button.connect('pressed', self.apply_button_pressed)

        # Main vbox
        self.vbox = gtk.VBox()
        self.vbox.add(self.hbox_secs)
        self.vbox.add(self.hbox_folder)
        self.vbox.add(self.apply_button)

        self.window.add(self.vbox)
        self.window.show_all()

    def build_menu(self, icon, button, presstime):
        ''' Create the drop down menu '''
        self.menu = gtk.Menu()

        # time
        time_menu = gtk.MenuItem(self.intToTime(self.time))
        self.menu.append(time_menu)

        # BG folder
        bg_folder_menu = gtk.MenuItem(
            'Folder: ' + os.path.basename(self.bg_folder))
        self.menu.append(bg_folder_menu)

        # Next image
        next_image_button = gtk.MenuItem('Next Image')
        next_image_button.connect('activate', self.next_image_pressed)
        self.menu.append(next_image_button)

        # Slideshow toggle
        if self.wallpaper_changer.active is True:
            toggle_string = 'Stop Slideshow'
        else:
            toggle_string = 'Start Slideshow'
        toggle_active_button = gtk.MenuItem(toggle_string)
        toggle_active_button.connect('activate', self.toggle_active_pressed)
        self.menu.append(toggle_active_button)

        # Exit button
        exit_button = gtk.MenuItem('Exit')
        exit_button.connect('activate', self.kill)
        self.menu.append(exit_button)

        # Show the menu
        self.menu.show_all()
        self.menu.popup(None, None, gtk.status_icon_position_menu,
                        button, presstime, self.status_icon)

    def next_image_pressed(self, widget, data=None):
        ''' Next image pressed in the drop down menu'''
        if self.wallpaper_changer.timer is not None:
            self.wallpaper_changer.timer.cancel()
            self.wallpaper_changer.apply_background()
        else:
            # Forcing new wallpaper
            self.wallpaper_changer._apply_background()

    def toggle_active_pressed(self, widget, data=None):
        ''' Stop/Start Slideshow pressed in the drop down menu'''        
        self.wallpaper_changer.toggle_active()

    def apply_button_pressed(self, widget, data=None):
        ''' Apply button pressed in the popup window '''
        self.bg_folder = self.file_selector_button.get_filename()
        self.time = self.slider.get_value_as_int()
        self.wallpaper_changer.new_time_and_folder(self.time, self.bg_folder)
        print 'Apply pressed!'
        try:
            outfile = open(CONFIG_FILE_PATH, 'w')
        except IOError as error:
            try:
                os.makedirs(CONFIG_FILE_FOLDER)
            except OSError as other_error:
                return

            outfile = open(CONFIG_FILE_PATH, 'w')

        outfile.writelines([str(self.time), '\n', str(self.bg_folder)])
        outfile.close()
        # Close the popup window
        self.window.destroy()
        self.window = None

    def close_win(self, widget, data=None):
        ''' Popup window closing signal '''
        self.window = None
        return False

    def kill(self, widget, data=None):
        ''' kill the application signal '''
        gtk.main_quit()

    @staticmethod
    def intToTime(seconds):
        ''' Translate seconds into min sec format '''
        if seconds < 60:
            return '%s sec' % seconds
        else:
            return '%sm %ss' % (int(seconds / 60), seconds % 60)


from threading import Timer
from random import shuffle


class Wallpaper_Changer(object):
    def __init__(self, time, folder):
        # Active flag
        self.active = True
        # Set folder and timer
        self.time = time
        self.folder = folder
        # Parse folder
        self.parse_folder()
        # Start timer
        self.apply_background()

    def toggle_active(self):
        ''' Change the active flag '''
        if self.active:
            self.timer.cancel()
            self.timer = None
        else:
            self.start_timer()
        self.active = not self.active

    def parse_folder(self):
        ''' Parse the folder in order to find backgrounds '''
        self.images = glob.glob(self.folder + '/*')
        shuffle(self.images)

    def start_timer(self):
        ''' Start the timer to the next application of the background'''
        self.timer = Timer(self.time, self.apply_background)
        self.timer.start()

    def new_time_and_folder(self, time, folder):
        ''' Update time and folder path '''
        self.time = time
        self.folder = folder
        self.parse_folder()
        if self.timer is not None:
            self.timer.cancel()
        self.start_timer()

    def apply_background(self):
        ''' Apply new background '''
        # Return if it is not active
        if self.active is False:
            return
        # get the first image and remove from the list
        background = self.images[0]
        print 'Applying -> ' + background
        self.images.pop(0)
        if len(self.images) == 0:
            # re-parse folder
            self.parse_folder()
        try:
            os.system(CHANGE_BG_COMMAND_PREFIX + background)
        except:
            print 'Unable to change Background!'
        self.start_timer()

    def _apply_background(self):
        ''' Force apply new background (used for the menu button while slideshow is disabled) '''        
        # get the first image and remove from the list
        background = self.images[0]
        print 'Applying -> ' + background
        self.images.pop(0)
        if len(self.images) == 0:
            # re-parse folder
            self.parse_folder()
        try:
            os.system(CHANGE_BG_COMMAND_PREFIX + background)
        except:
            print 'Unable to change Background!'


if __name__ == '__main__':
    indicator = Wallpaper_Changer_Indicator()
    gtk.gdk.threads_init()
    gtk.main()
    print 'Killing program..'
    indicator.wallpaper_changer.timer.cancel()
    os._exit(0)
