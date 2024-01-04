#!/usr/bin/env python

# !!! from https://stackoverflow.com/a/36419702
"""Find the currently active window."""

import logging
import sys

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)

def get_active_window():
    """
    Get the currently active window.

    Returns
    -------
    string :
        Name of the currently active window.
    """
    import sys
    active_window_name = None
    if sys.platform in ['linux', 'linux2']:
        # Alternatives: https://unix.stackexchange.com/q/38867/4784
        try:
            import wnck
        except ImportError:
            # logging.debug("wnck not installed")
            wnck = None
        if wnck is not None:
            screen = wnck.screen_get_default()
            screen.force_update()
            window = screen.get_active_window()
            if window is not None:
                pid = window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
        else:
            try:
                import gi
                gi.require_version('Wnck', '3.0')
                gi.require_version('Gtk', '3.0')
                from gi.repository import Gtk, Wnck
                gi = "Installed"
            except ImportError:
                # logging.debug("gi.repository not installed")
                gi = None
            if gi is not None:
                Gtk.init([])  # necessary if not using a Gtk.main() loop
                screen = Wnck.Screen.get_default()
                screen.force_update()  # recommended per Wnck documentation
                active_window = screen.get_active_window()
                pid = active_window.get_pid()
                with open("/proc/{pid}/cmdline".format(pid=pid)) as f:
                    active_window_name = f.read()
    elif sys.platform in ['Windows', 'win32', 'cygwin']:
        # https://stackoverflow.com/a/608814/562769
        import win32gui
        window = win32gui.GetForegroundWindow()
        active_window_name = win32gui.GetWindowText(window)
    elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
        # https://stackoverflow.com/a/373310/562769
        from AppKit import NSWorkspace
        active_window_name = (NSWorkspace.sharedWorkspace()
                              .activeApplication()['NSApplicationName'])
    else:
        print("sys.platform={platform} is unknown. Please report."
              .format(platform=sys.platform))
        print(sys.version)
    return active_window_name

# !!! main program
import wx
import wx.lib.platebtn as plateBtn
import yaml
import os.path
from pynput import mouse, keyboard

