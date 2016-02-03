import subprocess
import sys

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import font as TkFont

from pkg_resources import get_distribution

from PyHardLinkBackup import __version__
from PyHardLinkBackup.backup_app.models import BackupRun, BackupName
from PyHardLinkBackup.phlb.config import phlb_config


# These are set in setup.py !
from PyHardLinkBackup.phlb.human import dt2naturaltimesince
from PyHardLinkBackup.phlb.info import backup_info, backup_run_info

DISTRIBUTION_NAME = "PyHardLinkBackup"
DIST_GROUP = "console_scripts"
ENTRY_POINT = "phlb"



def get_module_name():
    """
    :return: a string like: "PyHardLinkBackup.phlb_cli"
    """
    distribution = get_distribution(DISTRIBUTION_NAME)
    entry_info = distribution.get_entry_info(DIST_GROUP, ENTRY_POINT)
    if not entry_info:
        raise RuntimeError(
            "Can't find entry info for distribution: %r (group: %r, entry point: %r)" % (
                DISTRIBUTION_NAME, DIST_GROUP, ENTRY_POINT
            )
        )
    return entry_info.module_name


class RunButtonsFrame(tk.LabelFrame):
    def __init__(self, master, **kwargs):
        tk.LabelFrame.__init__(self, master)# , text="")
        self.grid(**kwargs)

        self.listbox_backup_names = tk.Listbox(self, width=75,
            selectmode=tk.SINGLE,
        )
        backup_names = BackupName.objects.all()
        for backup_name in backup_names:
            print(backup_name)
            self.listbox_backup_names.insert(tk.END, backup_name.name)
        self.listbox_backup_names.grid(row=1, column=0)
        self.listbox_backup_names.bind("<<ListboxSelect>>", self.select_backup_name)
        self.selected_backup_name = None

        button_backup = tk.Button(self,
            width=25,
            text="backup",
            command=master.backup
        )
        button_backup.grid(row=1, column=1)

        self.listbox_backup_runs = tk.Listbox(self, width=75,
            selectmode=tk.SINGLE,
        )
        self.listbox_backup_runs.grid(row=2, column=0)
        self.listbox_backup_runs.bind("<<ListboxSelect>>", self.select_backup_run)

        button_verify = tk.Button(self,
            width=25,
            text="verify",
            command=master.verify
        )
        button_verify.grid(row=2, column=1)
        self.var_fast = tk.BooleanVar(value=True)
        button_fast = tk.Checkbutton(self, text="verify fast", variable=self.var_fast)
        button_fast.grid(row=3, column=1, sticky=tk.E)

    def _get_name_and_runs(self):
        backup_name = BackupName.objects.get(name=self.selected_backup_name)
        backup_runs = BackupRun.objects.filter(name=backup_name)
        return backup_name, backup_runs

    def select_backup_name(self, event):
        self.selected_backup_name = self.listbox_backup_names.get( # FIXME
            self.listbox_backup_names.curselection()[0]
        )
        backup_name, backup_runs = self._get_name_and_runs()

        self.listbox_backup_runs.delete(0, tk.END)
        for backup_run in backup_runs:
            # print(backup_run)
            self.listbox_backup_runs.insert(tk.END,
                dt2naturaltimesince(backup_run.backup_datetime)
            )

        self.master.backup_name_selected(backup_name, backup_runs)

    def select_backup_run(self, event):
        backup_name, backup_runs = self._get_name_and_runs()
        no = self.listbox_backup_runs.curselection()[0]

        backup_run = backup_runs[no]
        self.master.backup_run_selected(backup_run)

    def select_path(self):
        path = filedialog.askdirectory(
            master=self, parent=self,
            initialdir=self.var_path.get(), mustexist=True
        )
        self.var_path.set(path)



class NewBackupFrame(tk.LabelFrame):
    def __init__(self, master, **kwargs):
        tk.LabelFrame.__init__(self, master , text="New Backup")
        self.grid(**kwargs)

        self.var_path = tk.StringVar(master=self, value=phlb_config.backup_path)
        self.entry_path = tk.Entry(self, textvariable=self.var_path, width=100)
        self.entry_path.grid(row=0, column=0, columnspan=2)

        button_path = tk.Button(self,
            width=25,
            text="select path",
            command=self.select_path
        )
        button_path.grid(row=1, column=0)

        button_backup = tk.Button(self,
            width=25,
            text="backup",
            command=master.backup
        )
        button_backup.grid(row=1, column=1)

    def select_path(self):
        path = filedialog.askdirectory(
            master=self, parent=self,
            initialdir=self.var_path.get(), mustexist=True
        )
        self.var_path.set(path)






