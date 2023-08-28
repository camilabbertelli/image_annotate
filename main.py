import os
from glob import glob
import gui
from gui import sg
import subprocess

# setting up the pysimplegui screen

folder_name = ""
imagesLabels = dict()

window = sg.Window('Image Annotation', gui.layout_main)
    
program_type = gui.CLASSIFICATION
proceed = False

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    if event == "folder" and values['folder']:
        window['error'].update("")

    if event == 'go':
        folder_name = values['folder']

        if not folder_name:
            continue

        if not os.path.exists(values['folder']):
            window['error'].update("Folder doesn't exist!", text_color='maroon')
            window['folder'].update("")
            continue

        window['error'].update("")

        # the user has selected a folder to work with
        proceed = True

        if values[gui.CLASSIFICATION]:
            program_type = gui.CLASSIFICATION
        if values[gui.DETECTION]:
            program_type = gui.DETECTION

        break


window.close()

if not proceed:
    exit()

if program_type == gui.CLASSIFICATION:
    subprocess.call(["python3 classification.py \"" + folder_name + "\""], shell=True)

if program_type == gui.DETECTION:
    subprocess.call(["python3 detection.py \"" + folder_name + "\""], shell=True)