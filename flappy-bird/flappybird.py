
# coding: utf-8

# In[15]:

#! /usr/bin/env python3

"""Flappy Bird, implemented using Pygame."""
import pandas as pd
import numpy as np
import math
import os
import sys
from random import randint
from collections import deque
import random
import pygame
from pygame.locals import *


# In[16]:


FPS = 60# 设置帧率（屏幕每秒刷新的次数）
ANIMATION_SPEED = 0.18   # pixels per millisecond 0.18
WIN_WIDTH = 284 * 2     # BG image size: 284x512 px; tiled twice 窗口宽度
WIN_HEIGHT = 512    #窗口高度


# 定义常用颜色
WHITE       = (255, 255, 255)
GRAY        = (185, 185, 185)
BLACK       = (  0,   0,   0)
RED         = (155,   0,   0)
LIGHTRED    = (175,  20,  20)
GREEN       = (  0, 155,   0)
LIGHTGREEN  = ( 20, 175,  20)
BLUE        = (  0,   0, 155)
LIGHTBLUE   = ( 20,  20, 175)
YELLOW      = (155, 155,   0)
LIGHTYELLOW = (175, 175,  20)
class Bird(pygame.sprite.Sprite):
    """Represents the bird controlled by the player.

    The bird is the 'hero' of this game.  The player can make it climb
    (ascend quickly), otherwise it sinks (descends more slowly).  It must
    pass through the space in between pipes (for every pipe passed, one
    point is scored); if it crashes into a pipe, the game ends.

    Attributes:
    x: The bird's X coordinate.
    y: The bird's Y coordinate.
    msec_to_climb: The number of milliseconds left to climb, where a
        complete climb lasts Bird.CLIMB_DURATION milliseconds.

    Constants:
    WIDTH: The width, in pixels, of the bird's image.
    HEIGHT: The height, in pixels, of the bird's image.
    SINK_SPEED: With which speed, in pixels per millisecond, the bird
        descends in one second while not climbing.
    CLIMB_SPEED: With which speed, in pixels per millisecond, the bird
        ascends in one second while climbing, on average.  See also the
        Bird.update docstring.
    CLIMB_DURATION: The number of milliseconds it takes the bird to
        execute a complete climb.
    """
    WIDTH = HEIGHT = 32
    SINK_SPEED = 0.10 #小鸟下沉速度 0.18
    CLIMB_SPEED = 0.2  #小鸟攀升速度 0.3 
    CLIMB_DURATION = 333.3 #一个攀升周期（单位：毫秒） 原始：333.3
    
    def __init__(self, x, y, msec_to_climb, images):
        """Initialise a new Bird instance.

        Arguments:
        x: The bird's initial X coordinate.
        y: The bird's initial Y coordinate.
        msec_to_climb: The number of milliseconds left to climb, where a
            complete climb lasts Bird.CLIMB_DURATION milliseconds.  Use
            this if you want the bird to make a (small?) climb at the
            very beginning of the game.
        images: A tuple containing the images used by this bird.  It
            must contain the following images, in the following order:
                0. image of the bird with its wing pointing upward
                1. image of the bird with its wing pointing downward
        """
        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.msec_to_climb = msec_to_climb
        self._img_wingup, self._img_wingdown = images
        self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)

    def update(self, delta_frames=1):
        """Update the bird's position.

        This function uses the cosine function to achieve a smooth climb:
        In the first and last few frames, the bird climbs very little, in the
        middle of the climb, it climbs a lot.
        One complete climb lasts CLIMB_DURATION milliseconds, during which
        the bird ascends with an average speed of CLIMB_SPEED px/ms.
        This Bird's msec_to_climb attribute will automatically be
        decreased accordingly if it was > 0 when this method was called.

        Arguments:
        delta_frames: The number of frames elapsed since this method was
            last called.
        """
        if self.msec_to_climb > 0:
            frac_climb_done = 1 - self.msec_to_climb/Bird.CLIMB_DURATION
            self.y -= (Bird.CLIMB_SPEED * frames_to_msec(delta_frames) *
                       (1 - math.cos(frac_climb_done * math.pi)))
            self.msec_to_climb -= frames_to_msec(delta_frames)
        else:
            self.y += Bird.SINK_SPEED * frames_to_msec(delta_frames)

    @property
    def image(self):
        """Get a Surface containing this bird's image.

        This will decide whether to return an image where the bird's
        visible wing is pointing upward or where it is pointing downward
        based on pygame.time.get_ticks().  This will animate the flapping
        bird, even though pygame doesn't support animated GIFs.
        """
        if pygame.time.get_ticks() % 500 >= 250:
            return self._img_wingup
        else:
            return self._img_wingdown

    @property
    def mask(self):
        """Get a bitmask for use in collision detection.

        The bitmask excludes all pixels in self.image with a
        transparency greater than 127."""
        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown

    @property
    def rect(self):
        """Get the bird's position, width, and height, as a pygame.Rect."""
        return Rect(self.x, self.y, Bird.WIDTH, Bird.HEIGHT)


