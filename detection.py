import os
import io

import numpy as np
import sys
import splitfolders
import shutil
from glob import glob
from PIL import Image
import gui
from gui import sg

class Figure:
    def __init__(self, id, tlc, brc, label):
        self.tempID = id
        self.tlc = tlc
        self.brc = brc
        self.label = label

class ClassifImage:
    globalIndex = 0

    def __init__(self, path, name):
        self.index = ClassifImage.globalIndex
        ClassifImage.globalIndex += 1
        self.path = path
        self.name = name
        # list of Label
        self.labels = list()
        self.figures = list()


def getLabelsNameList(vectorLabels):
    aux = list()
    for label in vectorLabels:
        index = labels.index(label)
        aux.append(str(index + 1) + ": " + label)
    return aux


def loadImageAtIndex(window, index):
    global imageOriginal
    imageOriginal = Image.open(images[index].path)
    imageOriginal.thumbnail((1300, 700))
    bio = io.BytesIO()
    imageOriginal.save(bio, format="PNG")
    data=bio.getvalue()

    window["imageName"].update(images[index].name)

    image_width, image_height = imageOriginal.size
    graph.set_size((image_width, image_height))
    graph.change_coordinates((0, image_height),(image_width, 0))
    graph.DrawImage(data=data, location=(0,0)) if data else None

def loadImageFiguresAtIndex(index):
    global graph, labelsColors
    for figure in images[index].figures:
        tempID = graph.DrawRectangle(figure.tlc, figure.brc, line_color=labelsColors[figure.label], line_width=2)
        figure.tempID = tempID


def goToImage(window, indexToGo):
    global indexCurrentImage, currentLabel
    indexCurrentImage = indexToGo
    graph.Erase()
    loadImageAtIndex(window, indexCurrentImage)
    loadImageFiguresAtIndex(indexCurrentImage)
    
    window["previous"].update(disabled=False)
    window["next"].update(disabled=False)

    if indexCurrentImage == 0:
        window["previous"].update(disabled=True)

    if indexCurrentImage == len(images) - 1:
        window["next"].update(disabled=True)


    currentLabel = ""

def populateImages():
    if os.path.exists(folderName + "/train") and os.path.exists(folderName + "/test"):
        
        names = list()
        for root, dirs, files in os.walk(folderName, topdown=True):
            
            for name in files:

                label = root.split("/")[-1]
                path = os.path.join(root, name)

                if name not in names:
                    names.append(name)
                    images[names.index(name)] = Image(path=path, name=name)

                images[names.index(name)].labels.append(label)

                if not label in labels:
                    labels.append(label)
    else:
        imagesPaths = (folderName + '/*.png', folderName + '/*.jpg') # the tuple of file types
        allImages = list()
        for image in imagesPaths:
            allImages.extend(glob(image))
        allImages = sorted(allImages)
        for index in range(len(allImages)):
            images[index] = ClassifImage(allImages[index], allImages[index].split("/")[-1])


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

#if len(sys.argv) < 2:
#    sg.popup_no_buttons("Please provide the correct arguments.")

#    exit()

