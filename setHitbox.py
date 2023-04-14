# importing the module
import cv2
import json
import numpy as np
from os import listdir

x1 = 0 ;y1 = 0 ;x2 = 0;y2 = 0 #new
#rectangles_in_frame = []

def SaveRectangles():
    rectangles_json = []
    last_full_frame = []

    for frame in frames:
        rectangle_json = []
        if len(frame) == 0:
            frame = last_full_frame
        else:
            last_full_frame = frame

        for rect in frame:
            _rect = {
                "X":rect[0][0],
                "Y":rect[0][1],
                "Width":rect[1][0] - rect[0][0], #x2 - x1
                "Height":rect[1][1] - rect[0][1]
            }
            rectangle_json.append(_rect)

        rectangles_json.append(rectangle_json)

    with open(target_file_name,'w') as file:
        json.dump(rectangles_json, file)

def RectanglesAndFrameNr():
    global index,frames,img_hit
    for rect in frames[index]: #rectangles_in_frame:
        cv2.rectangle(img_hit, (rect[0][0],rect[0][1]),(rect[1][0],rect[1][1] ) , (0,0,255) ,1)     
    cv2.putText(img_hit,str(index),(0,10),cv2.FONT_HERSHEY_SIMPLEX,0.25,(255,0,0),1,cv2.LINE_AA)       

def PrintRectangles():
    global index,img_hit
    img_hit = base_img.copy()
    RectanglesAndFrameNr()
    cv2.imshow('image', img_hit)

def PrintNewRectangle(x,y):
    global img_hit
    RectanglesAndFrameNr()
    cv2.rectangle(img_hit, (x1,y1),(x,y) , (255,0,0) ,1)
    cv2.imshow('image', img_hit)
    img_hit = base_img.copy()

mouse_press = False

def MouseEvents(event, x, y, flags, params):
    global x1,y1,x2,y2,index,mouse_press
    global frames
    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_press = True
        print(x, ' ', y)
        x1 = x
        y1 = y
        #cv2.imshow('image', img_hit)
    if event == cv2.EVENT_MOUSEMOVE and mouse_press == True:
        PrintNewRectangle(x,y)
    elif event==cv2.EVENT_LBUTTONUP:
        mouse_press = False
        print(x, ' ', y)
        if x > x1:
            x2 = x
        else: #x1 > x
            x2 = x1
            x1 = x
        if y > y1:
            y2 = y
        else: #y1 > y
            y2 = y1
            y1 = y
        frames[index].append(((x1,y1),(x2,y2)))
        PrintRectangles() 
    elif event==cv2.EVENT_RBUTTONUP: 
        if len(frames[index]) > 0:
            print("delete rectangle")
            frames[index].pop()
            PrintRectangles() 

def LoadImage(directory,filename):
    global img_hit,base_img
    img = cv2.imread(directory+"\\"+filename,cv2.IMREAD_UNCHANGED)
    bgr = img[:,:,:3]
    alpha = img[:,:,3]
    base_img = bgr.copy()
    base_img[alpha==0] = (255)
    img_hit = base_img.copy()

def LoadConfig():
    global directory,target_file_name,load_file_name
    config_dict = json.load(open("config.json"))
    directory = config_dict["frames_dir"]
    target_file_name = config_dict["target"]
    load_file_name = config_dict["load"]



#                       MAIN
LoadConfig()

# reading the images from directory
#directory = input()
print(listdir(directory))
img_list = [f for f in listdir(directory) if ".png" in f]
if len(img_list) <= 0:
    exit()
frames = [[] for i in range(len(img_list))]

#get first image
LoadImage(directory,img_list[0])
cv2.imshow('image', img_hit)
cv2.setMouseCallback('image', MouseEvents)

#Load from file
try:
    rectangles_dict= json.load(open(load_file_name))
    index = 0
    for frame in rectangles_dict:
        
        rectangles_in_frame = []
        for rect in frame:
            rectangles_in_frame.append(((rect["X"],rect["Y"]),(rect["X"] + rect["Width"],rect["Y"]+rect["Height"])))
        frames[index] = rectangles_in_frame
        index+=1
except:
    print("File not found or wrong content")
# MAIN LOOP
index = 0
key = 0
# wait for esc key to be pressed to exit
while key != 27 and cv2.getWindowProperty('image', 0) >= 0: #and i < len(img_list)
    LoadImage(directory,img_list[index])
    PrintRectangles()

    key = cv2.waitKey(0) 
    #back
    if key == ord("a"):
        index-=1
        index = index%len(img_list)
    #save
    if key == ord("s"):
        SaveRectangles()
        print("save")
    #next
    if key == ord("d"):
        index+=1
        index = index %len(img_list)
    #Delete all rectangles in frame
    if key == ord("q"):
        for i in range(len(frames[index])):
            frames[index].pop()
    #Delete all rectangles and go to next frame
    if key == ord("e"):
        for i in range(len(frames[index])):
            frames[index].pop()
        index+=1
        index = index %len(img_list)
# close the window
cv2.destroyAllWindows()