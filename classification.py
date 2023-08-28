import os
import io
import sys
import splitfolders
import shutil
from glob import glob
from PIL import Image
import gui
from gui import sg

class ClassifImage:
    globalIndex = 0

    def __init__(self, path, name):
        self.index = ClassifImage.globalIndex
        ClassifImage.globalIndex += 1
        self.path = path
        self.name = name
        # list of Label
        self.labels = list()

def getLabelsNameList(vectorLabels):
    aux = list()
    for index in range(len(vectorLabels)):
        aux.append(str(index + 1) + ": " + vectorLabels[index])
    return aux

def loadImageAtIndex(window, index):
    image = Image.open(imagesLabels[index].path)
    image.thumbnail((700, 700))
    bio = io.BytesIO()
    image.save(bio, format="PNG")
    window["currentImage"].update(data=bio.getvalue())
    window["imageName"].update(imagesLabels[index].name)

def goToImage(window, indexToGo):
    global indexCurrentImage
    indexCurrentImage = indexToGo
    loadImageAtIndex(window, indexCurrentImage)
    
    aux = getLabelsNameList(imagesLabels[indexCurrentImage].labels)
    window["labels"].set_value(aux)
    window["previous"].update(disabled=False)
    window["next"].update(disabled=False)

    if indexCurrentImage == 0:
        window["previous"].update(disabled=True)

    if indexCurrentImage == len(imagesLabels) - 1:
        window["next"].update(disabled=True)

def populateImages():
    if os.path.exists(folderName + "/train") and os.path.exists(folderName + "/test"):
        
        names = list()
        for root, dirs, files in os.walk(folderName, topdown=True):
            
            for name in files:

                label = root.split("/")[-1]
                path = os.path.join(root, name)

                if name not in names:
                    names.append(name)
                    imagesLabels[names.index(name)] = Image(path=path, name=name)

                imagesLabels[names.index(name)].labels.append(label)

                if not label in labels:
                    labels.append(label)
    else:
        images = (folderName + '/*.png', folderName + '/*.jpg') # the tuple of file types
        allImages = list()
        for image in images:
            allImages.extend(glob(image))
        allImages = sorted(allImages)
        for index in range(len(allImages)):
            imagesLabels[index] = ClassifImage(allImages[index], allImages[index].split("/")[-1])


def transformNumpad(event):

    if event is None:
        return event

    if "KP_End" in event:
        return "1"
    if "KP_Down" in event:
        return "2"
    if "KP_Next" in event:
        return "3"
    if "KP_Left" in event:
        return "4"
    if "KP_Begin" in event:
        return "5"
    if "KP_Right" in event:
        return "6"
    if "KP_Home" in event:
        return "7"
    if "KP_Up" in event:
        return "8"
    if "KP_Prior" in event:
        return "9"
    
    return event

if len(sys.argv) < 2:
    sg.popup_no_buttons("Please provide the correct arguments.")
    exit()

