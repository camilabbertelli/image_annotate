## @package camicasa
# package for all functions, methods and classes create by Camila Bertelli

import os
import io
import sys
import gui
import shutil
import yaml
import random
import numpy as np
from glob import glob
from PIL import Image
from gui import sg
from collections import OrderedDict

## Class destinated to store information about figures present in an image in the detection context
class Figure:

    ## The constructor
    # @param self The object pointer
    # @param id ID generated bt the function Graph.DrawRectangle from PySimpleGUI
    # @param tlc tuple representing top-left corner point of figures bounding box 
    # @param brc tuple representing bottom-right corner point of figures bounding box
    # @param label string label associated with that figure
    # @param normalizedPoints boolean that represents if the points range from (0-1), 
    # being normalized by the width and height of image. default False
    def __init__(self, id : int, tlc: tuple[float, float], brc: tuple[float, float], label : str, normalizedPoints : bool = False) -> 'Figure':
        self.tempID = id
        self.tlc = tlc
        self.brc = brc
        self.label = label
        self.annotationID = (None, None)
        self.normalized = normalizedPoints

    ## Returns True if figure is normalized by width or height
    # @param self The object pointer
    def hasNormalizedPoints(self) -> bool:
        return self.normalized

    ## Denormalize figures tlc and brc, presenting them in range of image size
    # @param self The object pointer
    # @param width image width to consider
    # @param height image height to consider
    def denormalizePoints(self, width : float, height : float) -> None:
        if self.normalized:
            self.normalized = False
            self.tlc = (self.tlc[0] * width, self.tlc[1] * height)
            self.brc = (self.brc[0] * width, self.brc[1] * height)

## Class destinated to store information about an image in the detection context
class DetectImage:
    globalIndex = 0

    ## The constructor
    # @param self The object pointer
    # @param path The complete image path
    # @param name The image the image will go by, containing the extension, i.e. image.jpg, 001.png
    def __init__(self, path : str, name : str, width : int = 0, height : int = 0) -> 'DetectImage':
        self.index = DetectImage.globalIndex
        DetectImage.globalIndex += 1
        self.path = path
        self.name = name
        self.figures = list()
        self.width = width
        self.height = height
        
## Returns list of strings to be presented in the labels listbox,
# considering number on the left
# @param vectorLabels vector of labels to add indexes on the left
def getLabelsNameList(vectorLabels : list) -> list:
    aux = list()
    for label in vectorLabels:
        index = labels.index(label)
        aux.append(str(index + 1) + ": " + label)
    return aux

## Loads image on image container(sg.Graph) and updates related information 
# @param window PySimpleGUI window to update
# @param index DetectImage inloadImadex in images list
def loadImageAtIndex(window : sg.Window, index : int) -> None:
    global graph, images

    imageOriginal = Image.open(images[index].path)
    imageOriginal.thumbnail((1300, 700))
    bio = io.BytesIO()
    imageOriginal.save(bio, format="PNG")
    data=bio.getvalue()

    window["imageName"].update(images[index].name)

    images[index].width, images[index].height = imageOriginal.size
    graph.set_size((images[index].width, images[index].height))
    graph.change_coordinates((0, images[index].height),(images[index].width, 0))

    graph.DrawImage(data=data, location=(0,0)) if data else None

## Loads figures on image container(sg.Graph) given the desired image and optionally a label
# @param index DetectImage index in images list
# @param label 
# @param label optional label to load. if none given, will load everything
def loadImageFiguresAtIndex(index : int, label : str = None) -> None:
    global graph, labelsColors
    deleteFigures(index)
    
    for figure in images[index].figures:
        if label is None or not label or (label is not None and label == figure.label):
            figure.denormalizePoints(images[index].width, images[index].height)
            tempID = graph.DrawRectangle(figure.tlc, figure.brc, line_color=labelsColors[figure.label], line_width=2)
            figure.tempID = tempID
            drawAnnotateLabel(figure)

## Loads labels in labels listbox accordingly
# @param window PySimpleGUI window to update
def loadLabelsListBox(window : sg.Window) -> None:
    global labels, labelsColors

    window["labels"].update(getLabelsNameList(labels))

    for label in labels:
        bgColor = labelsColors[label]
        fgColor = pickTextColorBasedOnBgColor(bgColor)
        window["labels"].Widget.itemconfig(labels.index(label), bg=bgColor, fg=fgColor)

