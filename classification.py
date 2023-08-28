import os
import io
import sys
import splitfolders
import threading
import shutil
from glob import glob
from PIL import Image
import gui
from gui import sg


def setSelected(index):
    aux = list()
    for value in imagesLabels[index]:
        index = labels.index(value)
        aux.append(gui.labelsInList[index])
    window["labels"].set_value(aux)

def loadImageAtIndex(index):
    address = allImages[index]
    image = Image.open(address)
    image.thumbnail((700, 700))
    bio = io.BytesIO()
    image.save(bio, format="PNG")
    window["currentImage"].update(data=bio.getvalue())
    window["imageName"].update(address.split("/")[-1])

    window["labels"].update()


indexCurrentImage = 0

def goToImage(indexToGo):
    global indexCurrentImage
    indexCurrentImage = indexToGo
    loadImageAtIndex(indexCurrentImage)

    if indexCurrentImage not in imagesLabels:
        imagesLabels[indexCurrentImage] = list()
    
    setSelected(indexCurrentImage)
    window["previous"].update(disabled=False)
    window["next"].update(disabled=False)

    if indexCurrentImage == 0:
        window["previous"].update(disabled=True)

    if indexCurrentImage == len(allImages) - 1:
        window["next"].update(disabled=True)

def populateImages():
    if os.path.exists(folder_name + "/train") and os.path.exists(folder_name + "/test"):
        
        names = list()
        for root, dirs, files in os.walk(folder_name, topdown=True):
            
            for name in files:

                label = root.split("/")[-1]
                path = os.path.join(root, name)

                if name not in names:
                    allImages.append(path)
                    names.append(name)
                    imagesLabels[names.index(name)] = list()

                imagesLabels[names.index(name)].append(label)
                if label not in labels:
                    labels.append(label)
                    gui.labelsInList.append(str(labels.index(label) + 1) + ": " + label)
    else:
        images = (folder_name + '/*.png', folder_name + '/*.jpg') # the tuple of file types
        for image in images:
            allImages.extend(glob(image))

    return sorted(allImages)

folder_name = sys.argv[1]
#folder_name = "/home/camicasa/Documents/image_annotate/test_images"

labels = list()
allImages = list()
imagesLabels = dict()

allImages = populateImages()

if not allImages:
    sg.popup_no_buttons("Unfortunatly, the folder provided has no images", title=":(")
    os.system("python3 main.py")
    exit()

window = sg.Window('Image Classification Annotation', gui.layout_classification, finalize=True, return_keyboard_events=True)
window['labelToAdd'].bind("<Return>", "_enter")
window["labelToAdd"].set_focus(True)
window["numberImages"].update("Images loaded:" + str(len(allImages)))

proceed = False
missingAnnotation = list()
firstQuickAnnotation = True
quickAnnotation = False
defaultLabel = ""

goToImage(indexCurrentImage)