def getFigureAtLocation(figures, coord):
    global graph
    for fig in figures:
        p1, p2 = graph.GetBoundingBox(fig.tempID)
        x1, y1 = p1
        x2, y2 = p2
        x, y = coord
        if x1 <= x and x2 >= x and y1 <= y and y2 >= y:
            return fig.tempID, ((x2 - x1)//2, (y2 - y1)//2)

    return None, (0, 0)

def get_box_area(tlc, brc):
    x1, y1, x2, y2 = tlc[0], tlc[1], brc[0], brc[1]
    area = abs(x2 - x1) * abs(y2 - y1)
    return area

def delete_dotted_lines():
    global graph
    global dotted_lines
    for fig in dotted_lines:
        graph.DeleteFigure(fig)

    dotted_lines = list()

def draw_dotted_lines(pt1, pt2, color, thickness=1, style='dotted', gap=10):
    global graph
    global dotted_lines
    """
    Draw dotted lines. 
    Adopted from StackOverflow.
    """
    dist = ((pt1[0]-pt2[0])**2+(pt1[1]-pt2[1])**2)**0.5
    pts= []
    for i in  np.arange(0, dist, gap):
        r = i/dist
        x = int((pt1[0] * (1-r) + pt2[0] * r) + 0.5)
        y = int((pt1[1] * (1-r) + pt2[1] * r) + 0.5)
        p = (x,y)
        pts.append(p)

    if style == 'dotted':
        for p in pts:
            dotted_lines.append(graph.DrawCircle(p, thickness, color))

def pickTextColorBasedOnBgColor(bgColor):
    hex = bgColor.lstrip("#")
    red, green, blue = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
    return ("#000000" if (red*0.299 + green*0.587 + blue*0.114) > 186 else "#ffffff")

def main():
    global images, labels, labelsColors, currentLabel
    global folderName
    global indexCurrentImage, imageOriginal
    global graph, dotted_lines

    currentRect = None
    dotted_lines = list()
    start_rect = coord = (0, 0)
    drawBox = False
    
    #folderName = sys.argv[1]
    folderName = "/home/camicasa/Documents/image_annotate/test_images"
    # global lists and dicts initialization
    labels = list()
    labelsColors = dict()
    images = dict()
    missingAnnotation = list()

    indexCurrentImage = 0

    # populate images list
    populateImages()

    if not images:
        sg.popup_no_buttons("Unfortunatly, the folder provided has no images", title=":(")
        os.system("python3 main.py")
        exit()

    # main window creation and keyboard bindings
    window = sg.Window('Image Classification Annotation', gui.layout_detection, finalize=True, return_keyboard_events=True)
    graph = window.Element("graph")     # type: sg.Graph
    window['labelToAdd'].bind("<Return>", "_enter")
    window["labelToAdd"].set_focus(True)
    window["numberImages"].update("Images loaded:" + str(len(images)))

    # control variables
    proceed = False
    firstQuickAnnotation = True
    quickAnnotation = False
    currentLabel = ""

    # load first image 
    goToImage(window, indexCurrentImage)

    moveFigure =  False
    clickedFigure = None
    canMove = False
    moveRatio = (0, 0)

    while True:

        event, values = window.read()
        # transform base numpad event 
        event = transformNumpad(event)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        
        h = imageOriginal.height
        w = imageOriginal.width
        horizontal_pt1 = (0, coord[1])
        horizontal_pt2 = (w, coord[1])
        vertical_pt1 = (coord[0], 0)
        vertical_pt2 = (coord[0], h)

        delete_dotted_lines()
        draw_dotted_lines(horizontal_pt1, horizontal_pt2, "black")
        draw_dotted_lines(vertical_pt1, vertical_pt2, "black")

        if event == "graph" + "+MOVE":
            # Current coordinate. Updated every instant with the cursor.
            x, y = values["graph"]
            coord = (x, y)

        if event == "graph":
            #Clicked point.
            x, y = values["graph"]

            coord = (x, y)
            
            if moveFigure and clickedFigure:
                drawBox = False

                graph.RelocateFigure(clickedFigure, x-moveRatio[0], y-moveRatio[1])
                
                for fig in images[indexCurrentImage].figures:
                   if fig.tempID == clickedFigure:
                       fig.tlc = (x-moveRatio[0], y-moveRatio[1])
                       fig.brc = (x+moveRatio[0], y+moveRatio[1])
                       break
                continue

            #if not figures:
            if not drawBox:
                if values["moveFigures"]:
                    clickedFigure, moveRatio = getFigureAtLocation(images[indexCurrentImage].figures, coord)
                    if clickedFigure:
                        moveFigure = True
                        graph.BringFigureToFront(clickedFigure)
                elif currentLabel:
                    start_rect = coord
                    drawBox = True


        if event == "graph" + "+UP": 
            if moveFigure:
                moveFigure = False
                clickedFigure = None
                continue

            if drawBox:
                drawBox = False
                area = get_box_area(start_rect, coord)
                if start_rect != coord and area > 30:
                    tempID = graph.DrawRectangle(start_rect, coord, line_color=labelsColors[currentLabel], line_width=2)
                    figure = Figure(tempID, start_rect, coord, currentLabel)
                    images[indexCurrentImage].figures.append(figure)
            

        graph.DeleteFigure(currentRect)
        if drawBox and start_rect != coord:
            currentRect = graph.DrawRectangle(start_rect, coord, line_color=labelsColors[currentLabel], line_width=2)

        if event == "colorPicked":
            color = values["colorPicked"]
            window["colorChooser"].update(button_color=color)

        if event == "addLabel" or event == "labelToAdd" + "_enter":
            color = values["colorPicked"]
            labelToAdd = values["labelToAdd"]

            if not labelToAdd or not color:
                continue

            if labelToAdd in labels:
                window['error'].update("Label already in \navailable classes!", text_color='maroon')
                continue

            labels.append(labelToAdd)
            labelsColors[labelToAdd] = color

            window["labels"].update(getLabelsNameList(labels))

            for label in labels:
                bgColor = labelsColors[label]
                fgColor = pickTextColorBasedOnBgColor(bgColor)
                window["labels"].Widget.itemconfig(labels.index(label), bg=bgColor, fg=fgColor)
            
            window["labelToAdd"].update("")
            window['error'].update("")
            
            aux = getLabelsNameList(images[indexCurrentImage].labels)
            window["labels"].set_value(aux)

            continue


        if event == "removeLabel":
            labelToRemove = values["labelToAdd"]

            if not labelToRemove:
                continue

            if not labelToRemove in labels:
                window['error'].update("Label is non-existent!", text_color='maroon')
                continue

            for index in images:
                image = images[index]
                if labelToRemove in image.labels:
                    images[index].labels.remove(labelToRemove)
                    
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

                    for index in images:
                        if labelToEdit in images.labels:
                            images[index].labels[labels.index(labelToEdit)] = replaceWith

                    labels[labels.index(labelToEdit)] = replaceWith
                    edit['error-replace'].update("")
                    break

            edit.close()
            
            window["labels"].update(getLabelsNameList(labels))
            window["labelToAdd"].update("")
            window['error'].update("")

            aux = getLabelsNameList(images[indexCurrentImage].labels)
            window["labels"].set_value(aux)


        if event == "previous" or event == "Left:113":
            if indexCurrentImage - 1 < 0:
                continue
            
            goToImage(window, indexCurrentImage - 1)
            
            continue


        if event == "next" or event == "Right:114":
            if indexCurrentImage + 1 >= len(images):
                continue
            
            goToImage(window, indexCurrentImage + 1)
            
            continue


        if event == "labels":
            # listNames = getLabelsNameList(labels)
            # aux = list()
            # for value in values["labels"]:
            #     index = listNames.index(value)
            #     aux.append(labels[index])

            # images[indexCurrentImage].labels = aux
            listNames = getLabelsNameList(labels)
            
            if not values["labels"]:
                continue


            select = values["labels"][0]
            index = listNames.index(select)
            currentLabel = labels[index]

            continue


        if event == "continue":
            missingAnnotation = list()
            for index in images:
                image = (ClassifImage)(images[index])
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

            for index in images:
                image = images[index]
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
                    for index in images:
                        image = images[index]
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
            firstCharEvent = event.split(":", 1)[0]
            if firstCharEvent.isdigit() and int(firstCharEvent) <= len(labels):
                index = int(firstCharEvent) - 1

                # if already in list, remove
                if labels[index] in images[indexCurrentImage].labels:
                    images[indexCurrentImage].labels.remove(labels[index])
                else:
                    images[indexCurrentImage].labels.append(labels[index])

                aux = getLabelsNameList(images[indexCurrentImage].labels)
                window["labels"].set_value(aux)
                continue

        
    window.close()

    if not proceed:
        exit()

    if len(missingAnnotation) == len(images):
        sg.Popup("Since there are no labeled images, the program will close.", title=":(")
        exit()

    for missing in missingAnnotation:
        images[missing] = [defaultLabel]
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
            for index in images:
                imageAddress = images[index].path
                imageLabels = images[index].labels

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