## Performs whole operation of changing from one image to another in the visualizer
# @param window PysimpleGUI window to update
# @param indexToGo index from images list to load the image and relative information
def goToImage(window : sg.Window, indexToGo : int) -> None:
    global indexCurrentImage, currentLabel, images, showSelected
    indexCurrentImage = indexToGo

    graph.Erase()
    loadImageAtIndex(window, indexCurrentImage)
    
    window["previous"].update(disabled=False)
    window["next"].update(disabled=False)

    if indexCurrentImage == 0:
        window["previous"].update(disabled=True)

    if indexCurrentImage == len(images) - 1:
        window["next"].update(disabled=True)

    label = None
    if showSelected:
        label = currentLabel
    loadImageFiguresAtIndex(indexCurrentImage, label)

## Populates the images list, considering a folder with only images or
# a folder with the format of a detection folder
def populateImages() -> None:
    # check existence of previous yaml to initialize labels list
    yamls = glob(folderName + '/*.yaml')
    if yamls:
        with open(yamls[0], "r") as file:
            oldYaml = yaml.safe_load(file)
            for labelIndex, a in enumerate(oldYaml["names"]):       
                element = oldYaml["names"][a] if isinstance(oldYaml["names"], dict) else a
                labelIndex = int(a) if isinstance(oldYaml["names"], dict) else labelIndex

                sizeLabels = len(labels)
                if sizeLabels <= labelIndex:
                    for i in range(labelIndex - sizeLabels + 1):
                        labels.append("")
                        labelsColors[element] = generateColor()
                        
                if element not in labels:
                    labels[labelIndex] = element

    if not (os.path.exists(folderName + "/labels") and os.path.exists(folderName + "/images")):
        imagesPaths = (folderName + '/*.png', folderName + '/*.jpg') # the tuple of file types
        allImages = list()
        for image in imagesPaths:
            allImages.extend(glob(image))
        allImages = sorted(allImages)
        for index in range(len(allImages)):
            images[index] = DetectImage(allImages[index], allImages[index].split("/")[-1])
        return
        
    names = list()
    foldersName = OrderedDict()
    for root, dirs, files in os.walk(folderName + "/images/", topdown=True):
        
        for name in files:

            path = os.path.join(root, name)
            folder = root.split("/")[-1]
            name_no_extension = name.split(".")[0]
            extension = name.split(".")[-1]

            if not name.endswith(".jpg") and not name.endswith(".png"):
                continue
                
            if name not in foldersName:
                foldersName[name] = list()
            
            if folder not in foldersName[name]:
                foldersName[name].append(folder)

            actualName = name
            
            if (folder in foldersName[name] and len(foldersName[name]) > 1) or \
                (folder not in foldersName[name]):
                actualName = name_no_extension + "_" + str(len(foldersName[name]) - 1) + "." + extension
                os.rename(path, root + "/" + actualName)
                os.rename(folderName + "/labels/" + folder + "/" + name.split(".")[0] + ".txt", 
                          folderName + "/labels/" + folder + "/" + actualName.split(".")[0] + ".txt")
            
            if actualName not in names:
                names.append(actualName)
                        
            index = names.index(actualName)
            if index not in images:
                images[index] = DetectImage(path=path, name=actualName)
                images[index].figures = list()

            fileFigures = glob(folderName + "/labels/" + folder + "/" + actualName.split(".")[0] + ".txt")

            if not fileFigures:
                continue

            with open(fileFigures[0], "r") as f:
                figures = f.readlines()
                for fig in figures:
                    fig = fig.replace("\n", "")
                    fig = fig.split(" ")

                    labelIndex = int(fig[0])
                    centerX = float(fig[1])
                    centerY = float(fig[2])
                    width = float(fig[3])
                    height = float(fig[4])

                    # update labels list

                    sizeLabels = len(labels)
                    if sizeLabels <= labelIndex:
                        for i in range(sizeLabels - labelIndex + 1):
                            labels.append("")

                    if not labels[labelIndex]:
                        labels[labelIndex] = str(labelIndex)
                        labelsColors[str(labelIndex)] = generateColor()

                    tlc = (centerX - (width/2), centerY - (height/2))
                    brc = (tlc[0] + width, tlc[1] + height)
                    images[index].figures.append(Figure(0, tlc, brc, labels[labelIndex], normalizedPoints = True))


## Auxiliary function to transform the event generated by the numpad to trigger the corresponding action
# @param event PySimpleGUI event generated from a sg.Window
def transformNumpad(event : str) -> str:

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

