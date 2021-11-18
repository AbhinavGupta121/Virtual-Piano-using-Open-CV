# Import essential libraries
import requests
import cv2
import numpy as np
import imutils
import mediapipe as mp
import threading
import pygame.mixer
from pygame import *
import time
import os
import sys
import multiprocessing

#Global variables definition
landmarks= {'thumb': [1,2,3,4], 'index': [5,6,7,8], 'middle': [9,10,11,12], 'ring': [13,14,15,16], 'little': [17,18,19,20]} #Position landmarks index corresponding to each finger. Refer to mediapipe github repo for more details

tip_landmarks = [4,8,12,16,20] #index of tip position of all fingers
dist_threshold_param= {'thumb': 8.6, 'index': 6, 'middle': 6, 'ring': 6, 'little': 5} #customized dist threshold values for calibration of finger_detect_and_compute module
left_detect=np.zeros(5);right_detect=np.zeros(5) #arrays representing detected finger presses for each hand
left_coordinates=np.zeros((5,2));right_coordinates=np.zeros((5,2)) #arrays representing pixel coordinates of each detected finger press (tip landmark)
bboxes_white=np.zeros((52,4)) #initializing bboxes for all white keys in standard 88key piano
bboxes_black=np.zeros((36,4)) #initializing bboxes for all black keys in standard 88key piano
start_x=40; start_y=250; #starting pixel coordinates of piano
white_key_width=10; white_key_height=80; black_key_width=5; black_key_height=40 #params related to piano visualization
white_key_reference=[]#list containing reference key values for all white keys.
black_key_reference=[]#list containing reference key values for all black keys.
key_index_array=[]#stores indexes and colors for all detected key presses
play_music_status=1
visualizer_status=1

class handDetector():
    def __init__(self, mode=False, maxHands=4, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands #Max no of hands to be detected in one frame. 
        self.detectionCon = detectionCon #detection confidence
        self.trackCon = trackCon #tracking confidence--enables tracking rather than detection on every frame if tracking confidence is good (improves fps)
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands()
        self.mpDraw = mp.solutions.drawing_utils #drawing object used for drawing later on the image

    def findHands(self, img, draw=True):

        """ Function: Get results and Draw landmarks on the read image for all hands detected in the frame
            Arguments:  self, img: image to draw landmarks on, 
                        draw: if True, draws landmarks on the image frame
            returns: img: final image with the landmarks """
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS) 
        return img

    def findPosition(self, img, handNo=0, draw=True):

        """ Function: Store position of all landmarks corresponding to a hand in a list
            Arguments:  self, img: image to draw landmarks on.
                        draw: If True, draws landmarks on the image frame.
                        handNo: index of corresponding hand (left or right)
            returns: List: List of image coordinates and id's of position landmarks of a hand """
        List = []
        if (self.results.multi_hand_landmarks):
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                List.append([id, cx, cy])
                # if draw:
                #     cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)
        List=np.array(List)
        return List


    def handsCount(self):

        """ Function: calculates the total no of hands detected in an image frame
            Arguments: self
            returns: total no of hands detected in a frame """
        # Returns the no of hand detected in the image frame

        dim=np.shape(np.array(self.results.multi_hand_landmarks))
        if(dim):
            return dim[0]
        else:
            return 0


def check_threshold(p1,p2,p3,finger):

    """ Function: Checks whether a key press is detected for a finger based on a mathematical condition
            Arguments: p1,p2,p3: positions of landmarks of a finger
                       finger: string name of the finger pressed (not required)
            returns: boolean value of whether key press is detected or not """
    global dist_threshold_param
    p1=p1/10
    p2=p2/10
    p3=p3/10

    dist = np.linalg.norm(p1 - p2) +  np.linalg.norm(p3 - p2) + np.linalg.norm(p1 - p3) #Calculating sum of absolute distances b/w three landmark points of a finger. This is a noobie algo. Can be improved!
    return (dist<dist_threshold_param[finger]) #return True if this is smaller than a prespecified threshold during calibration