class PipePair(pygame.sprite.Sprite):
    """Represents an obstacle.

    A PipePair has a top and a bottom pipe, and only between them can
    the bird pass -- if it collides with either part, the game is over.

    Attributes:
    x: The PipePair's X position.  This is a float, to make movement
        smoother.  Note that there is no y attribute, as it will only
        ever be 0.
    image: A pygame.Surface which can be blitted to the display surface
        to display the PipePair.
    mask: A bitmask which excludes all pixels in self.image with a
        transparency greater than 127.  This can be used for collision
        detection.
    top_pieces: The number of pieces, including the end piece, in the
        top pipe.
    bottom_pieces: The number of pieces, including the end piece, in
        the bottom pipe.

    Constants:
    WIDTH: The width, in pixels, of a pipe piece.  Because a pipe is
        only one piece wide, this is also the width of a PipePair's
        image.
    PIECE_HEIGHT: The height, in pixels, of a pipe piece.
    ADD_INTERVAL: The interval, in milliseconds, in between adding new
        pipes.
    """
    #global ADD_INTERVAL,WIDTH,PIECE_HEIGHT
    WIDTH = 80
    PIECE_HEIGHT = 32
    ADD_INTERVAL = 3000 #管子障碍物之间的间隔（单位毫秒） 原始：3000 

    def __init__(self, pipe_end_img, pipe_body_img):
        """Initialises a new random PipePair.

        The new PipePair will automatically be assigned an x attribute of
        float(WIN_WIDTH - 1).

        Arguments:
        pipe_end_img: The image to use to represent a pipe's end piece.
        pipe_body_img: The image to use to represent one horizontal slice
            of a pipe's body.
        """
        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False

        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()   # speeds up blitting
        self.image.fill((0, 0, 0, 0))
        total_pipe_body_pieces = int(
            (WIN_HEIGHT -                  # fill window from top to bottom
             3 * Bird.HEIGHT -             # make room for bird to fit through
             3 * PipePair.PIECE_HEIGHT) /  # 2 end pieces + 1 body piece
            PipePair.PIECE_HEIGHT          # to get number of pipe pieces
        )
        self.bottom_pieces = randint(1, total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces

        # bottom pipe
        for i in range(1, self.bottom_pieces + 1):
            piece_pos = (0, WIN_HEIGHT - i*PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)

        # top pipe
        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))

        # compensate for added end pieces
        self.top_pieces += 1
        self.bottom_pieces += 1

        # for collision detection
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def top_height_px(self):
        """Get the top pipe's height, in pixels."""
        return self.top_pieces * PipePair.PIECE_HEIGHT

    @property
    def bottom_height_px(self):
        """Get the bottom pipe's height, in pixels."""
        return self.bottom_pieces * PipePair.PIECE_HEIGHT

    @property
    def visible(self):
        """Get whether this PipePair on screen, visible to the player."""
        return -PipePair.WIDTH < self.x < WIN_WIDTH

    @property
    def rect(self):
        """Get the Rect which contains this PipePair."""
        return Rect(self.x, 0, PipePair.WIDTH, PipePair.PIECE_HEIGHT)

    def update(self, delta_frames=1):
        """Update the PipePair's position.

        Arguments:
        delta_frames: The number of frames elapsed since this method was
            last called.
        """
        self.x -= ANIMATION_SPEED * frames_to_msec(delta_frames)

    def collides_with(self, bird):
        """Get whether the bird collides with a pipe in this PipePair.

        Arguments:
        bird: The Bird which should be tested for collision with this
            PipePair.
        """
        return pygame.sprite.collide_mask(self, bird)