## Auxiliary method that deletes from the graph associated figures 
# with a certain label or all figures (except the image itself).
# @param index image index to consider
# @param label optional label to delete. if none given, will delete everything
def deleteFigures(index : int, label : str = None) -> None:
    global graph

    for fig in images[index].figures:
        if (label is None) or (label is not None and fig.label == label):
            graph.DeleteFigure(fig.tempID)
            graph.DeleteFigure(fig.annotationID[0])
            graph.DeleteFigure(fig.annotationID[1])

## Handles the small annotation with the label name rectangle on top of every drawn figure
# @param figure Figure that will receive annotation
def drawAnnotateLabel(figure : Figure) -> None:
    global graph 

    text = figure.label
    tlc = figure.tlc

    graph.DeleteFigure(figure.annotationID[0])
    graph.DeleteFigure(figure.annotationID[1])

    bgColor = labelsColors[text]
    
    fgColor = pickTextColorBasedOnBgColor(bgColor)

    textID = graph.DrawText(text, location=(tlc[0], tlc[1] - 12), color=fgColor, font=gui.bodyFont)
    p1, p2 = graph.GetBoundingBox(textID)
    
    rectID = graph.DrawRectangle(p1, p2, bgColor, bgColor, line_width=2)

    graph.BringFigureToFront(textID)

    figure.annotationID = (textID, rectID)

## Returns Figure on top of sg.Graph at the given coordinates 
# @param figures list of figures to search
# @param coord tuple of points
def getFigureAtLocation(figures: list, coord : tuple[float, float]) -> Figure:
    global graph

    label = None
    if showSelected:
        label = currentLabel

    for fig in figures:
        try:
            if (label is None) or (label is not None and fig.label == label):
                p1, p2 = graph.GetBoundingBox(fig.tempID)
                x1, y1 = p1
                x2, y2 = p2
                x, y = coord
                if x1 <= x and x2 >= x and y1 <= y and y2 >= y:
                    return fig
        except Exception as e:
            return None
    return None

## Return the area of a bounding box represented by two points
# @param tlc point 1
# @param brc point 2
def getBoxArea(tlc : tuple[float, float], brc : tuple[float, float]) -> float:
    x1, y1, x2, y2 = tlc[0], tlc[1], brc[0], brc[1]
    area = abs(x2 - x1) * abs(y2 - y1)
    return area

## Auxiliary function to delete the figures that represent the dotted lines on the sg.Graph
def deleteDottedLines() -> None:
    global graph, dotted_lines

    for fig in dotted_lines:
        graph.DeleteFigure(fig)

    dotted_lines = list()

## Auxiliary function to draw all of the dotted lines in a cross format
# @param pt1 start of the line
# @param pt2 end of the line
# @param color color of the line. default "black"
def drawDottedLines(pt1 : tuple[int, int], pt2 : tuple[int, int], color : str = "black") -> None:
    global graph, dotted_lines

    thickness = 1
    gap = 10

    dist = ((pt1[0]-pt2[0])**2+(pt1[1]-pt2[1])**2)**0.5
    pts= []
    for i in  np.arange(0, dist, gap):
        r = i/dist
        x = int((pt1[0] * (1-r) + pt2[0] * r) + 0.5)
        y = int((pt1[1] * (1-r) + pt2[1] * r) + 0.5)
        p = (x,y)
        pts.append(p)

    for p in pts:
        dotted_lines.append(graph.DrawCircle(p, thickness, color))

## Given a color returns if its best to have a foreground text of white or black
# @param bgColor color to analyze
def pickTextColorBasedOnBgColor(bgColor : str) -> str:
    hex = bgColor.lstrip("#")
    red, green, blue = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
    return ("#000000" if (red*0.299 + green*0.587 + blue*0.114) > 186 else "#ffffff")

## Generates random hex color
def generateColor() -> str:
    color = random.randrange(0, 2**24)
    hex_color = hex(color)[2:]
    
    while len(hex_color) != 6:
        hex_color += "0"

    return "#" + hex_color

## Given the list displayed in the listbox, returns the corresponding selected label
# @param values list of values generated from a sg.Window read()
def selectedToLabel(values : list) -> str:
    global labels

    listNames = getLabelsNameList(labels)
            
    if not values["labels"]:
        return ""

    select = values["labels"][0]
    index = listNames.index(select)

    return labels[index]