def finger_detect_and_compute(list):

    """ Function: Computes whether a key is actually pressed using fingers of a hand in an image frame. Also computes the coordinates of tip_landmarks corresponding to the pressed fingers
            Arguments: list: a list containing all position landmarks of a hand
            returns: detected_array: boolean array representing corresponding key presses
                     coordinates: pixel coordinates of the tip landmakrs of the pressed keys """
    
    detect_array=np.array([(int)(check_threshold(list[2][1:3],list[3][1:3],list[4][1:3],'thumb')),(int)(check_threshold(list[6][1:3],list[7][1:3],list[8][1:3],'index')),(int)(check_threshold(list[10][1:3],list[11][1:3],list[12][1:3],'middle')),(int)(check_threshold(list[14][1:3],list[15][1:3],list[16][1:3],'ring')),(int)(check_threshold(list[18][1:3],list[19][1:3],list[20][1:3],'little'))])
    coordinates=np.zeros((5,2))
    for i in range(5):
        if(detect_array[i]!=0):
            coordinates[i]=list[tip_landmarks][i,1:3]
    
    return detect_array,coordinates

def initialize_visualizer(img1):

    """ Function: Initialize all variables important to piano visualization on image
            Arguments: img1: Image to display piano image
            returns: img_background: updated background image to display piano image """
    global bboxes_white, bboxes_black, start_x, start_y, white_key_width, white_key_height, black_key_width, black_key_height
    curr_x=start_x; curr_y=start_y
    img_background=img1.copy()
    for i in range(52):#Initializing 52 white piano keys
        img_background = cv2.rectangle(img_background, (curr_x,curr_y), (curr_x+white_key_width,curr_y+white_key_height), [255,255,255], 2)
        bboxes_white[i]=[curr_x,curr_y,curr_x+white_key_width,curr_y+white_key_height]
        curr_x=curr_x + white_key_width

    #Overlaying the first odd black key
    curr_x= (int)(start_x + white_key_width-black_key_width/2.0)
    img_background = cv2.rectangle(img_background, (curr_x,curr_y), (curr_x+black_key_width,curr_y+black_key_height), [0,0,0], -1)
    bboxes_black[0]=[curr_x,curr_y,curr_x+black_key_width,curr_y+black_key_height]
    curr_x=curr_x + 2*white_key_width

    for i in range(7): #initializing the remaining black keys
        img_background = cv2.rectangle(img_background, (curr_x,curr_y), (curr_x+black_key_width,curr_y+black_key_height), [0,0,0], -1)
        bboxes_black[i*5+1]=[curr_x,curr_y,curr_x+black_key_width,curr_y+black_key_height]

        curr_x=curr_x + white_key_width

        img_background = cv2.rectangle(img_background, (curr_x,curr_y), (curr_x+black_key_width,curr_y+black_key_height), [0,0,0], -1)
        bboxes_black[i*5+2]=[curr_x,curr_y,curr_x+black_key_width,curr_y+black_key_height]

        curr_x=curr_x + 2*white_key_width

        img_background = cv2.rectangle(img_background, (curr_x,curr_y), (curr_x+black_key_width,curr_y+black_key_height), [0,0,0], -1)
        bboxes_black[i*5+3]=[curr_x,curr_y,curr_x+black_key_width,curr_y+black_key_height]

        curr_x=curr_x + white_key_width

        img_background = cv2.rectangle(img_background, (curr_x,curr_y), (curr_x+black_key_width,curr_y+black_key_height), [0,0,0], -1)
        bboxes_black[i*5+4]=[curr_x,curr_y,curr_x+black_key_width,curr_y+black_key_height]

        curr_x=curr_x + white_key_width

        img_background = cv2.rectangle(img_background, (curr_x,curr_y), (curr_x+black_key_width,curr_y+black_key_height), [0,0,0], -1)
        bboxes_black[i*5+5]=[curr_x,curr_y,curr_x+black_key_width,curr_y+black_key_height]

        curr_x=curr_x + 2*white_key_width

    print("White_bboxes=",bboxes_white)
    print("Black_bboxes=",bboxes_white)
    return img_background
   
    

def visualizer(img_background):

    """ Function: Visualize updated piano set on an image
            Arguments: img_background:updated image to display piano image
            returns: None """

    global key_index_array,bboxes_white,bboxes_black

    if(visualizer_status): 
        print("In thread1")
        try:
            if(len(key_index_array)!=0): #Makes the pressed piano keys in different color for better visualization
                for key_index,color in key_index_array:
                    if(color=='white'):
                        xmin,ymin,xmax,ymax = bboxes_white[key_index]
                        start=(int(xmin),int(ymin))
                        end=(int(xmax),int(ymax))
                        print("start and end=",(start,end))
                        img_background_new=cv2.rectangle(img_background,start,end,(255,182,193),-1)
                        print('Printing key pressed-----------------------------',(key_index,color))
                    if(color=='black'):
                        xmin,ymin,xmax,ymax = bboxes_black[key_index]
                        start=(int(xmin),int(ymin))
                        end=(int(xmax),int(ymax))
                        print("start and end=",(start,end))
                        img_background_new=cv2.rectangle(img_background,start,end,(144,238,144),-1)
                        print('Printing key pressed-----------------------------',(key_index,color))
            
            print("key_index_array=",key_index_array)
            key_index_array=[]
        except KeyboardInterrupt:
            print("Exiting visualizer thread")
            sys.exit()