class WorkWork(wx.Frame):

    def __init__(self, *args, **kw):
        # ensure parent's __init__ is called
        super(WorkWork, self).__init__(*args, **kw)

        # create panel in frame
        self.pnl = wx.Panel(self)

        # create timer text
        self.timerText = wx.StaticText(self.pnl, label="00:00:00")
        font = self.timerText.GetFont()
        font.PointSize += 12
        self.timerText.SetFont(font)
        self.timerText.SetForegroundColour((0,0,0))

        # create MENU button and style
        self.menuBtn = plateBtn.PlateButton(self, label="MENU", style=plateBtn.PB_STYLE_SQUARE)
        self.menuBtn.Bind(wx.EVT_BUTTON, self.ShowMenu)

        # create MENU dropdown
        menuDropdown = wx.Menu()
        resumeItem = menuDropdown.Append(-1, "&Resume previous time")
        menuDropdown.AppendSeparator()
        self.firstWindowItem = menuDropdown.Append(-1, "Program #&1: <none>")
        self.secondWindowItem = menuDropdown.Append(-1, "Program #&2: <none>")
        self.thirdWindowItem = menuDropdown.Append(-1, "Program #&3: <none>")
        emptySlotsItem = menuDropdown.Append(-1, "Empty &Program Slots")
        menuDropdown.AppendSeparator()
        self.timeoutItem = menuDropdown.Append(-1, "&Timeout: 10")
        menuDropdown.AppendSeparator()
        self.colorItem = menuDropdown.Append(-1, "Color &Alert", kind=wx.ITEM_CHECK)

        # set dropdown handlers
        self.Bind(wx.EVT_MENU, self.OnResumePrevious, resumeItem)
        self.Bind(wx.EVT_MENU, self.OnSetWindowItem1, self.firstWindowItem)
        self.Bind(wx.EVT_MENU, self.OnSetWindowItem2, self.secondWindowItem)
        self.Bind(wx.EVT_MENU, self.OnSetWindowItem3, self.thirdWindowItem)
        self.Bind(wx.EVT_MENU, self.OnEmptyProgramSlots, emptySlotsItem)
        self.Bind(wx.EVT_MENU, self.OnSetTimeout, self.timeoutItem)
        self.Bind(wx.EVT_MENU, self.OnSetColor, self.colorItem)

        # add dropdown to MENU
        self.menuBtn.SetMenu(menuDropdown)

        # handler for closing window
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        # create sizer to manage layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.timerText, wx.SizerFlags().Align(wx.ALIGN_CENTER_VERTICAL).Border(wx.LEFT, 4))
        sizer.Add(self.menuBtn, wx.SizerFlags().Align(wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL).Border(wx.LEFT, 4))
        self.pnl.SetSizer(sizer)
        self.pnl.Fit()

        # create stopwatch and timer to trigger updates
        self.stopwatch = wx.StopWatch()
        self.stopwatch.Pause()
        self.timer = wx.Timer(self)
        self.timer.Start(1000)
        self.Bind(wx.EVT_TIMER, self.Update)

        # create pynput handlers to check for key activity
        keyboard_listener = keyboard.Listener(
            on_press=self.UserActivity
        )
        keyboard_listener.start()

        mouse_listener = mouse.Listener(
            on_move=self.UserActivity,
            on_click=self.UserActivity,
            on_scroll=self.UserActivity
        )
        mouse_listener.start()

        # read config file and set settings
        # get config path
        self.config_dir = os.path.join(os.path.expanduser("~"), ".workwork")
        self.config_file = os.path.join(self.config_dir, "config.yml")
        # defaults
        self.work_windows = [None] * 3
        self.timeout = 10000
        self.color_alert = True
        self.not_working_color = {'red': 240, 'blue': 112, 'green': 112}
        self.not_working_text_color = {'red': 0, 'blue': 0, 'green': 0}
        self.working_color = {'red': 176, 'blue': 255, 'green': 255}
        self.working_text_color = {'red': 0, 'blue': 0, 'green': 0}
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
                self.work_windows = config["work_windows"]
                self.timeout = config["timeout"]
                self.previous_time = config["previous_time"]
                self.color_alert = config["color_alert"]
                self.working_color = config["working_color"]
                self.working_text_color = config["working_text_color"]
                self.not_working_color = config["not_working_color"]
                self.not_working_text_color = config["not_working_text_color"]
                self.UpdateProgramSlotLabels()
                logging.info("loaded config file at " + self.config_file)
        except Exception as e:
            logging.info("config file not found, likely first run. continuing with defaults. printing error...")
            logging.debug(repr(e))
            
        # set misc defaults
        self.setting_window = False
        self.paused = True

        # update ui elements to new state
        self.UpdateColors()
        self.UpdateColorAlertCheck()
        self.UpdateTimeoutLabel()

    def ShowMenu(self, *args, **kw):
        # hacky function to trim extra args from menubtn showmenu call from event
        self.menuBtn.ShowMenu()

    def UserActivity(self, *args, **kw):
        # get current time for later comparison
        self.timeAtLastActivity = self.stopwatch.Time()

    def UpdateTimeoutLabel(self):
        # updates timeout menuitem label to match timeout
        self.timeoutItem.SetItemLabel("Timeout: " + str(int(self.timeout / 1000)))

    def UpdateColorAlertCheck(self):
        # updates checkmark on color alert menu item
        self.colorItem.Check(self.color_alert)

    def UpdateColors(self):
        # update colors of all ui elements to match paused state
        if self.paused and self.color_alert:
            self.SetBackgroundColour(wx.Colour(self.not_working_color['red'], self.not_working_color['blue'], self.not_working_color['green']))
            self.menuBtn.SetLabelColor(wx.Colour(self.not_working_text_color['red'], self.not_working_text_color['blue'], self.not_working_text_color['green']))
            self.timerText.SetForegroundColour(wx.Colour(self.not_working_text_color['red'], self.not_working_text_color['blue'], self.not_working_text_color['green']))
        else:
            self.SetBackgroundColour(wx.Colour(self.working_color['red'], self.working_color['blue'], self.working_color['green']))
            self.menuBtn.SetLabelColor(wx.Colour(self.working_text_color['red'], self.working_text_color['blue'], self.working_text_color['green']))
            self.timerText.SetForegroundColour(wx.Colour(self.working_text_color['red'], self.working_text_color['blue'], self.working_text_color['green']))

    def UpdateProgramSlotLabels(self):
        # update labels to new programs
        self.firstWindowItem.SetItemLabel("Program #&1: " + (self.work_windows[0] or "<none>"))
        self.secondWindowItem.SetItemLabel("Program #&2: " + (self.work_windows[1] or "<none>"))
        self.thirdWindowItem.SetItemLabel("Program #&3: " + (self.work_windows[2] or "<none>"))

    def Update(self, *args, **kw):

        # get focused window
        focused = get_active_window()

        # get current time
        time = self.stopwatch.Time()

        # check if work windows are currently focused
        # or if timeout time has passed since activity
        if focused not in self.work_windows or time - self.timeAtLastActivity > self.timeout:
            self.working = False
        else:
            self.working = True

        # toggle stopwatch
        if self.working and self.paused:
            self.stopwatch.Resume()
            self.SetTitle("KEEP WORKING")
            self.paused = False
        elif not self.working and not self.paused:
            self.stopwatch.Pause()
            self.SetTitle("BACK TO WORK")
            self.paused = True
        self.UpdateColors()

        # update timer text to current stopwatch time
        x = time / 1000
        s = str(int(x % 60)).rjust(2, '0')
        x /= 60
        m = str(int(x % 60)).rjust(2, '0')
        x /= 60
        h = str(int(x % 24)).rjust(2, '0')
        self.timerText.SetLabel(h + ":" + m + ":" + s)

        # if setting window show that instead
        if self.setting_window == True:
            self.timerText.SetLabel("Awaiting program...")
            if focused != self.work_window_name:
                self.work_windows[self.setting_window_slot] = focused
                self.setting_window = False
                self.setting_window_slot = None
                self.UpdateProgramSlotLabels()
                self.Update()

        # hacky: currently StaticText doesn't adjust size when font size changed
        # will only adjust after drawing. so we have to call this sometime after draw...
        self.pnl.Fit()

    def OnExit(self, event):

        # kill listening threads
        mouse.Listener.stop
        keyboard.Listener.stop
        # save config to file and close program
        config = {'work_windows': self.work_windows,
                  'timeout': self.timeout,
                  'previous_time': self.stopwatch.Time(),
                  'color_alert': self.color_alert,
                  'working_color': self.working_color,
                  'working_text_color': self.working_text_color,
                  'not_working_color': self.not_working_color,
                  'not_working_text_color': self.not_working_text_color,}
        
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            with open(self.config_file, 'w') as file:
                yaml.dump(config, file)
                logging.info("saved config, closing")
        except Exception as e:
            # fuck itt
            logging.error("failed to save config file, closing anyway. printing error...")
            logging.error(repr(e))
        self.Destroy()

    def OnResumePrevious(self, event):
        # read from config and set timer accordingly
        self.stopwatch.Start(self.previous_time)
        if self.paused:
            self.stopwatch.Pause()
        self.Update()

    def OnSetWindowItem1(self, event):
        # checked later in update loop
        self.setting_window_slot = 0
        self.OnSetWindowItem()

    def OnSetWindowItem2(self, event):
        # checked later in update loop
        self.setting_window_slot = 1
        self.OnSetWindowItem()

    def OnSetWindowItem3(self, event):
        # checked later in update loop
        self.setting_window_slot = 2
        self.OnSetWindowItem()

    def OnSetWindowItem(self):
        # capture currently focused window due to os inconsistencies
        self.work_window_name = get_active_window()
        self.setting_window = True

    def OnEmptyProgramSlots(self, event):
        # reset slots array
        self.work_windows = [None] * 3
        self.UpdateProgramSlotLabels()

    def OnSetTimeout(self, event):
        # create gui for selecting timeout value. or dialog
        new_timeout = wx.GetNumberFromUser("Enter idle timeout in seconds:", "", "Set Idle Timeout", 10, 1, 9999999, self)
        # update menu item if not cancelled
        if new_timeout > 0:
            # convert to ms
            self.timeout = new_timeout * 1000
            self.UpdateTimeoutLabel()

    def OnSetColor(self, event):
        # toggle color alert
        self.color_alert = not self.color_alert
        self.UpdateColors()
        

if __name__ == '__main__':
    # creating window, moving to main loop
    app = wx.App()
    frm = WorkWork(None, title='BACK TO WORK', style=wx.STAY_ON_TOP | wx.SYSTEM_MENU | wx.CLOSE_BOX, size=(200, 65))
    frm.SetIcon(wx.Icon("./workwork.ico"))
    frm.Show()
    app.MainLoop()
