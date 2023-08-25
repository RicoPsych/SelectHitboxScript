# importing the module
from collections import defaultdict
import itertools
import multiprocessing
import os
import cv2
import json
import numpy as np



def LoadConfig():
    global SOURCE_DIRECTORY, TARGET_DIRECTORY, HITBOX_FILE_NAME
    config_dict = json.load(open("config.json"))
    SOURCE_DIRECTORY = config_dict["source"]
    TARGET_DIRECTORY = config_dict["target"]
    HITBOX_FILE_NAME = config_dict["hitboxFileName"] + ".json"

def RecursiveDirectoryPngSearch(dir,list):
    currentDirectory = os.listdir(dir)
    pngList =  [child for child in currentDirectory if (".png" in child )]
    pngList = [dir+"/" + x for x in pngList]
    list = list + pngList #Add new JsonFiles

    currentDirectory =  [child for child in currentDirectory if ("." not in child )] #Get Folders from 
    for childDirectory in currentDirectory:
        list = RecursiveDirectoryPngSearch(dir+"/"+childDirectory,list)
    return list

#FilePaths
def GetActionPartDirectoryPath(fullPath):
    return fullPath.replace("/textures/"+fullPath.split("/")[-1], "")



def DirectoriesTree(allImageList):
    mainDirectories = defaultdict(list)
#   dict {
#        "actionPartPath": [actionPartFrames]
#        }
    for path in allImageList:
        actionPartDirectoryPath = GetActionPartDirectoryPath(path)
        mainDirectories[actionPartDirectoryPath].append(path)
    return mainDirectories

##LOAD

def LoadImage(path):
    img = cv2.imread(path,cv2.IMREAD_UNCHANGED)
    bgr = img[:,:,:3]
    alpha = img[:,:,3]
    baseImage = bgr.copy()
    baseImage[alpha==0] = (255)

    return baseImage # RETURN BASE_IMG 




#SAVE RECTANGLES TO JSON
def ConvertRectangleToJsonRectangle(rectangle):
    return {
        "X":rectangle[0],
        "Y":rectangle[1],
        "Width":rectangle[2],
        "Height":rectangle[3]

        # "X":rectangle[0][0],
        # "Y":rectangle[0][1],
        # "Width":rectangle[1][0] - rectangle[0][0], #x2 - x1
        # "Height":rectangle[1][1] - rectangle[0][1]
    }

def SaveRectanglesToFile(path, frames):
    rectanglesJson = []
    last_full_frame = []

    for frame in frames:
        frameRectanglesJson = []
        #JESLI FRAME NIE MA PROSTOKATOW _> UZYJ PROSTOKATOW Z POPRZEDNIEGO FRAMEA
        if len(frame) == 0:
            frame = last_full_frame
        else:
            last_full_frame = frame

        for rectangle in frame:
            frameRectanglesJson.append(ConvertRectangleToJsonRectangle(rectangle))

        rectanglesJson.append(frameRectanglesJson)

    newDirectoryPath = path.replace(SOURCE_DIRECTORY,TARGET_DIRECTORY)+"/"
    if not os.path.exists(newDirectoryPath):
        os.makedirs(newDirectoryPath)

    with open(newDirectoryPath+HITBOX_FILE_NAME,'w+') as file:
        json.dump(rectanglesJson, file)


##PRINTING RECTANGLES ON IMAGES

def AddRectanglesToImage(image,rectangles):
    for rect in rectangles: #rectangles_in_frame:
        cv2.rectangle(image, (rect[0],rect[1]), ( rect[0]+rect[2],rect[1]+rect[3] ) , (0,0,255) ,1)     
    #cv2.putText(image,str(index),(0,10),cv2.FONT_HERSHEY_SIMPLEX,0.25,(255,0,0),1,cv2.LINE_AA)
    return image       

def PrintRectangles(image,rectangles):
    imageWithRectangles = AddRectanglesToImage(image.copy(),rectangles)
    cv2.imshow('image', imageWithRectangles)


###HITBOX RECTANGLE CREATION
def CheckIfRectangleInHitbox(img,width,height,x,y):
    count = 0
    threshold = 0.1
    for i in range(int(height)):
        for n in range(int(width)):
            pixel = img[int(y+i)][int(x+n)]
            if  pixel != 255:
                count+=1

    return count > width*height*threshold

# Multiprocessing??? Useless?
# def CheckRectangleRowInHitbox(rowIndex , height, width, horizontal_rect_count, img_gray):
#     hitbox_rectangles=[]
#     y = rowIndex*height
#     for n in range(horizontal_rect_count):
#         x = n * width
#         if CheckIfRectangleInHitbox(img_gray,width,height,x, y):
#             hitbox_rectangles.append((x,y,width,height))
#     return hitbox_rectangles

