#!/usr/bin/env python
from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
import time
import sys
import math
import random
import numpy as np
import pymunk
from pymunk import Vec2d



try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


def num2perc(num, maxNum):
    return ((float(num) / float(maxNum)) * 100.0)

def perc2num(perc, maxNum):
    return ((float(perc) / 100.0) * float(maxNum))

def reverseAngle(angle):
    # Reverses an angle (degrees)
    newAngle = angle + 180
    if newAngle > 360:
        newAngle -= 360
    return newAngle

def getPointAvg(lst):
    # Gathers the center of every point in `lst` and returns the average
    # Used to get the exact center of a an object with many sprites in it
    nList = np.array([[i.x(), i.y()] for i in lst])
    nList = sum(nList) / len(nList)
    return QtCore.QPointF(nList[0], nList[1])

def posList(lst):
    lst2 = []
    for i in lst:
        if (i < 0):
            lst2.append(-i)
        else:
            lst2.append(i)
    return lst2

def condition(listVar, multiplier=1):
    try:
        lst2 = []

        for i in listVar:
            i = float(i)
            isneg = False
            if (i < 0):
                isneg = True; i = -i
            i = (i / sum(posList(listVar))*multiplier)
            if (isneg): i = -i
            lst2.append(i)

        return lst2
    except ZeroDivisionError:
        return [0,0]

def getDirection(x1, y1, x2, y2, invert=False):
    if invert:
        direction = [ (x1-x2), (y1-y2) ]
    else:
        direction = [ (x2-x1), (y2-y1) ]
    direction = condition(direction)
    return direction

def spriteDirection(sprite1, sprite2, invert=False):
    direction = getDirection(
        sprite1.getCenter().x(),
        sprite1.getCenter().y(),
        sprite2.getCenter().x(),
        sprite2.getCenter().y(),
        invert=invert
    )
    return direction

def randomDirection(multiplier=1):
    return condition([random.random()-random.random(), random.random()-random.random()], multiplier=multiplier)

def calculateDistance(x1,y1,x2,y2):
    dist = math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )
    return dist

def spriteDistance(sprite1, sprite2):
    x1 = sprite1.getCenter().x()
    y1 = sprite1.getCenter().y()
    x2 = sprite2.getCenter().x()
    y2 = sprite2.getCenter().y()
    return calculateDistance(x1, y1, x2, y2)



class Sprite(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, pos, width, height, environment,
                 mass=10, friction=.3, elasticity=.5, image=None, parent=None, collisionInt=.5):
        # "pos" should be a QtCore.QPointF class

        self.parent = parent   # Look at self.setParentItem(<item>)
        super(Sprite, self).__init__(parent)

        self.connections = {}
        # Structure: {<sprite>: <angle>}
        # Angle is in degrees

        self.environment = environment

        if image:
            self.pixmap = QtGui.QPixmap(image)
            self.setPixmap( self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio) )

        self.setTransformOriginPoint(width/2, height/2)

        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsSelectable)
        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)

        self.collisionInt = float(collisionInt)   # The interval at which to wait before calling "self.collision" again
        self.collisions = {}
        # Structure: {<item>: <time.time()>}

        self.limitedBoundary = True   # If set to True, this sprite will bounce off the edges of the scene

        # Pymunk
        #--

        self.radius = width/2

        inertia = pymunk.moment_for_circle(mass, 0, self.radius, (0,0))

        self.body = pymunk.Body(mass, inertia)
        self.body.position = pos

        self.shape = pymunk.Circle(self.body, self.radius, Vec2d(0,0))
        self.shape.friction = friction
        self.shape.elasticity = elasticity
        self.shape.sprite = self

        self.connections = {}
        # Structure: {<Sprite>: <pymunk.PinJoint>}

        #--

        #self.setPos(self.xPos, self.yPos)
        self.setPos(pos[0], pos[1])

        self.lastUpdated = time.time()

        self.elasticity = 1.

        self.mouseHoverFunc = None   # Executes with (self, event)
        self.mouseReleaseFunc = None   # Executes with (self, event)
        self.mousePressFunc = None   # Executes with (self, event)

    def mousePressEvent(self, event):
        if self.mousePressFunc != None:
            self.mousePressFunc(self, event)
    def mouseReleaseEvent(self, event):
        if self.mouseReleaseFunc != None:
            self.mouseReleaseFunc(self, event)
    def hoverEnterEvent(self, event):
        if self.mouseHoverFunc != None:
            self.mouseHoverFunc(self, event)

    def scale(self, width, height):
        tempPixmap = self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio)
        self.setPixmap( tempPixmap )

    def getCenter(self):
        childrenList = self.childItems()
        if not childrenList:
            return self.sceneBoundingRect().center()
        aList = [i.sceneBoundingRect().center() for i in childrenList]
        return getPointAvg(aList)
    def getRect(self):
        return self.sceneBoundingRect()

    def getWidth(self):
        return self.getRect().width()
    def getHeight(self):
        return self.getRect().height()

    def bump(self, direction, speed, invert=False):
        # Set "invert" to True if you want the sprite to move away from the target
        newVel = getDirection(self.body.position[0], self.body.position[1], direction[0], direction[1])
        newVel = [i*speed for i in newVel]
        self.body.velocity = Vec2d(newVel)

    def collision(self, item):
        pass

    def connectTo(self, sprite):
        # angle is in degrees
        direction = getDirection(self.getCenter().x(), self.getCenter().y(), sprite.getCenter().x(), sprite.getCenter().y())

        point1 = (direction[0]*self.radius, direction[1]*self.radius)
        point2 = (-direction[0]*self.radius, -direction[1]*self.radius)
        c = pymunk.PinJoint(self.body, sprite.body, point1, point2)
        self.body.space.add(c)
        self.connections[sprite] = c
        sprite.connections[self] = c

    def updateSprite(self, spriteList, speed):
        uDiff = time.time() - self.lastUpdated
        uDiff = uDiff * speed

        self.setPos(self.body.position[0]-self.radius, self.body.position[1]-self.radius)

        frictionCut = self.environment.friction * uDiff
        newVel = list(self.body.velocity)
        newVel = [i-(i*frictionCut) for i in newVel]

        self.body.velocity = Vec2d(newVel)

        self.body.angular_velocity -= self.body.angular_velocity * frictionCut

        angle = math.degrees(self.body.angle)

        self.setRotation(angle)

        self.update()
        self.lastUpdated = time.time()



