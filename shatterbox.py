#!/usr/bin/env python
from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
import time
import sys
import math
import random



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
    def __init__(self, pos, width, height, image=None, parent=None, collisionInt=.5):
        # "pos" should be a QtCore.QPointF class

        self.parent = parent   # Look at self.setParentItem(<item>)
        super(Sprite, self).__init__(parent)

        self.connections = []

        if image:
            self.pixmap = QtGui.QPixmap(image)
            self.setPixmap( self.pixmap.scaled(width, height, QtCore.Qt.KeepAspectRatio) )
        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsSelectable)
        #self.setFlag(QtGui.QGraphicsPixmapItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)

        self.collisionInt = float(collisionInt)   # The interval at which to wait before calling "self.collision" again
        self.lastCollision = time.time() - self.collisionInt
        self.lastItemsList = []   # The last list of collision items this object collided with to help keep track of collisions
        # `self.collision` is called with ( self, [<itemsList>] )
        # "[<itemsList>]" is a list of all items this sprite is colliding with

        self.limitedBoundary = True   # If set to True, this sprite will bounce off the edges of the scene

        #self.setPos(self.xPos, self.yPos)
        self.setPos(pos[0], pos[1])

        self.lastUpdated = time.time()

        self.movDirection = [1.0, 1.0]
        #self.movSpeed = 0.0
        self.vel = [0., 0.]
        self.friction = 8.0   # The percentage of movement speed to subtract per second
        # If set to 0, the sprite will not slow down
        self.frictionCutOff = 0.01   # If the movement speed falls below this, it will be set to 0.0 just to help keep things simple
        self.elasticity = 1.0

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

    def getPos(self):
        return self.pos()

    def getCollisions(self):
        return self.collidingItems()

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

    def direct(self, direction, invert=False):   # Set "invert" to True if you want the sprite to move away from the target
        if invert:
            self.movDirection = [ (self.getCenter().x()-direction.x()), (self.getCenter().y()-direction.y()) ]
        else:
            self.movDirection = [ (direction.x()-self.getCenter().x()), (direction.y()-self.getCenter().y()) ]
        self.movDirection = condition(self.movDirection)

    def bump(self, direction, speed, invert=False):
        # Set "invert" to True if you want the sprite to move away from the target
        #self.direct(direction, invert=invert)
        self.vel = getDirection(self.getCenter().x(), self.getCenter().y(), direction.x(), direction.y())
        self.vel = [i*speed for i in self.vel]

    def collision(self, items):
        pass

    def connectTo(self, sprite):
        if not sprite in self.connections:
            self.connections.append(sprite)
        if not self in sprite.connections:
            sprite.connections.append(self)

    def bounceOff(self, sprite):
        # calculate normal and tangential unit vectors
        norm_vect = [(sprite.getCenter().x() - self.getCenter().x()),
                     (sprite.getCenter().y() - self.getCenter().y())]  # stil un-normalized!
        norm_length = math.sqrt((norm_vect[0]**2) + (norm_vect[1]**2))
        norm_vect = [norm_vect[0] / norm_length,
                     norm_vect[1] / norm_length]  # do normalization
        tang_vect = [-norm_vect[1], norm_vect[0]]  # rotate norm_vect by 90 degrees

        # normal and tangential velocities before collision
        vel1 = self.vel
        vel2 = sprite.vel
        vel1_norm = vel1[0] * norm_vect[0] + vel1[1] * norm_vect[1]
        vel1_tang = vel1[0] * tang_vect[0] + vel1[1] * tang_vect[1]
        vel2_norm = vel2[0] * norm_vect[0] + vel2[1] * norm_vect[1]
        vel2_tang = vel2[0] * tang_vect[0] + vel2[1] * tang_vect[1]

        # calculate velocities after collision
        new_vel1_norm = (vel1_norm * (self.getWidth() - sprite.getWidth())
                         + 2 * sprite.getWidth() * vel2_norm) / (self.getWidth() + sprite.getWidth())
        new_vel2_norm = (vel2_norm * (sprite.getWidth() - self.getWidth())
                         + 2 * self.getWidth() * vel1_norm) / (self.getWidth() + sprite.getWidth())
        # no need to calculate new_vel_tang, since it does not change

        # Now update the object's velocity
        self.vel = [norm_vect[0] * new_vel1_norm + tang_vect[0] * vel1_tang,
                       norm_vect[1] * new_vel1_norm + tang_vect[1] * vel1_tang]
        sprite.vel = [norm_vect[0] * new_vel2_norm + tang_vect[0] * vel2_tang,
                       norm_vect[1] * new_vel2_norm + tang_vect[1] * vel2_tang]

    def updateSprite(self, spriteList, speed=1.0):
        uDiff = time.time() - self.lastUpdated
        uDiff = uDiff * speed

        self.vel[0] -= perc2num(self.friction, self.vel[0]*speed)
        self.vel[1] -= perc2num(self.friction, self.vel[1]*speed)

        xPos = self.x()
        yPos = self.y()

        if self.limitedBoundary:
            if self.getRect().left() < 0:   # Too far left
                self.xPos = 0
                #if self.movDirection[0] < 0: self.movDirection[0] = -self.movDirection[0]
                if self.vel[0] < 0:
                    self.vel[0] = -self.vel[0]
            if self.getRect().right() > self.scene().sceneRect().width():   # Too far right
                self.xPos = self.scene().sceneRect().width() - self.getRect().width()
                #if self.movDirection[0] > 0: self.movDirection[0] = -self.movDirection[0]
                if self.vel[0] > 0:
                    self.vel[0] = -self.vel[0]
            if self.getRect().top() < 0:   # Too far up
                self.yPos = 0
                #if self.movDirection[1] < 0: self.movDirection[1] = -self.movDirection[1]
                if self.vel[1] < 0:
                    self.vel[1] = -self.vel[1]
            if self.getRect().bottom() > self.scene().sceneRect().height():   # Too far down
                self.yPos = self.scene().sceneRect().height() - self.getRect().height()
                #if self.movDirection[1] > 0: self.movDirection[1] = -self.movDirection[1]
                if self.vel[1] > 0:
                    self.vel[1] = -self.vel[1]

        for sprite in self.connections:
            distance = float(spriteDistance(self, sprite))
            direction = spriteDirection(self, sprite)
            sDir = spriteDirection(self, sprite)

            sprite.vel = self.vel


            if distance > self.getWidth()/3 + sprite.getWidth()/3:
                pass

        for sprite in [s for s in spriteList if s != self]:
            distance = spriteDistance(self, sprite)

            if distance < self.getWidth()/2 + sprite.getWidth()/2:
                self.bounceOff(sprite)

                jump_distance = self.getWidth()/2 + sprite.getWidth()/2
                jump_distance -= distance

                conditioned_velocity = condition(self.vel)

                jump_x = conditioned_velocity[0] * jump_distance
                jump_y = conditioned_velocity[1] * jump_distance

                xPos += jump_x/2
                yPos += jump_y/2
                sprite.setX(sprite.x() - jump_x/2)
                sprite.setX(sprite.x() - jump_y/2)

        #xPos = self.x() + (self.movSpeed * uDiff * self.movDirection[0])
        #yPos = self.y() + (self.movSpeed * uDiff * self.movDirection[1])

        xPos += self.vel[0] * uDiff
        yPos += self.vel[1] * uDiff

        self.setPos(xPos, yPos)

        hit = False
        preCol = self.getCollisions()
        collisions = []
        for i in preCol:
            if i.parent != self.parent:
                if self.parent and i.parent:
                    collisions.append(i)
        if self.lastItemsList == collisions and len(collisions) > 0 and time.time()-self.lastCollision >= self.collisionInt:
            hit = True
        elif collisions != self.lastItemsList and len(collisions) > 0:
            hit = True
        if hit:
            self.collision(collisions)
            self.lastCollision = time.time()
            self.lastItemsList = collisions

        self.update()

        self.lastUpdated = time.time()



