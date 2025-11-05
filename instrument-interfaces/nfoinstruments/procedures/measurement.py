from pymeasure.experiment import Results, Worker

import tkinter
from tkinter import filedialog
import os

def increment_filename(filename):
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(new_filename):
        new_filename = f"{base_name}_{counter}{ext}"
        counter += 1

    return new_filename

class Measurement:

    def __init__(self, procedure):
        self._procedure = procedure
        self.filename = None
        self.timeout = 36000 

        self._tk_root = tkinter.Tk()
        self._tk_root.withdraw()

    def run(self):
        if self.filename is None:
            raise Exception("No filename selected")
        
        self._result = Results(self._procedure, increment_filename(self.filename))
        self._worker = Worker(self._result)

        self._worker.start()
        self._worker.join(timeout=self.timeout)

    def choose_filename(self):
        """
        Open a file dialog to choose a base filename for saving the measurement data.
        """
        currdir = os.getcwd()
        file_options = {
            'parent': self._tk_root,
            'initialdir': currdir,
            'title': 'Please select a filename',
            'confirmoverwrite': False,
            'filetypes': [
                ("CSV file", ".csv"),
                ("Text file", ".txt")
            ],
            'defaultextension': ".csv"
        }
        filename = filedialog.asksaveasfilename(**file_options)
        if filename:
            self.filename = filename