class Environment():
    def __init__(self, worldView, scene, width, height, friction=20., gravity=0):
        self.worldView = worldView
        self.scene = scene
        self.friction = friction   # The percentage of movement speed to subtract per second
        # If set to 0, the sprite will not slow down
        self.sprites = []
        # A list containing all sprites in this environment
        self.space = pymunk.Space()
        self.space.gravity = 0, 0

        self.worldSpeed = .02
        self.updateSpeed = 50

        ch = self.space.add_collision_handler(0, 0)
        ch.post_solve = self.collision

        static_body = self.space.static_body
        static_lines = [pymunk.Segment(static_body, (0, 0), (0, height), 0.0),
                        pymunk.Segment(static_body, (0, height), (width, height), 0.0),
                        pymunk.Segment(static_body, (width, height), (width, 0), 0.0),
                        pymunk.Segment(static_body, (width, 0), (0, 0), 0.0)]
        for line in static_lines:
            line.elasticity = 0.95
            line.friction = 0.9
        self.space.add(static_lines)

        # Setup timer
        #--
        self.worldView.timer = QtCore.QBasicTimer()

        self.worldView.timerEvent = self.update
        #self.mouseReleaseEvent = self.worldMouseReleaseEvent
        self.scene.mouseReleaseEvent = self.worldMouseReleaseEvent

        self.worldView.timer.start(self.updateSpeed, self.worldView)
        #--

        self.scene.keyPressEvent = self.keyPressEvent

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_A:
            print(1)

    def collision(self, arbiter, space, data):
        shape1, shape2 = arbiter._get_shapes()
        if not isinstance(shape1, pymunk.Segment) and not isinstance(shape2, pymunk.Segment):
            sprite1 = shape1.sprite
            sprite2 = shape2.sprite

            sprite1.collision(sprite2)
            sprite2.collision(sprite1)

    def worldMouseReleaseEvent(self, event):
        pos = event.lastScenePos()

        print("Position: {}, {}".format(pos.x(), pos.y()))

        self.sprites[0].bump([pos.x(), pos.y()], 600)

    def update(self, event):
        self.space.step(self.worldSpeed)
        for sprite in self.sprites:
            sprite.updateSprite(self.sprites, self.worldSpeed)
        self.scene.update( self.scene.sceneRect() )

    def addSprite(self, xy, width, height, mass=10, friction=.3, elasticity=.5, image=None, parent=None):
        newSprite = Sprite(xy, width, height, self, mass=mass, friction=friction, elasticity=elasticity, image=image, parent=parent)
        self.scene.addItem(newSprite)
        self.sprites.append(newSprite)
        self.space.add(newSprite.body, newSprite.shape)
        return newSprite



def setupEnvironment(worldView, scene, friction=20., gravity=0):
    # worldView should be a `QGraphicsView` item
    # scene should be a `QGraphicsScene` item
    sceneRect = scene.sceneRect()
    environment = Environment(worldView, scene, sceneRect.width(), sceneRect.height(), friction=friction, gravity=gravity)
    return environment



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        self.width = 1050
        self.height = 1200
        MainWindow.resize(1100, 650)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))

        self.worldView = QtWidgets.QGraphicsView(self.centralwidget)

        self.worldView.setGeometry(QtCore.QRect(15, 20, 1070, 600))
        self.worldView.setObjectName(_fromUtf8("worldView"))

        self.timeline = QtCore.QTimeLine(1000)
        self.timeline.setFrameRange(0, 100)

        self.scene = QtWidgets.QGraphicsScene(self.worldView)

        self.scene.setSceneRect(0, 0, 1050, 1200)
        self.worldView.setScene(self.scene)

        self.worldView.setBackgroundBrush( QtGui.QBrush( QtGui.QColor(180,180,255) ) )

        MainWindow.setCentralWidget(self.centralwidget)



if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)
        #myapp.setupEnvironment()
        env = setupEnvironment(myapp.worldView, myapp.scene)

        sprite1 = env.addSprite([300,300], 40, 40, image="dot.png")
        sprite2 = env.addSprite([320,320], 40, 40, image="dot.png")

        sprite1.ff = True
        sprite2.ff = False

        sprite1.connectTo(sprite2)

        #sprite3 = env.addSprite([480,480], 20, 20, image="dot.png")
        #sprite4 = env.addSprite([400,460], 20, 20, image="dot.png")

        for i in range(80):
            size = random.randrange(10, 50)
            pos = [random.randrange(50, 1000), random.randrange(50, 1000)]
            sprite = env.addSprite(pos, size, size, image="dot.png")
            sprite.ff = False

        window.show()
        sys.exit(app.exec_())