def CreateRectanglesFromFrame(image):

    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Convert to binary image by thresholding
    _, threshold = cv2.threshold(img_gray, 245, 255, cv2.THRESH_BINARY_INV)
    
    horizontal_rect_count = 40
    vertical_rect_count = 30
    
    height = len(img_gray)/vertical_rect_count
    width = len(img_gray[0])/horizontal_rect_count

    # #pool = multiprocessing.Pool()
    # pool = multiprocessing.Pool(processes=4)

    # args = [(i , height, width, horizontal_rect_count, img_gray) for i in range(vertical_rect_count)]
    # results = pool.starmap(CheckRectangleRowInHitbox,args)

    # hitbox_rectangles = list(itertools.chain.from_iterable(results))
    hitbox_rectangles=[]
    for i in range(vertical_rect_count):
        y = i*height
        for n in range(horizontal_rect_count):
            x = n * width
            if CheckIfRectangleInHitbox(img_gray,width,height,x, y):
                hitbox_rectangles.append((int(x),int(y),int(width),int(height)))
    #           cv2.rectangle(image, (int(x),int(y)),(int(x+width),int(y+height) ) , (0,0,255) ,1) 
    
    #UPDATE_PROGRESS()   

    return hitbox_rectangles 

#Multiprocessing
def CreateHitboxForImage(imagePath):
    image = LoadImage(imagePath)
    rectanglesList = CreateRectanglesFromFrame(image)
#    PRINT_PROGRESS()
    return rectanglesList

def CreateHitboxForActionPart(imagesPathList):
    pool = multiprocessing.Pool()
    pool = multiprocessing.Pool(processes=8)
    hitboxesList = pool.map(CreateHitboxForImage,imagesPathList)
    #SUM RECTANGLES HERE
    return [SumHitboxRectanglesHorizontal(rectangleList) for rectangleList in hitboxesList]
    #return hitboxesList

def CreateActionPartsDictionaryWithHitboxes(actionsPartsDictionary):         
    actionsPartsHitboxes = defaultdict(list)
#   dict {
#        "actionPartPath": [frames[rectangles]]
#        }
    for actionPart in actionsPartsDictionary:
        actionsPartsHitboxes[actionPart] = CreateHitboxForActionPart(actionsPartsDictionary[actionPart])
        UPDATE_PROGRESS()
        PRINT_PROGRESS()

    return actionsPartsHitboxes

#SUMMING 
def SumHitboxRectanglesHorizontal(hitboxRectangles):
    summedRectangles = []
    rectangleRows = defaultdict(list)

    for rectangle in hitboxRectangles:
        rectangleRows[rectangle[1]].append(rectangle)

    for row in rectangleRows:
        rowRect = (rectangleRows[row][0][0],
                rectangleRows[row][0][1], 
                rectangleRows[row][-1][0]-rectangleRows[row][0][0] + rectangleRows[row][-1][2],
                rectangleRows[row][0][3])

    ##TODO:possibility to add multiple row rectangles if there is a gap ???

        summedRectangles.append(rowRect)

    return summedRectangles

### PROGRESS PRINT

def UPDATE_PROGRESS():
    global PROGRESS
    PROGRESS+=1

def PRINT_PROGRESS():
    global PROGRESS, TARGET_VALUE
    os.system("cls")
    print(PROGRESS/TARGET_VALUE)

###              MAIN
def Main():
    global PROGRESS, TARGET_VALUE
    PROGRESS = 0

    LoadConfig()
    
    characters = os.listdir(SOURCE_DIRECTORY)
    print(characters)

    allImageList = []
    allImageList = RecursiveDirectoryPngSearch(SOURCE_DIRECTORY,allImageList)


    if len(allImageList) <= 0:
        exit()

    actionsPartsPathsDictionary = DirectoriesTree(allImageList)
    
    TARGET_VALUE = len(actionsPartsPathsDictionary)

    actionsPartsHitboxesDictionary = CreateActionPartsDictionaryWithHitboxes(actionsPartsPathsDictionary)


    for actionPart in actionsPartsHitboxesDictionary:
        SaveRectanglesToFile(actionPart,actionsPartsHitboxesDictionary[actionPart])

    # 2nd LOOP -> Review hitboxes
    actionIndex = 0
    frameIndex = 0
    

    actionParts = list(actionsPartsPathsDictionary.keys())


    currentImage = LoadImage(actionsPartsPathsDictionary[actionParts[actionIndex]][frameIndex])
    currentImageHitboxes = actionsPartsHitboxesDictionary[actionParts[actionIndex][frameIndex]]
    cv2.imshow('image', currentImage)

    key = 0
    # wait for esc key to be pressed to exit
    while key != 27 and cv2.getWindowProperty('image', 0) >= 0: #and i < len(img_list)

        currentImage = LoadImage(actionsPartsPathsDictionary[actionParts[actionIndex]][frameIndex])
        currentImageHitboxes = actionsPartsHitboxesDictionary[actionParts[actionIndex]][frameIndex]
        PrintRectangles(currentImage,currentImageHitboxes)

        key = cv2.waitKey(0) 
        #back frame
        if key == ord("a"):
            frameIndex-=1
        #next frame
        if key == ord("d"):
            frameIndex+=1
        frameIndex = frameIndex % len(actionsPartsPathsDictionary[actionParts[actionIndex]])

        #back frame
        if key == ord("q"):
            actionIndex-=1
            frameIndex = 0
        #next frame
        if key == ord("e"):
            actionIndex+=1
            frameIndex = 0

        actionIndex = actionIndex %len(actionsPartsPathsDictionary)

        #save
        # if key == ord("s"):
        #     SaveRectangles()
        #     print("save")

    # close the window
    cv2.destroyAllWindows()

if __name__ == "__main__":
    Main()