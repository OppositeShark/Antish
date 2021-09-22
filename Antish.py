# -*- coding: utf-8 -*-
"""
Created on Tue Sep 21 12:26:58 2021

@author: degog
"""
#%% Importing
import pygame
#importing stuff
from PIL import Image, ImageDraw
import random
import math
import threading

#%%Setup

#Window Size
width=300
height=width

#Seed
seed=None

wallWidth=2

#Angles and Sight
randomWalk=math.radians(3)
angs=(45,)
seeAngs={math.radians(i*s):1 for i in angs for s in (-1,1)}
seeAngs[0]=1
seeDist=2
maxturn=math.radians(50)
#Speed
maxSpeed=1
acceleration=0.1
#Weights and Colors
wallweight=-1000
distWeight=lambda d:0.9**d
#Number of Ants

numants=100
numType = 10

startX=width/2
startY=height/2
#Threading
numThreads=4
#Lasting Pheromones
fadeRate=0
#%%Starting
global BP
global BPheromones

def ResetImgs():
    #Pheromones
    #Trail away from the nest
    global FieldImg
    FieldImg=Image.new("RGBA",(width,height),(0,0,255,0))
    global Field
    Field=FieldImg.load()
    global FieldDraw
    FieldDraw = ImageDraw.Draw(FieldImg)
                
ResetImgs()

#Frames
frameNum=0
def resetFrames():
    global frameNum
    frameNum=0

#%%Colors
BLUE=(0,0,255)
RED=(255,0,0)
GREEN=(0,255,0)
YELLOW=(255,255,0)
WHITE=(255,255,255)
PINK=(255,0,255)
ORANGE=(255,100,0)
PURPLE=(100,0,255)
BLACK=(0,0,0)
CLEAR=(0,0,0,0)
#Specific Colors
ANTCOLOR=BLACK+(255,)
TONEST=BLUE
AWAYNEST=RED
WALL=BLACK+(255,)
FOOD=GREEN+(255,)
NEST=YELLOW+(150,)

#%%Ants
#Ant List
ants=[]
def OutOfBounds(x,y):
    return x>=width or x<0 or y>=height or y<0

#Ant Class
updateList=[]
def updatePixel(x,y):
    rect=pygame.Rect(x,y,1,1)
    updateList.append(rect)

def avgAng(ang1,ang2,ranges,weight=0.5):
    if abs(ang1-ang2)>ranges/2:
        if ang1>ang2:
            ang1+=ranges
        else:
            ang2+=ranges
    return lerp(ang1,ang2,weight)%ranges
    
def lerp(x,y,t):
    return (y-x)*t+x

def lerpColors(color1,color2,t):
    return tuple([lerp(color1[i],color2[i],t) for i in range(len(color1))])

def ColorsAreClose(color1,color2,threshold):
    r,g,b = [color1[i]+color2[i] for i in range(3)]
    return math.sqrt(sum([i**2 for i in (r,g,b)]))<threshold

class antish():
    def __init__(self,x,y,ang,color,impact,rules,intensity):
        self.x=x
        self.y=y
        if ang==None:
            ang = random.uniform(0, 2*math.pi)
        self.ang=ang
        self.speed=maxSpeed
        self.placePheromone=True
        self.color=color
        self.pheromoneImpact = impact
        self.rules = rules
        self.intensity=intensity
    
    toShade = 255/math.pi/2
    def dropPheromone(self):
        #Sets image pixel to red or blue
        if self.x>width or self.x<0 or self.y>height or self.y<0:
            return
        PixVal = Field[self.x,self.y]
        newColor = lerpColors(PixVal[:3],self.color,self.pheromoneImpact)
        Field[self.x,self.y]=tuple([round(i) for i in newColor])+(round(PixVal[3]+self.intensity),)
        
    def senses(self):
        #Creating Angle Choices
        choice={}
        for i in seeAngs.keys():
            choice[i]=0
        
        #Sight
        #Seeing each angle
        for ang,weight in seeAngs.items():
            direction=self.ang+ang
            cosDirection=math.cos(direction)
            sinDirection=math.sin(direction)
            for i in range(1,seeDist+1):
                #(x,y)
                x=round(i*cosDirection+self.x)
                y=round(i*sinDirection+self.y)
                
                #If the detection is out of bounds
                if OutOfBounds(x,y): 
                    break
                #Distance Weight
                iWeight=distWeight(i)
                PixVal = Field[x,y]
                #Check if it's blank
                if PixVal==CLEAR:
                    pass
                #Checking if theres a wall
                elif PixVal==WALL:
                    choice[ang]+=iWeight*wallweight
                    break
                for val in self.rules.keys():
                    #rules[0] is the threshold and rules[1] is the function
                    if ColorsAreClose(PixVal[:3],val,self.rules[val][0]):
                        choice[ang]+=self.rules[val][1](PixVal[3])
                
            #Angle Weight
            if abs(choice[ang])>=1:
                choice[ang]*=weight
            else:
                choice[ang]/=weight
        
        #Shift and Expand distances between Values
        minWeight = min(choice.values())
        if minWeight>0:
            minWeight=-minWeight
        for i in choice.keys():
            choice[i]+=minWeight
        
        #Weights of each choice
        totalWeight=sum(choice.values())
        if totalWeight==0:
            return seeAngs
        return choice
    
    def move(self):
        #Move Forward
        self.x+=self.speed*math.cos(self.ang)
        self.y+=self.speed*math.sin(self.ang)
        
        goStraight=False
        
        #Collision Detection
        if 0<self.x<width and 0<self.y<height:
            #"Kill" if they hit a wall
            if Field[self.x,self.y]==WALL:
                self.restart()
        
        #Sensing & Turning
        sight=self.senses()
        if not goStraight:
            #Random Walk
            self.ang+=random.gauss(0,randomWalk)
            #Sensing
            ang = random.choices(list(sight.keys()),weights = list(sight.values()))[0]
            if ang>maxturn:
                ang=maxturn
            elif ang<-maxturn:
                ang=-maxturn
            self.ang+=ang
                    
        #Accelerate
        if self.speed<maxSpeed:
            self.speed+=acceleration
        
        #Simplifying Angle
        self.ang=self.ang%(2*math.pi)
            
    def run(self):
        if OutOfBounds(self.x,self.y):
            self.restart()
            return
        updatePixel(self.x,self.y)
        self.move()
        if self.placePheromone:
            self.dropPheromone()
        updatePixel(self.x,self.y)
        
    def restart(self):
        self.food=False
        self.x=startX
        self.y=startY
        self.ang=random.uniform(0,2*math.pi)
    