def main():
    global imagesLabels, labels
    global folderName
    global indexCurrentImage
    
    folderName = sys.argv[1]
    # global lists and dicts initialization
    labels = list()
    imagesLabels = dict()
    missingAnnotation = list()

    indexCurrentImage = 0

    # populate images list
    populateImages()

    if not imagesLabels:
        sg.popup_no_buttons("Unfortunatly, the folder provided has no images", title=":(")
        os.system("python3 main.py")
        exit()

    # main window creation and keyboard bindings
    window = sg.Window('Image Classification Annotation', gui.layout_classification, finalize=True, return_keyboard_events=True)
    window['labelToAdd'].bind("<Return>", "_enter")
    window["labelToAdd"].set_focus(True)
    window["numberImages"].update("Images loaded:" + str(len(imagesLabels)))

    # control variables
    proceed = False
    firstQuickAnnotation = True
    quickAnnotation = False
    defaultLabel = ""

    # load first image 
    goToImage(window, indexCurrentImage)

    while True:

        event, values = window.read()
        # transform base numpad event 
        event = transformNumpad(event)

        if event in (sg.WIN_CLOSED, 'Exit'):
            break


        if event == "addLabel" or event == "labelToAdd" + "_enter":
            labelToAdd = values["labelToAdd"]

            if not labelToAdd:
                continue

            if labelToAdd in labels:
                window['error'].update("Label already in \navailable classes!", text_color='maroon')
                continue

            labels.append(labelToAdd)

            window["labels"].update(getLabelsNameList(labels))
            window["labelToAdd"].update("")
            window['error'].update("")
            
            aux = getLabelsNameList(imagesLabels[indexCurrentImage].labels)
            window["labels"].set_value(aux)

            continue


        if event == "removeLabel":
            labelToRemove = values["labelToAdd"]

            if not labelToRemove:
                continue

            if not labelToRemove in labels:
                window['error'].update("Label is non-existent!", text_color='maroon')
                continue

            for index in imagesLabels:
                image = imagesLabels[index]
                if labelToRemove in image.labels:
                    imagesLabels[index].labels.remove(labelToRemove)
                    
            labels.remove(labelToRemove)

            window["labels"].update(getLabelsNameList(labels))
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

                    for index in imagesLabels:
                        if labelToEdit in imagesLabels.labels:
                            imagesLabels[index].labels[labels.index(labelToEdit)] = replaceWith

                    labels[labels.index(labelToEdit)] = replaceWith
                    edit['error-replace'].update("")
                    break

            edit.close()
            
            window["labels"].update(getLabelsNameList(labels))
            window["labelToAdd"].update("")
            window['error'].update("")

            aux = getLabelsNameList(imagesLabels[indexCurrentImage].labels)
            window["labels"].set_value(aux)


        if event == "previous" or event == "Left:113":
            if indexCurrentImage - 1 < 0:
                continue
            
            goToImage(window, indexCurrentImage - 1)
            
            continue


        if event == "next" or event == "Right:114":
            if indexCurrentImage + 1 >= len(imagesLabels):
                continue
            
            goToImage(window, indexCurrentImage + 1)
            
            continue


        if event == "labels":
            listNames = getLabelsNameList(labels)
            aux = list()
            for value in values["labels"]:
                index = listNames.index(value)
                aux.append(labels[index])

            print(aux)
            imagesLabels[indexCurrentImage].labels = aux

            continue


        if event == "continue":
            missingAnnotation = list()
            for index in imagesLabels:
                image = (ClassifImage)(imagesLabels[index])
                if not image.labels:
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

            # disable input boxes
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

            for index in imagesLabels:
                image = imagesLabels[index]
                extra = ""
                if image.labels:
                    extra = " (" + ", ".join(image.labels) + ")"
                justNames.append(image.name + extra)

            window.hide()

            # creation of listbox layout
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
                    for index in imagesLabels:
                        image = imagesLabels[index]
                        color_bg = "powder blue" if image.labels else "light coral"
                        color_fg = "white" if image.index == indexCurrentImage else "black"
                        choose['justNames'].Widget.itemconfig(image.index, bg=color_bg, fg=color_fg)

                if event == "choose" or event == "justNames" + "_double":
                    select = values["justNames"]
                    if not select:
                        break
                    
                    index = justNames.index(select[0])
                    goToImage(window, index)
                    break


            choose.close()
            window.UnHide()
            
            continue


        if quickAnnotation:
            print(event)
            firstCharEvent = event.split(":", 1)[0]
            if firstCharEvent.isdigit() and int(firstCharEvent) <= len(labels):
                index = int(firstCharEvent) - 1

                # if already in list, remove
                if labels[index] in imagesLabels[indexCurrentImage].labels:
                    imagesLabels[indexCurrentImage].labels.remove(labels[index])
                else:
                    imagesLabels[indexCurrentImage].labels.append(labels[index])

                aux = getLabelsNameList(imagesLabels[indexCurrentImage].labels)
                print(aux)
                window["labels"].set_value(aux)
                continue

        
    window.close()

    if not proceed:
        exit()

    if len(missingAnnotation) == len(imagesLabels):
        sg.Popup("Since there are no labeled images, the program will close.", title=":(")
        exit()

    for missing in missingAnnotation:
        imagesLabels[missing] = [defaultLabel]
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

            # create temporary folder with classes and their corresponding images
            for index in imagesLabels:
                imageAddress = imagesLabels[index].path
                imageLabels = imagesLabels[index].labels

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
                
                # split folders in trian test and validation
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

if __name__ == "__main__":
    main()