class MultiStatusBar(tk.Frame):
    """
    base on code from idlelib.MultiStatusBar.MultiStatusBar
    """
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master)
        self.grid(**kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.labels = {}

    def set_label(self, name, text='', **kwargs):
        defaults = {
            "ipadx": 2, # add internal padding in x direction
            "ipady": 2, # add internal padding in y direction
            "padx": 1, # add padding in x direction
            "pady": 0, # add padding in y direction
            "sticky": tk.NSEW, # stick to the cell boundary
        }
        defaults.update(kwargs)
        if name not in self.labels:
            label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
            label.grid(column=len(self.labels), row=0, **defaults)
            self.labels[name] = label
        else:
            label = self.labels[name]
        label.config(text=text)


class TextFrame(tk.LabelFrame):
    def __init__(self, master, **kwargs):
        tk.LabelFrame.__init__(self, master, text="Info")
        self.grid(**kwargs)

        self.text = scrolledtext.ScrolledText(
            master=self, height=30, width=80
        )
        self.text.config(
            background="#ffffff", foreground="#000000",
            highlightthickness=0,
            font=('courier', 11),
        )
        self.text.grid(row=0, column=0, sticky=tk.NSEW)

        self.text.insert(tk.END, "Please select a backup.")

    def clear(self):
        self.text.delete("1.0", tk.END)

    def append(self, txt):
        self.text.insert(tk.END, txt)

    def set_content(self, txt):
        self.clear()
        self.append(txt)




class Launcher:
    def __init__(self):
        module_name = get_module_name()
        print("module_name:", module_name)
        self.subprocess_args = (sys.executable, "-m", module_name)

    def launch(self, *args):
        subprocess_args = list(self.subprocess_args)
        subprocess_args += args
        print("Launch: %r" % subprocess_args)
        subprocess.call(subprocess_args)


class PyHardLinkBackupLauncher(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.geometry("+%d+%d" % (
            self.winfo_screenwidth() * 0.1, self.winfo_screenheight() * 0.1
        ))
        self.title("PyHardLinkBackup v%s - launcher" % __version__)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.add_widgets()
        # self.set_status_bar()

        self.update()

        self.launcher = Launcher()


    def add_widgets(self):
        padding = 5
        defaults = {
            "ipadx": padding, # add internal padding in x direction
            "ipady": padding, # add internal padding in y direction
            "padx": padding, # add padding in x direction
            "pady": padding, # add padding in y direction
            "sticky": tk.NSEW, # stick to the cell boundary
        }

        self.frame_new_backup = NewBackupFrame(self, column=0, row=0, **defaults)

        self.frame_run_buttons = RunButtonsFrame(self, column=0, row=1, **defaults)

        self.text_frame = TextFrame(self, column=0, row=2, **defaults)

        self.status_bar = MultiStatusBar(self, column=0, row=3,
            # columnspan=2,
            sticky=tk.NSEW,
        )

    def set_status_bar(self):
        defaults = {
            "padx": 5, # add padding in x direction
            "pady": 0, # add padding in y direction
        }
        self.status_bar.set_label("python_version", sys.version, **defaults)

    def backup_name_selected(self, backup_name, backup_runs):
        self.backup_name = backup_name
        self.text_frame.clear()
        for line in backup_info(backup_name):
            self.text_frame.append(line + "\n")
        self.text_frame.append("\nPlease select one backup run for more info.")

    def backup_run_selected(self, backup_run):
        self.backup_run = backup_run
        self.text_frame.clear()
        for line in backup_run_info(backup_run):
            self.text_frame.append(line + "\n")

    def backup(self):
        path = self.frame_run_buttons.var_path.get()
        self.launcher.launch("backup", path)

    def verify(self):
        path = "%s" % self.backup_run.path_part() # Path2() instance to string
        fast = self.frame_run_buttons.var_fast.get()
        print("verify (fast:%s): %s" % (fast, path))

        args = ["verify"]
        if fast:
            args.append("--fast")
        args.append(path)

        self.launcher.launch(*args)