def load_images():
    """Load all images required by the game and return a dict of them.

    The returned dict has the following keys:
    background: The game's background image.
    bird-wingup: An image of the bird with its wing pointing upward.
        Use this and bird-wingdown to create a flapping bird.
    bird-wingdown: An image of the bird with its wing pointing downward.
        Use this and bird-wingup to create a flapping bird.
    pipe-end: An image of a pipe's end piece (the slightly wider bit).
        Use this and pipe-body to make pipes.
    pipe-body: An image of a slice of a pipe's body.  Use this and
        pipe-body to make pipes.
    """

    def load_image(img_file_name):
        """Return the loaded pygame image with the specified file name.

        This function looks for images in the game's images folder
        (./images/).  All images are converted before being returned to
        speed up blitting.

        Arguments:
        img_file_name: The file name (including its extension, e.g.
            '.png') of the required image, without a file path.
        """
        file_name = os.path.join('.', 'images', img_file_name)
        img = pygame.image.load(file_name)
        img.convert()
        return img

    return {'background': load_image('background.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),
            # images for animating the flapping bird -- animated GIFs are
            # not supported in pygame
            'bird-wingup': load_image('bird_wing_up.png'),
            'bird-wingdown': load_image('bird_wing_down.png')}


def frames_to_msec(frames, fps=FPS):
    """Convert frames to milliseconds at the specified framerate.

    Arguments:
    frames: How many frames to convert to milliseconds.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):
    """Convert milliseconds to frames at the specified framerate.

    Arguments:
    milliseconds: How many milliseconds to convert to frames.
    fps: The framerate to use for conversion.  Default: FPS.
    """
    return fps * milliseconds / 1000.0


# In[17]:

#降低游戏难度
def makegameeasy():
#     SINK_SPEED = 0.10 #小鸟下沉速度 0.18
#     CLIMB_SPEED = 0.2  #小鸟攀升速度 0.3 
#     CLIMB_DURATION = 333.3 #一个攀升周期（单位：毫秒） 原始：333.3
#     ADD_INTERVAL = 3000 #管子障碍物之间的间隔（单位毫秒） 原始：3000 
#     ANIMATION_SPEED= 0.18  #小鸟飞行速度
    global ANIMATION_SPEED
    global SINK_SPEED
    global CLIMB_SPEED
    global CLIMB_DURATION
    global ADD_INTERVAL
    ANIMATION_SPEED -=0.02
    #ADD_INTERVAL +=1500


# In[18]:

#提高游戏难度
def makegamehard():
    global ANIMATION_SPEED
    global SINK_SPEED
    global CLIMB_SPEED
    global CLIMB_DURATION
    global ADD_INTERVAL
    ANIMATION_SPEED +=0.02
    #ADD_INTERVAL -=1500


# In[19]:

#退出游戏
def terminate():
    pygame.quit()
    sys.exit()


# In[20]:

#显示分数
def drawScore(score):
    scoreSurf=BASICFONT.render('Score: %s' %(score),True,WHITE)
    scoreRect=scoreSurf.get_rect()
    scoreRect.topleft=(WIN_WIDTH-120,10)
    display_surface.blit(scoreSurf,scoreRect)


# In[21]:

#检测按键事件
def drawPressKeyMsg():
    pressKeySurf=BASICFONT.render('Press Any Key To START',True, GREEN)
    pressKeyRect=pressKeySurf.get_rect()
    pressKeyRect.topleft=(WIN_WIDTH-200, WIN_HEIGHT-30)
    display_surface.blit(pressKeySurf,pressKeyRect)


# In[22]:

#检测按键事件
def checkForKeyPress():
    if len(pygame.event.get(QUIT))>0:
        terminate()
    keyUpEvents=pygame.event.get(KEYUP)
    if len(keyUpEvents)==0:
        return None
    if keyUpEvents[0].key==K_ESCAPE:
        terminate()
    return keyUpEvents[0].key


# In[23]:

#游戏开始界面，按键盘任意键开始
def showStartScreen():
    display_surface.fill(BLACK)
    titleFont=pygame.font.Font('resource/ARBERKLEY.ttf',100)
    titleSurf=titleFont.render('FlappyBird!',True,GREEN)
    titleRect=titleSurf.get_rect()
    titleRect.center=(WIN_WIDTH/2,WIN_HEIGHT/2 )
    display_surface.blit(titleSurf,titleRect)
    
    drawPressKeyMsg()
    
    pygame.display.update()
    
    while True:
        if checkForKeyPress():
            pygame.event.get()
            return


# In[24]:

#创建文本绘制对象
def makeTextObjs(text,font,color):
    surf=font.render(text,True,color)
    return surf,surf.get_rect()


# In[25]:

#显示开始、暂停、结束画面
def showTextScreen(text):
    #该函数用于在屏幕中央显示大文本，知道按下任意键
    #绘制文字阴影
    titleSurf,titleRect=makeTextObjs(text,BIGFONT,GRAY)
    titleRect.center=(int(WIN_WIDTH/2),int(WIN_HEIGHT/2))
    display_surface.blit(titleSurf,titleRect)
    
    #绘制文字
    titleSurf,titleRect=makeTextObjs(text,BIGFONT,WHITE)
    titleRect.center=(int(WIN_WIDTH/2)-3, int(WIN_HEIGHT/2)-3)
    display_surface.blit(titleSurf,titleRect)
    
#     #绘制额外的Press a key to play文字
#     pressKeySurf,pressKeyRect=makeTextObjs('Press a key to play.', BASICFONT,WHITE)
#     pressKeyRect.center=(int(WIN_WIDTH/2) , int(WIN_HEIGHT/2)+100)
#     display_surface.blit(pressKeySurf, pressKeyRect)
    
#     while checkForKeyPress()==None:
#         pygame.display.update()
#         clock.tick()
    drawPressKeyMsg()
    pygame.display.update()
    while True:
        if checkForKeyPress():
            pygame.event.get()
            return


# In[26]:

#显示游戏结束画面  To exit: use 'exit', 'quit', or Ctrl-D.
def showGameOverScreen():
    gameOverFont=pygame.font.Font('resource/ARBERKLEY.ttf',50)
    gameSurf=gameOverFont.render('Game',True,WHITE)
    overSurf=gameOverFont.render('Over',True,WHITE)
    gameRect=gameSurf.get_rect()
    overRect=overSurf.get_rect()
    gameRect.midtop=(WIN_WIDTH/2,WIN_HEIGHT/2-gameRect.height-10)
    overRect.midtop=(WIN_WIDTH/2,WIN_HEIGHT/2)
    
    display_surface.blit(gameSurf,gameRect)
    display_surface.blit(overSurf,overRect)
    drawPressKeyMsg()
    pygame.display.update()
    pygame.time.wait(500) #等待时间
    checkForKeyPress()
    
    while True:
        if checkForKeyPress():
            pygame.event.get()
            terminate()
            return


# In[27]:

def dataload(scores,hards,times,trialnums,failnums,successnums):
#     print( scores)
#     print( hards)
#     print( times)
#     print( trialnums)
#     print( failnums)
#     print( successnums)
    data={'分数（通过关卡数）':scores,
          '难度系数（难度由低到高）':hards,
          '通关时间（单位：秒）':times,
          '单个游戏次数':trialnums,
          '失败trial次数':failnums,
          '成功trial次数':successnums}
    frame=pd.DataFrame(data)
    frame.to_excel('被试数据.xlsx')
    print(frame)


# In[28]:

def rungame():

    # the bird stays in the same x position, so bird.x is a constant
    # center bird on screen
    score_font = pygame.font.SysFont(None, 32, bold=True)  # default font
    images = load_images()
    bird = Bird(50, int(WIN_HEIGHT/2 - Bird.HEIGHT/2), 2,
                (images['bird-wingup'], images['bird-wingdown']))

    pipes = deque()

    frame_clock = 0  # this counter is only incremented if the game isn't paused
    score = 0
    done = paused = passed = False #done 是完成了，passed是通过了
    index=0 #游戏已经进行的关卡数量
    
    #*******************************************
    N=2#15 #游戏总计关卡数量 即trial数量为N+1，但最后一关有时会出问题，所以不计入总数
    passscore=2#10 #每关成功所需通过障碍物的数量  19关一分钟
    
    trialnums=0 #每个被试做单个游戏的次数
    successnums=0 #成功trial数目
    failnums=0#失败trial数目，减一为正确数目
    trialnumss=[]
    successnumss=[]
    failnumss=[]
    hard=0 #初始任务难度
    times=[] #每个trial所需时间
    hards=[] #每个trial难度，初始难度为0
    scores=[] #每个trial分数
#     time=[153]
#     times=numpy.concatenate((times,time ))
    #*******************************************

    while index<N: #共计有N关
        print()
        #case 1：
        if score>=passscore and index<N: #通关
            print("case 1")
            #增加游戏难度
            makegamehard()
            #播放通关背景音乐
            pygame.mixer.music.load('resource/tetrisb.mid')
            pygame.mixer.music.play(-1, 0.0)
            #print("showTextScreen")
            #每关结束后显示等待界面
            showTextScreen('Pass!')
            #print("After showTextScreen")
            #难度加1，将难度计入数组
            ha=[hard]
            hard +=1
            hards = np.concatenate((hards,ha))
            done = paused = passed = False
            #统计时间和分数
            sc=[score]
            scores=np.concatenate((scores,sc))
            fr=[frame_clock]
            times=np.concatenate((times,fr))    
            score=0
            frame_clock=0
            pipes=deque()
            bird=Bird(50,int(WIN_HEIGHT/2- Bird.HEIGHT/2) ,2 , (images['bird-wingup'],images['bird-wingdown']))
            print("已通过第%i关" %index)
            index+=1
            print('Game over! Score: %i' % score)
            print('frame_colock : %i' %frame_clock)
            print('当前关卡为第 ：%i 关' %index)
            print('*******************************')
        while not done and index<N:
            #停止播放音乐
            pygame.mixer.music.stop()
            clock.tick(FPS)

            # Handle this 'manually'.  If we used pygame.time.set_timer(),
            # pipe addition would be messed up when paused.
            if not (paused or frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)):
                pp = PipePair(images['pipe-end'], images['pipe-body'])
                pipes.append(pp)

            for e in pygame.event.get():
                if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                    done = True
                    break
                elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                    paused = not paused
                elif e.type == MOUSEBUTTONUP or (e.type == KEYUP and
                        e.key in (K_UP, K_RETURN, K_SPACE)):
                    bird.msec_to_climb = Bird.CLIMB_DURATION

            if paused:
                continue  # don't draw anything
            #检查是否已经通关
            if score>=passscore:
                done=True
                #成功任务次数统计
                successnums +=1
                su=[successnums]
                successnumss=np.concatenate((successnumss,su))
            
            # check for collisions
            pipe_collision = any(p.collides_with(bird) for p in pipes)
            #发生撞击
            if pipe_collision or 0 >= bird.y or bird.y >= WIN_HEIGHT - Bird.HEIGHT:
                done = True

            for x in (0, WIN_WIDTH / 2):
                display_surface.blit(images['background'], (x, 0))

            while pipes and not pipes[0].visible:
                pipes.popleft()

            for p in pipes:
                p.update()
                display_surface.blit(p.image, p.rect)

            bird.update()
            display_surface.blit(bird.image, bird.rect)

            # update and display score
            for p in pipes:
                if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                    score += 1
                    p.score_counted = True

            score_surface = score_font.render(str(score), True, (255, 255, 255))
            score_x = WIN_WIDTH/2 - score_surface.get_width()/2
            display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))

            pygame.display.flip()
            #游戏帧数
            frame_clock += 1
        #case 3:
        if score<passscore and index<N:  #未通关
            print("case 3")
            #失败的游戏次数统计
            failnums +=1
            fa=[failnums]
            failnumss=np.concatenate((failnumss,fa))
            #降低游戏难度
            makegameeasy()
            done = paused = passed = False

            pipes=deque()
            bird=Bird(50,int(WIN_HEIGHT/2- Bird.HEIGHT/2) ,2 , (images['bird-wingup'],images['bird-wingdown']))
            #难度减1，将难度计入数组
            ha=[hard] #先计算当前的难度系数再更新新的难度
            hard -=1
            hards = np.concatenate((hards,ha))
            #统计时间和分数
            sc=[score]
            scores=np.concatenate((scores,sc))
            fr=[frame_clock]
            times=np.concatenate((times,fr))            
            score=0
            frame_clock=0
            print("showTextScreen")
            #每关结束后显示等待界面
            showTextScreen('Fail')
            print("After showTextScreen")
            print('Game over! Score: %i' % score)
            print('frame_colock : %i' %frame_clock)
            print('当前关卡为第 ：%i 关' %index)
            print('*******************************')            
        #总共做的游戏次数统计
        trialnums +=1
        tr=[trialnums]
        trialnumss=np.concatenate((trialnumss,tr))
    print("打印结果")
    print( scores)
    print( hards)
    print( times)
    print( trialnums)
    print( failnums)
    print( successnums)
    dataload(scores,hards,times/60,trialnumss-1,failnumss,successnumss) #帧数和时间要进行换算


# In[29]:

def main():
    """The application's entry point.

    If someone executes this module (instead of importing it, for
    example), this function is called.
    """
    global display_surface,clock,BASICFONT,BIGFONT
    
    # 初始化pygame
    pygame.init()
    # 设置屏幕宽高
    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    # 设置窗口的标题
    pygame.display.set_caption('Pygame Flappy Bird')
    # 获得pygame时钟
    clock = pygame.time.Clock()
    # 设置基本字体
    BASICFONT = pygame.font.Font('resource/ARBERKLEY.ttf', 18)
    # 设置大字体
    BIGFONT=pygame.font.Font('resource/ARBERKLEY.ttf',100)
#     # 二选一随机播放背景音乐
#     if random.randint(0, 1) == 0:
#         pygame.mixer.music.load('resource/tetrisb.mid')
#     else:
#         pygame.mixer.music.load('resource/tetrisc.mid')


    showStartScreen()
    
    rungame()
    
    showGameOverScreen()


# In[ ]:




# In[30]:

if __name__ == '__main__':
    # If this module had been imported, __name__ would be 'flappybird'.
    # It was executed (e.g. by double-clicking the file), so call main.
    main()