def isWithinBounds(pt1 : tuple[float, float], pt2 : tuple[float, float]) -> bool :
    global graph

    bounds_pt1 = (0, 0) 
    bounds_pt2 = graph.get_size()

    return (bounds_pt1[0] <= pt1[0] < pt2[0] < bounds_pt2[0] and 
            bounds_pt1[1] <= pt1[1] < pt2[1] < bounds_pt2[1])

def main():
    global labels, labelsColors, currentLabel
    global folderName
    global images, indexCurrentImage
    global graph, dotted_lines, showSelected
    
    # arguments check
    if len(sys.argv) < 2:
        sg.popup_no_buttons("Please provide the correct arguments.")

        exit()

    folderName = sys.argv[1]

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

    # control variables
    proceed = False
    firstQuickAnnotation = True
    quickAnnotation = False
    drawBox = False
    showSelected = False
    dragging = False
    dotted_lines = list()
    start_rect = coord = (0, 0)
    currentRect = None
    currentLabel = ""
    lastChoosenColor = "#d9d9d9"

    # main window creation and keyboard bindings
    window = sg.Window('Image Classification Annotation', gui.layout_detection, finalize=True, return_keyboard_events=True)
    graph = window.Element("graph")
    window['labelToAdd'].bind("<Return>", "_enter")
    window["labelToAdd"].set_focus(True)
    window["numberImages"].update("Images loaded:" + str(len(images)))

    # load first image 
    goToImage(window, indexCurrentImage)
    # load labels if there are any
    loadLabelsListBox(window)

    while True:

        event, values = window.read()
        # transform base numpad event 
        event = transformNumpad(event)

        if event in (sg.WIN_CLOSED, 'Exit'):
            break

        # coord is the position of the mouse on the sg.Graph
        # if not yet captured, coord == (0, 0)

        horizontal_pt1 = (0, coord[1])
        horizontal_pt2 = (images[indexCurrentImage].width, coord[1])
        vertical_pt1 = (coord[0], 0)
        vertical_pt2 = (coord[0], images[indexCurrentImage].height)

        deleteDottedLines()
        drawDottedLines(horizontal_pt1, horizontal_pt2)
        drawDottedLines(vertical_pt1, vertical_pt2)

        # needs to be done everytime for smooth drawing effect
        graph.DeleteFigure(currentRect)

        # move mouse event
        if event == "graph" + "+MOVE":
            x, y = values["graph"]
            coord = (x, y)

        # click on graph event
        if event == "graph":
            x, y = values["graph"]

            coord = (x, y)

            if not dragging:
                start_rect = coord
                dragging = True
                drag_figure = getFigureAtLocation(images[indexCurrentImage].figures, coord)
                lastxy = coord
            
            delta_x, delta_y = x - lastxy[0], y - lastxy[1]
            lastxy = x,y

            if values["moveFigures"] and (drag_figure is not None):
                for fig in images[indexCurrentImage].figures:
                    if fig.tempID == drag_figure.tempID:
                        
                        new_tlc_x = fig.tlc[0]+delta_x
                        new_tlc_y = fig.tlc[1]+delta_y
                        new_brc_x = fig.brc[0]+delta_x
                        new_brc_y = fig.brc[1]+delta_y

                        if not isWithinBounds((new_tlc_x, new_tlc_y), (new_brc_x, new_brc_y)):
                            
                            graph.update()
                            break

                        graph.move_figure(fig.tempID, delta_x, delta_y)
                        
                        graph.BringFigureToFront(fig)
                        images[indexCurrentImage].figures.remove(fig)
                        images[indexCurrentImage].figures.insert(0, fig)

                        fig.tlc = (new_tlc_x, new_tlc_y)
                        fig.brc = (new_brc_x, new_brc_y)
                        drawAnnotateLabel(fig)
                        
                        break
            elif start_rect != coord and currentLabel:
                drawBox = True
                currentRect = graph.DrawRectangle(start_rect, coord, line_color=labelsColors[currentLabel], line_width=2)

        # mouse click up event
        if event == "graph" + "+UP": 
            
            # draw and consolidate figure drawn
            if dragging and drawBox:
                drawBox = False
                area = getBoxArea(start_rect, coord)
                if start_rect != coord and area > 30 and currentLabel and isWithinBounds(start_rect, coord):
                    tempID = graph.DrawRectangle(start_rect, coord, line_color=labelsColors[currentLabel], line_width=2)
                    figure = Figure(tempID, start_rect, coord, currentLabel)
                    images[indexCurrentImage].figures.append(figure)
                    drawAnnotateLabel(figure)
            start_rect = coord = (0, 0)
            drag_figure = None
            dragging = False

        # checkbox "Show only figures from selected label" event
        if event == "showFromSelected":
            label = None
            showSelected = values["showFromSelected"]

            if showSelected:
                label = currentLabel
            loadImageFiguresAtIndex(indexCurrentImage, label)

            continue

        # checkbox "Show only figures from selected label" event
        if event.startswith("m:") and window.FindElementWithFocus() != window["labelToAdd"]:
            window["moveFigures"].update(value=(not values["moveFigures"]))
            continue

        # clear image event
        if event == "clear":
            deleteFigures(indexCurrentImage)
            images[indexCurrentImage].figures = list()

            continue

        # color picker event
        if event == "colorPicked":
            color = values["colorPicked"]
            if len(color) == len(lastChoosenColor):
                lastChoosenColor = color
            window["colorChooser"].update(button_color=lastChoosenColor)
            continue

        # add new label event
        if event == "addLabel" or event == "labelToAdd" + "_enter":
            color = lastChoosenColor
            labelToAdd = values["labelToAdd"]

            if not labelToAdd or not color:
                continue

            if labelToAdd in labels:
                window['error'].update("Label already in \navailable classes!", text_color='maroon')
                continue

            labels.append(labelToAdd)
            labelsColors[labelToAdd] = color

            loadLabelsListBox(window)
            window["labels"].update(set_to_index=[labels.index(labelToAdd)])
            currentLabel = labelToAdd
            
            window["labelToAdd"].update("")
            window['error'].update("")
            
            continue

        # remove label event
        if event == "removeLabel":
            labelToRemove = values["labelToAdd"]
            clearSelected = False
            all = False
            close = False
            if not labelToRemove:
                if values["labels"]:
                    labelToRemove = selectedToLabel(values)
                    clearSelected = True
                else:
                    continue

            if not labelToRemove in labels:
                window['error'].update("Label is non-existent!", text_color='maroon')
                continue

            # confirmation of removal window
            remove_space = [[sg.Push(),sg.Text("Remove \"" + labelToRemove + "\" from:", font=gui.subtitleFont), sg.Push()],
                            [sg.Push(),sg.Button("All images", key="all", font=gui.bodyFont), sg.Push(), sg.Button("This image", key="this", font=gui.bodyFont),sg.Push()]]
            
            remove = sg.Window('Remove label', remove_space, keep_on_top=True, finalize=True)
            while (True):
                event, values = remove.read()

                if event in (sg.WIN_CLOSED, 'Exit'):
                    close = True
                    break

                if event == "all":
                    all = True
                    break

                if event == "this":
                    break
            
            remove.close()

            if close:
                continue

            for index in images:
                if not all and index != indexCurrentImage:
                    continue

                image = images[index]
                for figure in image.figures.copy():
                    if figure.label == labelToRemove:
                        deleteFigures(index, figure.label)
                        images[index].figures.remove(figure)

                if not all and index == indexCurrentImage:
                    break
            
            if all:
                labels.remove(labelToRemove)

            window["labelToAdd"].update("")
            window['error'].update("")

            loadLabelsListBox(window)

            if clearSelected:
                window["labels"].set_value([])
                currentLabel = ""

            continue

        # edit label event
        if event == "editLabel":
            labelToEdit = values["labelToAdd"]
            if not labelToEdit:
                if values["labels"]:
                    labelToEdit = selectedToLabel(values)
                else:
                    continue

            if labelToEdit not in labels:
                window['error'].update("Label is non-existent!", text_color='maroon')
                continue

            replaceWith = labelToEdit

            originalColor = labelsColors[labelToEdit]
            lastChoosenColorEdit = originalColor
            
            # creation of edit window
            replace_space = [[sg.Push(),sg.Text("Replace \"" + labelToEdit + "\" with:", font=gui.subtitleFont),sg.Push()],
                            [sg.Push(),sg.Input(replaceWith, key="replaceWith", font=gui.bodyFont),sg.ColorChooserButton(button_text="", target="colorPickedEdit", key="colorChooserEdit", button_color=originalColor, bind_return_key=True), sg.Push()],
                            [sg.Push(),sg.Text(key="error-replace", font=gui.bodyFont),sg.Push()],
                            [sg.Push(),sg.Button("Save", key="save", font=gui.bodyFont),sg.Push()],
                            [sg.Input(originalColor, key="colorPickedEdit", visible=False, enable_events=True)]]
            

            edit = sg.Window('Edit label', replace_space, keep_on_top=True, finalize=True, return_keyboard_events=True)

            edit['replaceWith'].bind("<Return>", "_enter")

            while (True):
                event, values = edit.read()

                if event in (sg.WIN_CLOSED, 'Exit'):
                    break

                if event == "colorPickedEdit":
                    color = values["colorPickedEdit"]
                    if len(color) == len(lastChoosenColorEdit):
                        lastChoosenColorEdit = color
                    edit["colorChooserEdit"].update(button_color=lastChoosenColorEdit)


                if event == "save" or event == "replaceWith" + "_enter":

                    replaceWith = values["replaceWith"]
                    colorReplace = lastChoosenColorEdit

                    if not replaceWith or not colorReplace:
                        replaceWith = labelToEdit
                        colorReplace = originalColor
                        continue

                    labelsColors[labelToEdit] = colorReplace

                    if replaceWith == labelToEdit:
                        break

                    if replaceWith in labels:
                        edit['error-replace'].update("Label already exists", text_color='maroon')
                        replaceWith = labelToEdit
                        continue

                    for index in images:
                        for fig in images[index].figures:
                            if fig.label == labelToEdit:
                                fig.label = replaceWith

                    labels[labels.index(labelToEdit)] = replaceWith
                    currentLabel = replaceWith
                    labelsColors[replaceWith] = labelsColors[labelToEdit]
                    del labelsColors[labelToEdit]

                    edit['error-replace'].update("")
                    break

            edit.close()
            

            window["labelToAdd"].update("")
            window['error'].update("")

            label = None
            if showSelected:
                label = currentLabel
            loadImageFiguresAtIndex(indexCurrentImage, label)
            loadLabelsListBox(window)

            window["labels"].update(set_to_index=[labels.index(replaceWith)])

        # previous button event
        if event == "previous" or event == "Left:113":
            if indexCurrentImage - 1 < 0:
                continue
            
            goToImage(window, indexCurrentImage - 1)
            
            continue

        # next button event
        if event == "next" or event == "Right:114":
            if indexCurrentImage + 1 >= len(images):
                continue
            
            goToImage(window, indexCurrentImage + 1)
            
            continue

        # click on labels listbox event
        if event == "labels":
            listNames = getLabelsNameList(labels)
            
            if not values["labels"]:
                continue

            select = values["labels"][0]
            index = listNames.index(select)

            currentLabel = selectedToLabel(values)

            label = None
            if showSelected:
                label = currentLabel
            loadImageFiguresAtIndex(indexCurrentImage, label)

            continue

        # bring figure to front event (right-click at a specific figure)
        if event == 'Bring to front':
            if values['graph'] == (None, None):
                continue

            fig = getFigureAtLocation(images[indexCurrentImage].figures, values["graph"])
            if fig is not None:
                graph.BringFigureToFront(fig)
                images[indexCurrentImage].figures.remove(fig)
                images[indexCurrentImage].figures.insert(0, fig)

            continue

        # send figure to back event (right-click at a specific figure)
        if event == 'Send to back':
            if values['graph'] == (None, None):
                continue

            fig = getFigureAtLocation(images[indexCurrentImage].figures, values["graph"])
            if fig is not None:
                graph.SendFigureToBack(fig)
                images[indexCurrentImage].figures.remove(fig)
                images[indexCurrentImage].figures.insert(len(images[indexCurrentImage].figures), fig)

            continue

        # erase figure event (right-click at a specific figure)
        if event == 'Erase item':
            if values['graph'] == (None, None):
                continue

            fig = getFigureAtLocation(images[indexCurrentImage].figures, values["graph"])
            if fig is not None:
                graph.DeleteFigure(fig.tempID)
                graph.DeleteFigure(fig.annotationID[0])
                graph.DeleteFigure(fig.annotationID[1])
                images[indexCurrentImage].figures.remove(fig)
            
            continue

        # proceed to the next phase event
        if event == "continue":
            missingAnnotation = list()
            for index in images:
                image = images[index]
                if not image.figures:
                    missingAnnotation.append(index)

            ch = "No"
            if not missingAnnotation:
                ch = sg.popup_yes_no("  Once you continue and move on to the next phase, you won't be able to go back.\n" \
                                    "  Do you wish to proceed?",  title="Are you sure?")
            else:
                ch = sg.popup_yes_no("  Atention! You have " + str(len(missingAnnotation)) + " image(s) with no objects annotated!\n" \
                                    "  Go to 'All images' to check what you missed!\n\n" \
                                    "  Once you continue and move on to the next phase, you won't be able to go back.\n" \
                                    "  Do you wish to proceed?",  title="Are you sure?")

            if ch == "Yes":
                proceed = True
                break

            continue

        # show relation of all images event
        if event == "allImages":
            justNames = list()

            # gather all labels associated with an especific image and its figures
            for index in images:
                image = images[index]
                extra = ""
                
                figLabels = list()
                for fig in image.figures:
                    if fig.label not in figLabels:
                        figLabels.append(fig.label)

                figLabels.sort()
                
                if figLabels:
                    extra = " (" + ", ".join(figLabels) + ")"
                
                justNames.append(image.name + extra)


            # creation of listbox layout
            layout_all_images = list()
            layout_all_images = [[sg.Push(),sg.Text("Images and their state (Labeled, Unlabeled)", font=gui.subtitleFont), sg.Push()],
                            [sg.Push(), sg.Listbox(values=justNames, size=(30, 30), enable_events=True,horizontal_scroll=True,
                                                font=gui.bodyFont,key="justNames", bind_return_key=True), sg.Push()],
                            [sg.Column([])],
                            [sg.Push(), sg.Button("Go to image", key="choose", font=gui.bodyFont), sg.Push()]]
            
            choose = sg.Window('Choose file', layout_all_images, keep_on_top=True, finalize=True)
            choose["justNames"].bind('<Double-Button-1>' , "_double")

            # color code elements
            for index in images:
                image = images[index]
                color_bg = "powder blue" if image.figures else "light coral"
                color_fg = "white" if image.index == indexCurrentImage else "black"
                choose['justNames'].Widget.itemconfig(image.index, bg=color_bg, fg=color_fg)
            
            while (True):
                event, values = choose.read()

                if event in (sg.WIN_CLOSED, 'Exit'):
                    break

                if event == "choose" or event == "justNames" + "_double":
                    select = values["justNames"]
                    if not select:
                        break
                    
                    index = justNames.index(select[0])
                    goToImage(window, index)
                    break


            choose.close()
            
            continue

        # enable/disable "quickAnnotation" feature event 
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
            window["addLabel"].update(disabled=quickAnnotation)
            window["removeLabel"].update(disabled=quickAnnotation)
            window["editLabel"].update(disabled=quickAnnotation)

            state = "ON" if quickAnnotation else "OFF"
            window["quickAnnotation"].update(state)

            continue

        # handle numpad and number keyboard keys when quickAnnotation is active
        if quickAnnotation:
            firstCharEvent = event.split(":", 1)[0]
            if firstCharEvent.isdigit() and int(firstCharEvent) <= len(labels):
                index = int(firstCharEvent) - 1

                currentLabel = labels[index]
                window["labels"].update(set_to_index=[index])

                continue

            if firstCharEvent == "m":
                window["moveFigures"].update(value=(not values["moveFigures"]))

        
    window.close()

    if not proceed:
        exit()

    if len(missingAnnotation) == len(images):
        sg.Popup("Since there are no labeled images, the program will close.", title=":(")
        exit()

    """ START OF DATABASE SAVE SCREN """

    window = sg.Window('Image Classification Annotation', gui.layout_save_dataset)
    pop = None
    maintainContent = False

    while True:

        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'Exit'):
            break

        # maintain content event
        # if checked, doesn't wipe out content on the selected destination folder
        if event == "maintainContent":
            maintainContent = values["maintainContent"]

            if os.path.exists(values['folder']) and os.listdir(values['folder']) and maintainContent:
                window['error_folder'].update("Attention! Folder not empty. Will merge any existing content.", text_color='maroon')
                continue

            window['error_folder'].update("")    

        # select destination folder event
        if event == "folder" and values['folder']:
            if os.path.exists(values['folder']) and os.listdir(values['folder']) and maintainContent:
                window['error_folder'].update("Attention! Folder not empty. Will merge any existing content.", text_color='maroon')
                continue

            window['error_folder'].update("")

        # saves dataset
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

            window.Hide()
            pop = gui.popup("Processing...")

            imagesWithFigures = list()
            for img in images:
                if img not in missingAnnotation:
                    imagesWithFigures.append(img)

            # determine the number of images for each set
            train_size = int(len(imagesWithFigures) * train)
            val_size = int(len(imagesWithFigures) * val)

            images_train_folder = os.path.join(destinationFolder, "temp", "images", "train")
            images_test_folder  = os.path.join(destinationFolder, "temp", "images", "test")
            images_val_folder   = os.path.join(destinationFolder, "temp", "images", "val")
            labels_train_folder = os.path.join(destinationFolder, "temp", "labels", "train")
            labels_test_folder  = os.path.join(destinationFolder, "temp", "labels", "test")
            labels_val_folder   = os.path.join(destinationFolder, "temp", "labels", "val")


            # check existence of previous yaml and gather labels info if maintaining content
            labelsBefore = list()
            yamls = glob(destinationFolder + '/*.yaml')
            if yamls and maintainContent:
                with open(yamls[0], "r") as file:
                    oldYaml = yaml.safe_load(file)
                    for a in oldYaml["names"]:       
                        element = oldYaml["names"][a] if isinstance(oldYaml["names"], dict) else a
                        labelsBefore.append(element)

            for label in labels:
                if label not in labelsBefore:
                    labelsBefore.append(label)

            labels = labelsBefore

            if yamls:
                os.remove(yamls[0])
                    
            # make yaml:
            yamlDict = dict()

            yamlDict["path"] = destinationFolder
            yamlDict["train"] = "images/train"
            yamlDict["test"] = "images/test"
            yamlDict["val"] = "images/val"
            yamlDict["names"] = labels

            # create destination folders if they don't exist
            for folder_path in [images_train_folder, images_test_folder, images_val_folder,
                                 labels_train_folder, labels_test_folder, labels_val_folder]:
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

            # write new information in yaml file
            with open(destinationFolder + "/data.yaml", "w") as file:
                yaml.dump(yamlDict, file)


            for i, index in enumerate(imagesWithFigures):
                imageAddress = images[index].path
                imageName    = images[index].name

                if os.path.exists(destinationFolder):
                    for root, dirs, files in os.walk(destinationFolder, topdown=True):
                        for name in files:
                            if name == imageName:

                                indexAux = 1

                                newName = name.split(".")[0] + "_" + str(indexAux) + "." + name.split(".")[1]
                                while os.path.exists(imageAddress.replace(imageName, "") + newName):
                                    index += 1
                                    newName = name.split(".")[0] + "_" + str(indexAux) + "." + name.split(".")[1]
                                
                                os.rename(imageAddress, imageAddress.replace(imageName, "") + newName)
                                imageAddress = imageAddress.replace(imageName, "") + newName
                                imageName = newName

                dest_folder_images = ""
                dest_folder_labels = ""

                if i < train_size:
                    dest_folder_images = images_train_folder
                    dest_folder_labels = labels_train_folder
                elif i < train_size + val_size:
                    dest_folder_images = images_val_folder
                    dest_folder_labels = labels_val_folder
                else:
                    dest_folder_images = images_test_folder
                    dest_folder_labels = labels_test_folder

                shutil.copy(imageAddress, os.path.join(dest_folder_images, imageName))

                # go though each image and extract bounding boxes

                figuresText = list()
                for figure in images[index].figures:
                    indexLabel = labels.index(figure.label)
                    width   = figure.brc[0] - figure.tlc[0]
                    height  = figure.brc[1] - figure.tlc[1] 
                    centerX = figure.tlc[0] + (width/2)
                    centerY = figure.tlc[1] + (height/2)

                    # normalize the bounding boxes properties
                    width   /= images[index].width
                    height  /= images[index].height
                    centerX /= images[index].width
                    centerY /= images[index].height

                    figuresText.append(str(indexLabel) + " " + 
                                       str(centerX) + " " + 
                                       str(centerY) + " " + 
                                       str(width) + " " +
                                       str(height) + "\n")
                
                with open(dest_folder_labels + "/" + imageName.split('.')[0] + ".txt", 'w') as f:
                    f.writelines(figuresText)

            # clear unwanted content from destinationFolder
            if not maintainContent:
                inside = glob(destinationFolder + "/*")
                for clean_up in inside:
                    if not clean_up.endswith('/temp') and not clean_up.endswith('.yaml'):    
                        shutil.rmtree(clean_up, ignore_errors=True)
            shutil.copytree(destinationFolder + "/temp", destinationFolder, dirs_exist_ok=True)
            shutil.rmtree(destinationFolder + "/temp", ignore_errors=True)
            
            pop.close()
            window.UnHide()
            sg.Popup("Done!", title=":)")
                
            continue

if __name__ == "__main__":
    main()