while True:

    event, values = window.read()


    if event in (sg.WIN_CLOSED, 'Exit'):
        break


    if event == "addLabel" or event == "labelToAdd" + "_enter":
        labelToAdd = values["labelToAdd"]

        if not labelToAdd:
            continue

        if labelToAdd in labels:
            window['error'].update("Label already in \navailable classes!", text_color='maroon')
            continue
        
        gui.labelsInList.append(str(len(labels) + 1) + ": " + labelToAdd)
        labels.append(labelToAdd)

        window["labels"].update(gui.labelsInList)
        window["labelToAdd"].update("")
        window['error'].update("")

        setSelected(indexCurrentImage)

        continue


    if event == "removeLabel":
        labelToRemove = values["labelToAdd"]

        if not labelToRemove:
            continue

        if labelToRemove not in labels:
            window['error'].update("Label is non-existent!", text_color='maroon')
            continue

        for image in imagesLabels:
            if labelToRemove in imagesLabels[image]:
                imagesLabels[image].remove(labelToRemove)
                
        labels.remove(labelToRemove)
        gui.labelsInList = list()
        for index in range(len(labels)):
            gui.labelsInList.append(str(index + 1) + ": " + labels[index])

        window["labels"].update(gui.labelsInList)
        window["labelToAdd"].update("")
        window['error'].update("")


    if event == "editLabel":
        labelToEdit = values["labelToAdd"]

        if not labelToEdit:
            continue

        if labelToEdit not in labels:
            window['error'].update("Label is non-existent!", text_color='maroon')
            continue

        replaceWith = labelToEdit

        replace_space = [[sg.Push(),sg.Text("Replace \"" + labelToEdit + "\" with:", font=gui.subtitleFont),sg.Push()],
                         [sg.Push(),sg.Input(replaceWith, key="replaceWith", font=gui.bodyFont),sg.Push()],
                         [sg.Push(),sg.Text(key="error-replace", font=gui.bodyFont),sg.Push()],
                         [sg.Push(),sg.Button("Save", key="save", font=gui.bodyFont),sg.Push()]]
        

        edit = sg.Window('Edit label', replace_space, keep_on_top=True, finalize=True, return_keyboard_events=True)

        edit['replaceWith'].bind("<Return>", "_enter")
        while (True):
            event, values = edit.read()

            if event in (sg.WIN_CLOSED, 'Exit'):
                break

            if event == "save" or event == "replaceWith" + "_enter":

                replaceWith = values["replaceWith"]
                
                if not replaceWith:
                    replaceWith = labelToEdit
                    continue

                if replaceWith == labelToEdit:
                    break

                if replaceWith in labels:
                    edit['error-replace'].update("Label already exists", text_color='maroon')
                    replaceWith = labelToEdit
                    continue

                for image in imagesLabels:
                    if labelToEdit in imagesLabels[image]:
                        imagesLabels[image][imagesLabels[image].index(labelToEdit)] = replaceWith

                labels[labels.index(labelToEdit)] = replaceWith
                edit['error-replace'].update("")
                break

        edit.close()

        gui.labelsInList = list()
        for index in range(len(labels)):
            gui.labelsInList.append(str(index + 1) + ": " + labels[index])
        
        window["labels"].update(gui.labelsInList)
        window["labelToAdd"].update("")
        window['error'].update("")
        setSelected(indexCurrentImage)


    if event == "previous" or event == "Left:113":
        if indexCurrentImage - 1 < 0:
            continue
        
        goToImage(indexCurrentImage - 1)
        
        continue


    if event == "next" or event == "Right:114":
        if indexCurrentImage + 1 >= len(allImages):
            continue
        
        goToImage(indexCurrentImage + 1)
        
        continue


    if event == "labels":
        aux = list()
        for value in values["labels"]:
            index = gui.labelsInList.index(value)
            aux.append(labels[index])
        imagesLabels[indexCurrentImage] = aux

        continue


    if event == "continue":
        missingAnnotation = list()
        for image in range(len(allImages)):
            if image not in imagesLabels or not imagesLabels[image]:
                # append index of image with missing annotation
                missingAnnotation.append(image)

        defaultLabel = values["defaultLabel"] if values["defaultLabel"] else gui.defaultLabel

        ch = "No"
        if not missingAnnotation:
            ch = sg.popup_yes_no("  Once you continue and move on to the next phase, you won't be able to go back.\n" \
                                 "  Do you wish to proceed?",  title="Are you sure?")
        else:
            ch = sg.popup_yes_no("  Atention! You have " + str(len(missingAnnotation)) + " image(s) unlabeled!\n" \
                                 "  Go to 'All images' to check what you missed!\n\n" \
                                 "  Once you continue and move on to the next phase, you won't be able to go back.\n" \
                                 "  Do you wish to proceed?",  title="Are you sure?")

        if ch == "Yes":
            proceed = True
            break

        continue


    if event == "quickAnnotation":
        if firstQuickAnnotation:
            firstQuickAnnotation = False
            sg.Popup("  Quick annotation is a simple way to annotate your images " \
                     "using the first 9 classes you've possibly added.\n" \
                     "  All you have to do is type on your keyboard the number associated with the desired class. " \
                     "Moving between images with the arrow keys is always available. Try it! \n\n" \
                     "  P.S.: Adding new labels will be disabled while this functionality is on", title="Quick annotation")

        quickAnnotation = not quickAnnotation
        window["labelToAdd"].update(disabled=quickAnnotation)
        window["defaultLabel"].update(disabled=quickAnnotation)
        window["addLabel"].update(disabled=quickAnnotation)
        window["removeLabel"].update(disabled=quickAnnotation)
        window["editLabel"].update(disabled=quickAnnotation)

        state = "ON" if quickAnnotation else "OFF"
        window["quickAnnotation"].update(state)

        continue


    if event == "allImages":
        justNames = list()

        for i in range(len(allImages)):
            extra = ""
            if i in imagesLabels and imagesLabels[i]:
                extra = " (" + ", ".join(imagesLabels[i]) + ")"
            justNames.append(allImages[i].split(folder_name)[1] + extra)

        window.hide()

        layout_all_images = list()
        layout_all_images = [[sg.Push(),sg.Text("Images and their state (Labeled, Unlabeled)", font=gui.subtitleFont), sg.Push()],
                        [sg.Push(), sg.Listbox(values=justNames, size=(30, 30), enable_events=True,horizontal_scroll=True,
                                               font=gui.bodyFont,key="justNames", bind_return_key=True), sg.Push()],
                        [sg.Column([])],
                        [sg.Push(), sg.Button("Go to image", key="choose", font=gui.bodyFont), sg.Push()]]
        choose = sg.Window('Choose file', layout_all_images, keep_on_top=True, finalize=True)
       
        choose["justNames"].bind('<Double-Button-1>' , "_double")
        choose.write_event_value("start", None)
        while (True):
            event, values = choose.read()

            if event in (sg.WIN_CLOSED, 'Exit'):
                break

            if event == "start":
                for image in range(len(allImages)):
                    color_bg = "powder blue" if image in imagesLabels and imagesLabels[image] else "light coral"
                    color_fg = "white" if image == indexCurrentImage else "black"
                    choose['justNames'].Widget.itemconfig(image, bg=color_bg, fg=color_fg)

            if event == "choose" or event == "justNames" + "_double":
                select = values["justNames"]
                if not select:
                    break
                
                index = justNames.index(select[0])
                goToImage(index)
                break


        choose.close()
        window.UnHide()
        
        continue


    if quickAnnotation:
        firstCharEvent = event.split(":", 1)[0]
        if firstCharEvent.isdigit() and int(firstCharEvent) <= len(labels):
            index = int(firstCharEvent) - 1

            # if already in list, remove
            if labels[index] in imagesLabels[indexCurrentImage]:
                imagesLabels[indexCurrentImage].remove(labels[index])
            else:
                imagesLabels[indexCurrentImage].append(labels[index])

            setSelected(indexCurrentImage)  
            continue

    