#%%Creating Ants
ants=[]
def makeAntType(num, color, impact, rules, intensity):
    for i in range(num):
        ants.append(antish(startX,startY,None, color, impact, rules, intensity))
        
#%%Map Making
#Draw Walls
def drawWalls():
    #4 Walls
    FieldDraw.rectangle([0,0,width,wallWidth/2],fill=(0,0,0,255))
    FieldDraw.rectangle([0,0,wallWidth/2,height],fill=(0,0,0,255))
    FieldDraw.rectangle([width-(wallWidth/2),0,width,height],fill=(0,0,0,255))
    FieldDraw.rectangle([0,height-(wallWidth/2),width,height],fill=(0,0,0,255))

def drawMaze():
    random.seed(seed)
    #Drawing
    ResetImgs()
    drawWalls()
    
#%%Main Function
#Fading Pheromones
def fade(PixelAccess):
    for x in range(width):
        for y in range(height):
            color=PixelAccess[x,y]
            if color[3]==0:
                continue
            PixelAccess[x,y]=color[:3]+(color[3]-1,)
            updatePixel(x,y)
            
def saveImgs():
    FieldImg.save("Antish.png","PNG")

def runSimulation():
    '''
    Runs the simulation
    '''
    running=True
    colors=[]
    for i in range(numType):
        colors.append(tuple([random.randint(1, 255) for i in range(3)]))
    for i in range(numType):
        numTypeAnts = round(numants/numType)
        colorThreshold = random.randint(20,50)
        colorWeight = random.uniform(-1,1)
        rules = {c:[colorThreshold,lambda a:a*colorWeight] for c in colors}
        makeAntType(numTypeAnts, colors[i], random.uniform(0.1,1), rules, random.uniform(50,250))
    
    #Starting Pygame
    pygame.init()
    screen=pygame.display.set_mode((width,height))
    pygame.display.set_caption("Antish Simulation")
    
    #Initial Map
    screen.fill((255,255,255,255))
    FieldImg.save("Field.png","PNG")
    pygField=pygame.image.load("Field.png")
    for i in (pygField,):
        screen.blit(i, (0,0))
    pygame.display.update()
    
    def runAnts(ants):
        for i in ants:
            i.run()
    
    def threadAnts(func):
        threads=[]
        divisions=int(numants/numThreads)
        for i in range(numThreads):
            if i==numThreads-1:
                thread1=threading.Thread(target=func,args=(ants[i*divisions:],))
            else:
                thread1=threading.Thread(target=func,args=(ants[i*divisions:(i+1)*divisions],))
            threads.append(thread1)
            
        for i in threads:
            i.start()
        for i in threads:
            i.join()
            
    #Running
    while running:
        #Events
        for event in pygame.event.get():
            #Quitting
            if event.type==pygame.QUIT:
                running=False
            #Key Down
            elif event.type==2:
                #Down Button
                if event.key==274:
                    saveImgs()
                
        #Background
        screen.fill((255,255,255,255))
    
        #Calculations
        #Ant Movement
        threadAnts(runAnts)
        
        #Pheromone Reduction
        global frameNum
        if fadeRate!=0 and frameNum%fadeRate==0:
            fade(Field)
    
        #Drawing Pheromones, Food, and Walls
        pygField=pygame.image.fromstring(FieldImg.tobytes(), FieldImg.size, FieldImg.mode)
        screen.blit(pygField,(0,0))

        #Update Screen
        global updateList
        pygame.display.update(updateList)
        updateList=[]
        frameNum+=1
    pygame.quit()
    saveImgs()

def run():
    '''
    Sets up the simulation and runs it
    '''
    random.seed(seed)
    drawMaze()
    runSimulation()

if __name__=="__main__":
    run()