def piano_key_initializer():

    """ Function: Initialize piano keys for music. Used global variables white_key_reference and black_key_reference
            Arguments: None
            returns: None """

    
    global white_key_reference, black_key_reference
    white_key_reference.append('a0')
    white_key_reference.append('b0')
    black_key_reference.append('a-0')

    for i in range(7):
        white_key_reference.append('c'+str(i+1))
        white_key_reference.append('d'+str(i+1))
        white_key_reference.append('e'+str(i+1))
        white_key_reference.append('f'+str(i+1))
        white_key_reference.append('g'+str(i+1))
        white_key_reference.append('a'+str(i+1))
        white_key_reference.append('b'+str(i+1))

        black_key_reference.append('c-'+str(i+1))
        black_key_reference.append('d-'+str(i+1))
        black_key_reference.append('f-'+str(i+1))
        black_key_reference.append('g-'+str(i+1))
        black_key_reference.append('a-'+str(i+1))
    white_key_reference.append('c8')

    print("Piano Keys Initialized Succesfully!")


def within_threshold(pos,item):

    """ Function: check if the tip of pressed is within the threshold of piano key boundaries
            Arguments: pos: x,y pixel coordinates of the tip of finger
                       item: boundaries of bbox of a particular key of a piano
            returns: boolean value"""

    if(pos[0]>item[0] and pos[0]<item[2] and pos[1]>item[1] and pos[1]<item[3]):
        return True
    else:
        return False
    


def find_note(pos):

    """ Function: Given  coordinates of a key pressed (finger tip), returns string name of ogg file to be played!
            Arguments: pos: x,y pixel coordinates of the tip of finger
            returns: note: ogg file address
                     index: index of the pressed key
                     color: color of the pressed key: 'black or 'white """
                     
    x,y=pos
    index=0
    global bboxes_white,bboxes_black,white_key_reference,black_key_reference

    for id, items in enumerate(bboxes_black):
        if(within_threshold(pos,items)):
            index=id
            note=black_key_reference[id]
            return note,index,'black'

    for id, items in enumerate(bboxes_white):
        if(within_threshold(pos,items)):
            index=id
            note=white_key_reference[id]
            return note,index,'white'
    
    return 'Wrong Press',100,'None'



def find_music_list(pos,num):

    """ Function: Prepares the music list of piano keys to be played given the positions of all pressed piano keys and the no of keys pressed
            Arguments: pos: positions of all finger tips corresponding to which a key press is detected
                       num: no of keys pressed at a time 
            returns: music_list: list of all piano music files to be played"""

    music_list=[]; global key_index_array
    for i in range(num):
        note,key_index,color=find_note(pos[i])
        if(note!='Wrong Press'):
            key_index_array.append([key_index,color])
            for fname in os.listdir('/home/abhinav/Piano_project/25405__tedagame__88-piano-keys-long-reverb/'):
                if note in fname:
                    note=fname
                    break
            music_list.append('/home/abhinav/Piano_project/25405__tedagame__88-piano-keys-long-reverb/'+ note)

    return music_list      

def build_music_list():

    """ Function: Builds the list of piano keys to play music
            Arguments: none
            returns: music_list: list of all piano music files to be played"""

    global left_detect,left_coordinates,right_detect,right_coordinates
    positions=[];music_list=[]
    if(play_music_status):
        try:
            for i in range(5):
                if(left_detect[i]!=0):
                    positions.append(left_coordinates[i])
                if(right_detect[i]!=0):
                    positions.append(right_coordinates[i])
            num=len(positions)
            print('num=',num)
            if(num!=0):
                music_list=find_music_list(positions,num)
                print("Printing Music list in play_music:",music_list)
            return music_list
        except KeyboardInterrupt:
            print("Exiting play music thread")
            sys.exit()

