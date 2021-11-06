import pygame as pg
import numpy as np
from numba import njit

def main():
    pg.init()
    screen = pg.display.set_mode((800,600))
    running = True
    clock = pg.time.Clock()
    pg.mouse.set_visible(False)

    hres = 200 #horizontal resolution
    halfvres = 200 #vertical resolution/2

    mod = hres/60 #scaling factor (60° fov)

    size = 25
    posx, posy, rot, maph, mapc, exitx, exity = gen_map(size)
    
    frame = np.random.uniform(0,1, (hres, halfvres*2, 3))
    sky = pg.image.load('skybox2.jpg')
    sky = pg.surfarray.array3d(pg.transform.scale(sky, (360, halfvres*2)))/255
    floor = pg.surfarray.array3d(pg.image.load('floor.jpg'))/255
    wall = pg.surfarray.array3d(pg.image.load('wall.jpg'))/255
    
    while running:
        if int(posx) == exitx and int(posy) == exity:
            print("you got out of the maze!")
            running = False
        for event in pg.event.get():
            if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                running = False

        frame = new_frame(posx, posy, rot, frame, sky, floor, hres, halfvres, mod, maph, size,
                          wall, mapc, exitx, exity)

        surf = pg.surfarray.make_surface(frame*255)
        surf = pg.transform.scale(surf, (800, 600))
        fps = int(clock.get_fps())
        pg.display.set_caption("Pycasting maze - FPS: " + str(fps))

        screen.blit(surf, (0,0))
        pg.display.update()

        posx, posy, rot = movement(pg.key.get_pressed(), posx, posy, rot, maph, clock.tick()/500)
        pg.mouse.set_pos(400,300)

def movement(pressed_keys, posx, posy, rot, maph, et):
    x, y, rot0, diag = posx, posy, rot, 0
    if pg.mouse.get_focused():
        p_mouse = pg.mouse.get_pos()
        rot = rot + np.clip((p_mouse[0]-400)/200, -0.2, .2)

    if pressed_keys[pg.K_UP] or pressed_keys[ord('w')]:
        x, y, diag = x + et*np.cos(rot), y + et*np.sin(rot), 1

    elif pressed_keys[pg.K_DOWN] or pressed_keys[ord('s')]:
        x, y, diag = x - et*np.cos(rot), y - et*np.sin(rot), 1
        
    if pressed_keys[pg.K_LEFT] or pressed_keys[ord('a')]:
        et = et/(diag+1)
        x, y = x + et*np.sin(rot), y - et*np.cos(rot)
        
    elif pressed_keys[pg.K_RIGHT] or pressed_keys[ord('d')]:
        et = et/(diag+1)
        x, y = x - et*np.sin(rot), y + et*np.cos(rot)


    if not(maph[int(x-0.2)][int(y)] or maph[int(x+0.2)][int(y)] or
           maph[int(x)][int(y-0.2)] or maph[int(x)][int(y+0.2)]):
        posx, posy = x, y
        
    elif not(maph[int(posx-0.2)][int(y)] or maph[int(posx+0.2)][int(y)] or
             maph[int(posx)][int(y-0.2)] or maph[int(posx)][int(y+0.2)]):
        posy = y
        
    elif not(maph[int(x-0.2)][int(posy)] or maph[int(x+0.2)][int(posy)] or
             maph[int(x)][int(posy-0.2)] or maph[int(x)][int(posy+0.2)]):
        posx = x
        
    return posx, posy, rot

def gen_map(size):
    
    mapc = np.random.uniform(0,1, (size,size,3)) 
    maph = np.random.choice([0, 0, 0, 0, 1, 1], (size,size))
    maph[0,:], maph[size-1,:], maph[:,0], maph[:,size-1] = (1,1,1,1)

    posx, posy, rot = 1.5, np.random.randint(1, size -1)+.5, np.pi/4
    x, y = int(posx), int(posy)
    maph[x][y] = 0
    count = 0
    while True:
        testx, testy = (x, y)
        if np.random.uniform() > 0.5:
            testx = testx + np.random.choice([-1, 1])
        else:
            testy = testy + np.random.choice([-1, 1])
        if testx > 0 and testx < size -1 and testy > 0 and testy < size -1:
            if maph[testx][testy] == 0 or count > 5:
                count = 0
                x, y = (testx, testy)
                maph[x][y] = 0
                if x == size-2:
                    exitx, exity = (x, y)
                    break
            else:
                count = count+1
    return posx, posy, rot, maph, mapc, exitx, exity

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, hres, halfvres, mod, maph, size, wall, mapc, exitx, exity):
    for i in range(hres):
        rot_i = rot + np.deg2rad(i/mod - 30)
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(np.deg2rad(i/mod - 30))
        frame[i][:] = sky[int(np.rad2deg(rot_i)%359)][:]

        x, y = posx, posy
        while maph[int(x)%(size-1)][int(y)%(size-1)] == 0:
            x, y = x +0.01*cos, y +0.01*sin

        n = abs((x - posx)/cos)    
        h = int(halfvres/(n*cos2 + 0.001))

        xx = int(x*3%1*99)        
        if x%1 < 0.02 or x%1 > 0.98:
            xx = int(y*3%1*99)
        yy = np.linspace(0, 3, h*2)*99%99

        shade = 0.3 + 0.7*(h/halfvres)
        if shade > 1:
            shade = 1
            
        ash = 0 
        if maph[int(x-0.33)%(size-1)][int(y-0.33)%(size-1)]:
            ash = 1
            
        if maph[int(x-0.01)%(size-1)][int(y-0.01)%(size-1)]:
            shade, ash = shade*0.5, 0
            
        c = shade*mapc[int(x)%(size-1)][int(y)%(size-1)]
        for k in range(h*2):
            if halfvres - h +k >= 0 and halfvres - h +k < 2*halfvres:
                if ash and 1-k/(2*h) < 1-xx/99:
                    c, ash = 0.5*c, 0
                frame[i][halfvres - h +k] = c*wall[xx][int(yy[k])]
                if halfvres+3*h-k < halfvres*2:
                    frame[i][halfvres+3*h-k] = c*wall[xx][int(yy[k])]
                
        for j in range(halfvres -h):
            n = (halfvres/(halfvres-j))/cos2
            x, y = posx + cos*n, posy + sin*n
            xx, yy = int(x*2%1*99), int(y*2%1*99)

            shade = 0.2 + 0.8*(1-j/halfvres)
            if maph[int(x-0.33)%(size-1)][int(y-0.33)%(size-1)]:
                shade = shade*0.5
            elif ((maph[int(x-0.33)%(size-1)][int(y)%(size-1)] and y%1>x%1)  or
                  (maph[int(x)%(size-1)][int(y-0.33)%(size-1)] and x%1>y%1)):
                shade = shade*0.5

            frame[i][halfvres*2-j-1] = shade*(floor[xx][yy]+frame[i][halfvres*2-j-1])/2
            if int(x) == exitx and int(y) == exity and (x%1-0.5)**2 + (y%1-0.5)**2 < 0.2:
                ee = j/(10*halfvres)
                frame[i][j:2*halfvres-j] = (ee*np.ones(3)+frame[i][j:2*halfvres-j])/(1+ee)

    return frame



if __name__ == '__main__':
    main()
    pg.quit()