window.close()

if not proceed:
    exit()

if len(missingAnnotation) == len(allImages):
    sg.Popup("Since there are no labeled images, the program will close.", title=":(")
    exit()

for missing in missingAnnotation:
    imagesLabels[image] = [defaultLabel]
    if defaultLabel not in labels: 
        labels.append(defaultLabel)

""" START OF DATABASE SAVE SCREN """

window = sg.Window('Image Classification Annotation', gui.layout_save_dataset)
pop = None
maintainContent = False

while True:

    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    if event == "maintainContent":
        maintainContent = values["maintainContent"]

        if os.path.exists(values['folder']) and os.listdir(values['folder']) and maintainContent:
            window['error_folder'].update("Attention! Folder not empty. Will merge any existing content.", text_color='maroon')
            continue

        window['error_folder'].update("")    

    if event == "folder" and values['folder']:
        if os.path.exists(values['folder']) and os.listdir(values['folder']) and maintainContent:
            window['error_folder'].update("Attention! Folder not empty. Will merge any existing content.", text_color='maroon')
            continue

        window['error_folder'].update("")

    if event == "go":
        destinationFolder = values["folder"]
        if not destinationFolder:
            continue

        train = int(values["train"])/100
        test = int(values["test"])/100
        val = int(values["val"])/100

        if train + test + val != 1:
            window['error_split'].update("Split ratio needs to total 100%!", text_color='maroon')
            continue

        window['error_split'].update("")
        window['error_folder'].update("")

        if not maintainContent:
            shutil.rmtree(destinationFolder, ignore_errors=True)
        
        if not os.path.exists(destinationFolder):
            os.mkdir(destinationFolder)

        for index in imagesLabels:
            imageAddress = allImages[index]
            imageLabels = imagesLabels[index]

            for label in imageLabels:
                destinationPath = destinationFolder + "/dataset/" + label
                if not os.path.exists(destinationFolder + "/dataset"):
                    os.mkdir(destinationFolder + "/dataset")
                if not os.path.exists(destinationPath):
                    os.mkdir(destinationPath)

                shutil.copy(imageAddress, destinationPath)
                
        try:
            window.Hide()
            pop = gui.popup("Processing...")
            splitfolders.ratio(destinationFolder + "/dataset", seed=1337, output=destinationFolder + "/temp", ratio=(train, test, val))
            shutil.copytree(destinationFolder + "/temp", destinationFolder, dirs_exist_ok=True)
            shutil.rmtree(destinationFolder + "/dataset", ignore_errors=True)
            shutil.rmtree(destinationFolder + "/temp", ignore_errors=True)
            pop.close()
            window.UnHide()
            sg.Popup("Done!", title=":)")
        except Exception as e:
            window.write_event_value('FINISH', None)
            sg.Popup(e, title="An error occured")

        shutil.rmtree(destinationFolder + "/dataset", ignore_errors=True)
        shutil.rmtree(destinationFolder + "/temp", ignore_errors=True)
            
        continue