def play_music(q,status):

    """ Function: Plays piano music in a separate python process
            Arguments: q: queue to pass music_list data among different python processes
                       status: can be used to switch off this process (not required)
            returns: None"""

    print("Processing play_music process")
    while True:
        try:
            print("In the play_music function--Checking condition")
            mixer.init()
            pygame.mixer.set_num_channels(10)  # default is 8
            music_list=q.get()
            if(len(music_list)!=0):
                for id,items in enumerate(music_list):
                    pygame.mixer.Channel(id).play(pygame.mixer.Sound(music_list[id]))
                import time
                time.sleep(2)
        except KeyboardInterrupt:
            print("Play_music process stopped forcefully")
            sys.exit()


def reinitialize():

    """ Function: Reinitialize suitable global variables after every iteration
            Arguments: none
            returns: none"""

    global right_detect,right_coordinates,left_detect,left_coordinates,key_index_array

    left_detect=np.zeros(5);right_detect=np.zeros(5)
    left_coordinates=np.zeros((5,2));right_coordinates=np.zeros((5,2))
    key_index_array=[]

def processor(q,status):

    """ Function: Primary process to read image frames from server->detect finger landmarks->find finger tip positions and build music lists
            Arguments: none
            returns: music_list: list of all piano music files to be played"""

    # Declare useful variables
    pTime = 0; cTime = 0; right_hand=1; left_hand=0
    lmList=[]; rmList=[]
    detector = handDetector()
    global right_detect,right_coordinates,left_detect,left_coordinates,play_music_status,key_index_array
    music_list_curr=[]
    music_list_prev=[]

    url = "http://192.168.29.189:8080/shot.jpg"
    status.put(1)
 
    # While loop to continuously fetching data from the Url
    while True:
        try:
            print("Queue Size=",q.qsize())

            # Read image data from server and preprocess
            img_resp = requests.get(url)
            img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
            img = cv2.imdecode(img_arr, -1)
            img = imutils.resize(img, width=640, height=480)
            

            # Detect finger landmarks in left (or/and right hand)
            hands=1
            img = detector.findHands(img) #draw hand landmarks on image
            lmList = detector.findPosition(img,left_hand) #storing position of landmarks in an array
            hands=detector.handsCount() #find total no of hands in image frame
            print("No of hands are",hands)

            if(hands>1):
                rmList = detector.findPosition(img,right_hand)

            if len(lmList) != 0:
                left_detect,left_coordinates = finger_detect_and_compute(lmList) 
                print("Left Hand Detection Array=", left_detect)
                print("left coordinates are", left_coordinates)
                for i in range(5):
                    if(left_detect[i]!=0):
                        x,y=left_coordinates[i]
                        img=cv2.circle(img, (int(x),int(y)), 10, (10,50,50), 5)

            if len(rmList) != 0 and hands>1:
                right_detect,right_coordinates = finger_detect_and_compute(rmList)
                print("Right Hand Detection Array=", right_detect)
                print("Right coordinates are", right_coordinates)
                for i in range(5):
                    if(right_detect[i]!=0):
                        x,y=right_coordinates[i]
                        img=cv2.circle(img, (int(x),int(y)), 10, (50,50,100), 5)
                        
            music_list_curr=build_music_list() # Build music list

            if(len(music_list_curr)!=0) and music_list_curr!=music_list_prev:
                q.put(music_list_curr) #Pass curr_music_list to another python process running play_music() function
                music_list_prev=music_list_curr

            if(len(music_list_curr)==0 and music_list_curr!=music_list_prev and status.qsize()<=1): # Empty queue if curr_music_list is empty--stop music
                while not q.empty():
                    q.get()
            img_background = initialize_visualizer(img)
            visualizer(img_background) #Visualize virtual piano onscreen

            cTime = time.time()
            fps = 1 / (cTime - pTime)
            pTime = cTime
            lmList=[]
            rmList=[]
            reinitialize() # Reinitiaizing variables to initial values!
            cv2.putText(img_background, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                        (255, 0, 255), 3)
            cv2.imshow("Image", img_background)
            cv2.waitKey(100)
            time.sleep(0.1)
    
        except KeyboardInterrupt:
            print("Program Execution stopped forcefully! Killing all processes!")
            play_music_status=0
            visualizer_status=0
            sys.exit()
            


# Main function for initiating target processes

def main():
    
    piano_key_initializer() 
   
    q = multiprocessing.Queue()
    status= multiprocessing.Queue()
    # creating new processes
    p1 = multiprocessing.Process(target=processor, args=(q,status,))
    p2 = multiprocessing.Process(target=play_music, args=(q,status,))
  
    p1.start()
    p2.start()
    
    print("Exiting main")



if __name__ == "__main__":
    main()