class Environment():
    def __init__(self, scene):
        self.scene = scene
        self.sprites = []
        # A list containing all sprites in this environment

    def update(self, speed=1.0):
        for sprite in self.sprites:
            sprite.updateSprite(self.sprites, speed=speed)
        self.scene.update( self.scene.sceneRect() )

    def addSprite(self, xy, width, height, image=None, parent=None):
        newSprite = Sprite(xy, width, height, image=image, parent=parent)
        self.scene.addItem(newSprite)
        self.sprites.append(newSprite)
        return newSprite



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
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

        self.worldView.timerEvent = self.worldTimerEvent

        MainWindow.setCentralWidget(self.centralwidget)

    def setupEnvironment(self):
        self.environment = Environment(self.scene)

        self.worldView.timer = QtCore.QBasicTimer()
        self.worldView.updateSpeed = 50

        self.worldView.timerEvent = self.worldTimerEvent
        #self.worldView.mouseReleaseEvent = self.worldMouseReleaseEvent
        self.scene.mouseReleaseEvent = self.worldMouseReleaseEvent

        self.worldView.timer.start(self.worldView.updateSpeed, self.worldView)

    def worldMouseReleaseEvent(self, event):
        pos = event.lastScenePos()

        print("Position: {}, {}".format(pos.x(), pos.y()))

        self.environment.sprites[0].bump(pos, 500)

    def worldTimerEvent(self, event):
        self.environment.update(speed=1)




if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = QtWidgets.QMainWindow()
        myapp = Ui_MainWindow()

        myapp.setupUi(window)
        myapp.setupEnvironment()

        sprite1 = myapp.environment.addSprite([300,300], 40, 40, image="dot.png")
        sprite2 = myapp.environment.addSprite([400,400], 40, 40, image="dot.png")
        sprite3 = myapp.environment.addSprite([480,480], 20, 20, image="dot.png")
        #sprite4 = myapp.environment.addSprite([400,460], 20, 20, image="dot.png")

        for i in range(42):
            size = random.randrange(10, 50)
            pos = [random.randrange(50, 1000), random.randrange(50, 1000)]
            myapp.environment.addSprite(pos, size, size, image="dot.png")

        #sprite1.connectTo(sprite2)
        #sprite1.connectTo(sprite3)
        #sprite1.connectTo(sprite4)

        window.show()
        sys.exit(app.exec_())
