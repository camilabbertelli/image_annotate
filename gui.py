
import PySimpleGUI as sg

titleFont    = ('Ubuntu', 13)
subtitleFont = ('Ubuntu', 12)
bodyFont     = ('Ubuntu', 10)
sg.theme('LightGreen1')
sg.set_options(font=('Ubuntu', 10))

""" MAIN """

 # different program types
CLASSIFICATION = "Classification program"
DETECTION = "Detection program"

program_type_space = [[sg.Text("Program Type:", font=subtitleFont)],
                       [sg.Radio(CLASSIFICATION, "program", key=CLASSIFICATION, default=True, font=bodyFont)], 
                       [sg.Radio(DETECTION, "program", key=DETECTION, font=bodyFont)]]

browse_folder_space = [[sg.Text("Images folder:", font=subtitleFont)],
                [sg.Input(size=(60, 1), enable_events=True, key="folder", font=bodyFont),
                sg.FolderBrowse(font=bodyFont)],
                [sg.Text(key="error", font=bodyFont)]]

go_button_space = [[sg.Button("Go!", key="go", font=subtitleFont)]]

layout_main = [[sg.VPush()],
          [sg.Column(program_type_space)],
          [sg.Column([])],[sg.Column([])],
          [sg.Column(browse_folder_space)],
          [sg.Column([])],[sg.Column([])],[sg.Push(), sg.HSeparator(), sg.Push()],
          [sg.Push(), sg.Column(go_button_space), sg.Push()],
          [sg.VPush()]]

""" CLASSIFICATION """

defaultLabel = "default"
labels_space = [[sg.Text("Available classes:", font=subtitleFont)],
               [sg.Listbox(values=list(), size=(30, 20), enable_events=True, key="labels", font=bodyFont, horizontal_scroll=True, select_mode='multiple')],
               [sg.Input(size=(30, 5), key="labelToAdd", enable_events=True, font=bodyFont)], 
               [sg.Button("Add", key="addLabel", font=bodyFont), sg.Button("Remove", key="removeLabel", font=bodyFont), sg.Button("Edit", key="editLabel", font=bodyFont)],
               [sg.Text(key='error', font=bodyFont)],
               [sg.Text("Default class for unlabeled image: ", font=bodyFont)],
               [sg.Input(defaultLabel, size=(30, 5), key="defaultLabel", enable_events=True, font=bodyFont)]]

image_class_space = [[sg.Text("Images loaded: 0", key="numberImages", font=subtitleFont)],
              [sg.Image(key="currentImage", size=(700, 500))],
              [sg.Text("", key="imageName", font=bodyFont)], 
              [sg.Button(key="previous", image_filename="media/previous.png"), sg.Button(key="next", image_filename="media/next.png")]]

layout_classification = [[sg.Text("Quick annotation: "), sg.Button("OFF", key="quickAnnotation")],
          [sg.VPush(), sg.Push(), sg.Column(labels_space, element_justification='c'), sg.Push(), sg.VPush(), 
           sg.VSeparator(), 
           sg.VPush(), sg.Push(), sg.Column(image_class_space, element_justification='c'), sg.Push(), sg.VPush()],
          [sg.Column([])],[sg.Column([])],
          [sg.Button("Save-->", key="continue"), sg.Push(), sg.Button("All images", key="allImages")]]

def popup(message):
    layout = [[sg.Text(message)]]
    return sg.Window('Message', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    
""" SAVE DATASET """

browse_save_space = [[sg.Text("Destination folder: (please select an existing folder or create a new one by typing in the input)", font=subtitleFont)],
                [sg.Input(size=(60, 1), enable_events=True, key="folder", font=bodyFont),
                sg.FolderBrowse(font=bodyFont)],
                [sg.Checkbox("Maintain folder contents", key="maintainContent", enable_events=True, font=bodyFont)],
                [sg.Text(key="error_folder", font=bodyFont)]]

train_space = [[sg.Slider((0, 100), 60, orientation='horizontal', key="train")], [sg.Text("Train", font=subtitleFont)]]
test_space  = [[sg.Slider((0, 100), 20, orientation='horizontal', key="test")], [sg.Text("Test", font=subtitleFont)]]
val_space   = [[sg.Slider((0, 100), 20, orientation='horizontal', key="val")], [sg.Text("Validation", font=subtitleFont)]]

go_button_space.clear()
go_button_space = [[sg.Button("Go!", key="go", font=subtitleFont)]]

layout_save_dataset = [[sg.VPush()],
          [sg.Column(browse_save_space)],
          [sg.Column([])],[sg.Column([])],
          [sg.Push(), sg.Column(train_space, element_justification='c'), 
           sg.Push(), sg.Column(test_space, element_justification='c'), 
           sg.Push(), sg.Column(val_space, element_justification='c'), sg.Push()],
          [sg.Text(key="error_split", font=bodyFont)],
          [sg.Column([])],
          [sg.Push(), sg.HSeparator(), sg.Push()],
          [sg.Column([])],
          [sg.Push(), sg.Column(go_button_space), sg.Push()],
          [sg.VPush()]]

""" DETECTION """

labelsInList = list()
labels_space = [[sg.Text("Available classes:", font=subtitleFont)],
               [sg.Listbox(values=labelsInList, size=(30, 20), enable_events=True, key="labels", font=bodyFont, horizontal_scroll=True, select_mode='single')],
               [sg.Input(size=(23, 5), key="labelToAdd", enable_events=True, font=bodyFont), sg.ColorChooserButton(button_text="", target="colorPicked", key="colorChooser", button_color="#d9d9d9", bind_return_key=True)], 
               [sg.Button("Add", key="addLabel", font=bodyFont), sg.Button("Remove", key="removeLabel", font=bodyFont), sg.Button("Edit", key="editLabel", font=bodyFont)],
               [sg.Text(key='error', font=bodyFont)],
               [sg.Input("#d9d9d9", key="colorPicked", visible=False, enable_events=True)]]

image_class_space = [[sg.Push(), sg.Text("Images loaded: 0", key="numberImages", font=subtitleFont), sg.Push()],
              [sg.Graph(
               (1300, 700), 
               (0, 700),
               (1300, 0),
               key="graph",
               change_submits=True,  # mouse click events
               motion_events=True,
               drag_submits=True, 
               right_click_menu=["",[' ', 'Erase item']])],
              [sg.Checkbox("Move elements", key="moveFigures", enable_events=True, font=subtitleFont),
               sg.Checkbox("Show only figures from selected label", key="showFromSelected", enable_events=True, font=subtitleFont)],
              [sg.Push(), sg.Text("", key="imageName", font=bodyFont), sg.Push()], 
              [sg.Push(), sg.Button(key="previous", image_filename="media/previous.png"), sg.Button(key="next", image_filename="media/next.png"), sg.Push()]]

layout_detection = [[sg.Text("Quick annotation: "), sg.Button("OFF", key="quickAnnotation"), sg.Push(), sg.Button("Clear image", key="clear")],
          [sg.VPush(), sg.Push(), sg.Column(labels_space, element_justification='c'), sg.Push(), sg.VPush(), 
           sg.VSeparator(), 
           sg.VPush(), sg.Column(image_class_space), sg.VPush()],
          [sg.Column([])],[sg.Column([])],
          [sg.Button("Save-->", key="continue"), sg.Push(), sg.Button("All images", key="allImages")]]