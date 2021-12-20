import pygame as pg
import numpy as np
from numba import njit

def main():
    pg.init()
    pg.display.set_caption("Dead and - A Python game by FinFET, thanks for playing!")
    font = pg.font.SysFont("Courier New", 70)
    
    sounds = load_sounds()
    m_vol, sfx_vol = 0.3, 0.7
    set_volume(m_vol, sfx_vol, sounds)
    sounds['music'].play(-1)
    
    stepdelay = pg.time.get_ticks()/200
    stepdelay2 = stepdelay
    click, clickdelay = 0, stepdelay
    
    screen = pg.display.set_mode((800,600))
        
    running, pause, options, newgame = 1, 1, 0, 2
    clock = pg.time.Clock()
    pg.mouse.set_visible(False)

    hres, halfvres, mod, frame = adjust_resolution()
    fullscreen = 0
    level, player_health = 0, 0
    
    sky1 = pg.image.load('Assets/Textures/skybox2.jpg')
    sky = pg.surfarray.array3d(pg.transform.smoothscale(sky1, (720, halfvres*4)))/255
    floor = pg.surfarray.array3d(pg.image.load('Assets/Textures/floor.jpg'))/255
    wall = pg.surfarray.array3d(pg.image.load('Assets/Textures/wall.jpg'))/255
    bwall = pg.surfarray.array3d(pg.image.load('Assets/Textures/bwall.jpg'))/255
    door = pg.surfarray.array3d(pg.image.load('Assets/Textures/door2.jpg'))/255
    window = pg.surfarray.array3d(pg.image.load('Assets/Textures/window2.jpg'))/255
    menu = [pg.image.load('Assets/Textures/menu.png').convert_alpha()]
    menu.append(pg.image.load('Assets/Textures/options.png').convert_alpha())
    menu.append(pg.image.load('Assets/Textures/credits.png').convert_alpha())
    hearts = pg.image.load('Assets/Textures/hearts.png').convert_alpha()
    hearts2 = pg.Surface.subsurface(hearts,(0,0,player_health*20,20))
    exit1 = pg.image.load('Assets/Textures/exit.png').convert_alpha()
    exits = [pg.Surface.subsurface(exit1,(0,0,50,50)), pg.Surface.subsurface(exit1,(50,0,50,50))]
    splash = pg.image.load('Assets/Textures/splash.jpg').convert()
    sprites, spsize, sword, swordsp = get_sprites(hres)

    msg = "Press any key..."
    surf = splash
    splash_screen(msg, splash, clock, font, screen)
    
    while running:
        pg.display.update()
        ticks = pg.time.get_ticks()/200
        er = min(clock.tick()/500, 0.3)
        if not pause and (player_health <= 0 or (nenemies < size/2  and int(posx) == exitx and int(posy) == exity
                                                 and np.sum(enemies[:,9]) == 0)):
            if player_health <= 0:
                msg = "You died! Level: " + str(level)
                sounds['died'].play()
                newgame = 2
            else:
                level += 1
                msg = "Victory! Level: " + str(level)
                player_health = min(player_health+3, 10)
                sounds['won'].play()
                newgame = 1
                if level > 10:
                    msg = 'You finished the game!'
                    level = 0
                    sounds['died'].play()
            splash_screen(msg, surf, clock, font, screen)
            pause, clickdelay = 1, ticks

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if swordsp < 1 and not pause:
                    swordsp = 1
                if pause and ticks - clickdelay > 1:
                    click, clickdelay = 1, ticks
                    sounds['swoosh'].play()
                    
            if event.type == pg.KEYDOWN:
                if event.key == ord('p') or event.key == pg.K_ESCAPE:
                    if newgame == 2:
                        newgame = 1
                    else:
                        pause = not(pause)
                    options = 0
                    pg.mouse.set_pos(400,300)
                    if newgame == 0 and nenemies > size/2:
                        msg = "Kill the monsters!"
                if event.key == ord('f'): # toggle fullscreen
                    pg.display.toggle_fullscreen()
                    fullscreen =  not(fullscreen)

        if  pause:
            clock.tick(60)

            surf2, pause, options, running, newgame, adjust_res, m_vol, sfx_vol = pause_menu(
                surf.copy(), menu, pause, options, click, running, m_vol, sfx_vol, sounds, newgame, font, msg, level, ticks, hres)
            
            if adjust_res != 1:
                hres, halfvres, mod, frame = adjust_resolution(int(hres*adjust_res))
                sky = pg.surfarray.array3d(pg.transform.smoothscale(sky1, (720, halfvres*4)))/255
                adjust_res = 1             
                
            screen.blit(surf2, (0,0))
            click = 0
            
            if newgame == 1:
                newgame, pause = 0, not(pause)
                if player_health <= 0 or msg[0] != 'V':
                    level, player_health = 0, 10

                msg = 'Loading...'
                surf2 = surf.copy()
                surf2.blit(font.render(msg, 1, (255, 255, 255)), (30, 100))
                surf2.blit(font.render(msg, 1, (30, 255, 155)), (32, 102))
                screen.blit(surf2, (0,0))
                pg.display.update()
                msg = 'Kill the monsters!'
                
                size = 15+2*level
                nenemies = size+5*level #number of enemies
                posx, posy, rot, rotv, maph, mapc, exitx, exity, stepscount = gen_map(size)
                enemies = spawn_enemies(nenemies, maph, size, posx, posy)
                hearts2 = pg.Surface.subsurface(hearts,(0,0,player_health*20,20))
                exit2 = 1
                
                mape = np.zeros((size, size))
                enemies, player_health, mape = enemies_ai(posx, posy, enemies, maph, size, mape, 2,
                                                          ticks, player_health)
                enemies = sort_sprites(posx, posy, rot, enemies, maph, size, er/3)
                frame = new_frame(posx, posy, rot, frame, sky, floor, hres, halfvres, mod, maph, size,
                                  wall, mapc, exitx, exity, 0, rotv, door, window, bwall)
                sounds['won'].play()

        else:
            frame = new_frame(posx-0.2*np.cos(rot), posy-0.2*np.sin(rot), rot, frame, sky, floor, hres, halfvres,
                              mod, maph, size, wall, mapc, exitx, exity, nenemies, rotv, door, window, bwall)
            surf = pg.surfarray.make_surface(frame*(255-level*10))#(205 + 50*np.sin(ticks/50)))

            mape = np.zeros((size, size))
            health = player_health
            enemies, player_health, mape = enemies_ai(posx, posy, enemies, maph, size, mape, swordsp, ticks, player_health)
            enemies = sort_sprites(posx-0.2*np.cos(rot), posy-0.2*np.sin(rot), rot, enemies, maph, size, er/3)
            
            surf, en = draw_sprites(surf, sprites, enemies, spsize, hres, halfvres, ticks, sword, swordsp, rotv)

            surf = pg.transform.scale2x(surf)
            surf = pg.transform.smoothscale(surf, (800, 600))
            surf.blit(hearts2, (20,20))

            if nenemies <= int(size/2):
                if np.sum(enemies[:,9]) == 0:
                    exit2 = 0
                    msg = "Find the exit!"
                else:
                    exit2 = 1
                    msg = "Monsters nearby!"
            
            surf.blit(exits[exit2], (730,20))
            screen.blit(surf, (0,0))
            

            if health > player_health:
                hearts2 = pg.Surface.subsurface(hearts,(0,0,player_health*20,20))
                sounds['hurt'].play()

            if ticks - stepdelay > 2 and stepscount != posx + posy:
                sounds['step'].play()
                stepdelay = ticks
            stepscount = posx + posy
                
            if mape[int(posx)][int(posy)] > 0:
                delaycontrol = max(0.3, 2/np.random.uniform(0.99, mape[int(posx)][int(posy)]))
                if ticks - stepdelay2 > delaycontrol:
                    sounds['step2'].play()
                    stepdelay2 = ticks
            
            if int(swordsp) > 0:
                if swordsp == 1:
                    sounds['swoosh'].play()
                    en_o = en        
                    while enemies[en][3] > 1.25 and enemies[en][3] < 10:
                        enemies[en][8] = enemies[en][8] - np.random.uniform(1,4)
                        x = enemies[en][0] + 0.4*np.cos(rot)
                        y = enemies[en][1] + 0.4*np.sin(rot)
                        if maph[int(x)][int(y)] == 0:
                            enemies[en][0]= (x + enemies[en][0])/2 # push back
                            enemies[en][1]= (y + enemies[en][1])/2
                        if enemies[en][8] < 0:
                            sounds['deadmonster'].play()
                            enemies[en,:] = 0
                            nenemies = nenemies - 1
                            
                            if np.random.uniform(0,1) < 0.2:
                                player_health = min(player_health+0.5, 10)
                                hearts2 = pg.Surface.subsurface(hearts,(0,0,player_health*20,20))
                                sounds['healthup'].play()                           
                        en = en - 1
                    if en != en_o:
                        if enemies[en_o][4]:
                            sounds['hitmonster2'].play()
                        else:
                            sounds['hitmonster'].play() 
                swordsp = (swordsp + er*5)%4

            
            fps = int(clock.get_fps())
            pg.display.set_caption("Health: "+str(player_health)+" Enemies: " + str(nenemies) + " FPS: " + str(fps)+ ' ' + msg)
            posx, posy, rot, rotv = movement(pg.key.get_pressed(), posx, posy, rot, maph, er, rotv)
##            rot, rotv = rot + np.sin(ticks)/1000, rotv + np.cos(ticks)/1000
            pg.mouse.set_pos(400,300)
            
def movement(pressed_keys, posx, posy, rot, maph, et, rotv):
    x, y, rot0, diag = posx, posy, rot, 0
    if pg.mouse.get_focused():
        p_mouse = pg.mouse.get_pos()
        rot = rot + np.clip((p_mouse[0]-400)/200, -0.2, .2)
        rotv = rotv + np.clip((p_mouse[1]-300)/200, -0.2, .2)
        rotv = np.clip(rotv, -0.999, .999)

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

    posx, posy = check_walls(posx, posy, maph, x, y)

    return posx, posy, rot, rotv

def gen_map(size):
    
    mapc = np.random.uniform(0,1, (size,size,3)) 
    maph = np.random.choice([0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4], (size,size))
    maph[0,:] = np.random.choice([1, 2, 3, 4], size)
    maph[size-1,:] = np.random.choice([1, 2, 3, 4], size)
    maph[:,0] = np.random.choice([1, 2, 3, 4], size)
    maph[:,size-1] = np.random.choice([1, 2, 3, 4], size)
    posx, posy = np.random.randint(1, size -2)+0.5, np.random.randint(1, size -2)+0.5
    rot, rotv, stepscount = np.pi/4, 0, posx + posy
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
                dtx = np.sqrt((x-posx)**2 + (y-posy)**2)
                if (dtx > size*.6 and np.random.uniform() > .999) or np.random.uniform() > .99999:
                    exitx, exity = (x, y)
                    break
            else:
                count = count+1
    
    return posx, posy, rot, rotv, maph, mapc, exitx, exity, stepscount

@njit()
def new_frame(posx, posy, rot, frame, sky, floor, hres, halfvres, mod, maph, size, wall, mapc,
              exitx, exity, nenemies, rotv, door, window, bwall):
    offset = -int(halfvres*rotv)
    for i in range(hres):
        rot_i = rot + np.deg2rad(i/mod - 30)
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(np.deg2rad(i/mod - 30))
        frame[i][:] = sky[int(np.rad2deg(rot_i)*2%718)][halfvres-offset:3*halfvres-offset]

        n = 0
        n2 = 0
        x, y = posx +0.2*cos, posy +0.2*sin
        for j in range(2000):
            x, y = x +0.01*cos, y +0.01*sin
            if n == 0 and maph[int(x)%(size-1)][int(y)%(size-1)] != 0: # found lower wall
                n = np.sqrt((x-posx)**2+(y-posy)**2)
            if maph[int(x)%(size-1)][int(y)%(size-1)] == 2:# found upper wall
                n2 = np.sqrt((x-posx)**2+(y-posy)**2)
                h = halfvres/(n2*cos2 + 0.001)
                break
        cwall = wall
        if n2 > 0.5 and 3*h > int(halfvres/(n*cos2 + 0.000001)): #draw upper wall
            xx = int(x*3%1*99)
            xxx = x%1
            if x%1 < 0.02 or x%1 > 0.98:
                xx = int(y*3%1*99)
                xxx = y%1
            yy = np.linspace(0, 3, int(h*2))*99%99

            shade = 0.3 + 0.7*(h/halfvres)
            if shade > 1:
                shade = 1
                
            if maph[int(x-0.02)%(size-1)][int(y-0.02)%(size-1)] != 0:
                shade = shade*0.8
                
            c = shade*mapc[int(x)%(size-1)][int(y)%(size-1)]
            if n2 > 3.5:
                cwall = bwall
            for k in range(int(h)*2):
                c2 = c*cwall[xx][int(yy[k])]
                h1 = int(halfvres - int(h) +k +offset -2*h +3)
                h2 = int(halfvres+3*h-k+offset-1 +2*h - 6)
                if xxx > 1/3 and xxx < 2/3 and k > h*2/3 and k < h*4/3:
                    c2 = shade*window[xx][int(yy[k])]
                if h1 >= 0 and h1 < 2*halfvres:
                    frame[i][h1] = c2
                if h2 < halfvres*2:
                    frame[i][h2] = c2

        x, y = posx +n*cos, posy +n*sin    
        walltype = maph[int(x)%(size-1)][int(y)%(size-1)]
        cwall = wall
        if n > 3.5:
            cwall = bwall
        h = int(halfvres/(n*cos2 + 0.000001))

        xx = int(x*3%1*99)
        xxx = x%1
        if x%1 < 0.02 or x%1 > 0.98:
            xx = int(y*3%1*99)
            xxx = y%1
        yy = np.linspace(0, 3, int(h*2))*99%99

        shade = 0.4 + 0.6*(h/halfvres)
        if shade > 1:
            shade = 1
            
        ash = 0 
        if maph[int(x-0.33)%(size-1)][int(y-0.33)%(size-1)] != 0:
            ash = 1
            
        if maph[int(x-0.01)%(size-1)][int(y-0.01)%(size-1)] != 0:
            shade, ash = shade*0.7, 0
            
        c = mapc[int(x)%(size-1)][int(y)%(size-1)]
        cdoor = np.sqrt(np.ones(3) - c)
        c = shade*c
        start_range, stop_range = 0, int(2*h)
        if h > halfvres+abs(offset):
            start_range = int(h - halfvres - offset)
            stop_range = int(h + halfvres - offset)
        for k in range(start_range, stop_range):
            c2 = c*cwall[xx][int(yy[k])]
            h1 = int(halfvres - h +k +offset)
            h2 = int(halfvres+3*h-k+offset-3)
            if xxx > 1/3 and xxx < 2/3 and k > h*2/3:
                if walltype < 3:
                    c2 = shade*cdoor*door[xx][int(yy[k])]
                elif k < h*4/3 and walltype == 3:
                    c2 = shade*window[xx][int(yy[k])]
            if h1 >= 0 and h1 < 2*halfvres:
                if ash and 1-k/(2*h) < 1-xx/99:
                    c2, c, ash = 0.7*c2, 0.7*c, 0
                frame[i][h1] = c2
            if h2 < halfvres*2:
                frame[i][h2] = c2

                
        for j in range(int(halfvres -h -offset)): #floor
            n = (halfvres/(halfvres-j - offset ))/cos2
            x, y = posx + cos*n, posy + sin*n
            xx, yy = int(x*3%1*99), int(y*3%1*99)

            shade = min(0.2 + 0.8/n, 1)
            if maph[int(x-0.33)%(size-1)][int(y-0.33)%(size-1)] != 0:
                shade = shade*0.7
            elif ((maph[int(x-0.33)%(size-1)][int(y)%(size-1)] and y%1>x%1)  or
                  (maph[int(x)%(size-1)][int(y-0.33)%(size-1)] and x%1>y%1)):
                shade = shade*0.7

            frame[i][halfvres*2-j-1] = shade*(floor[xx][yy]*2+frame[i][halfvres*2-j-1])/3
            
            if nenemies < size/2 and int(x) == exitx and int(y) == exity and (x%1-0.5)**2 + (y%1-0.5)**2 < 0.2:
                ee = j/(10*halfvres)
                frame[i][j:2*halfvres-j] = (ee*np.ones(3)+frame[i][j:2*halfvres-j])/(1+ee)

    return frame

@njit()
def vision(posx, posy, enx, eny, dist2p, maph, size):
    cos, sin = (posx-enx)/dist2p, (posy-eny)/dist2p
    x, y = enx, eny
    seen = 1
    x, y = x +0.25*cos, y +0.25*sin
    for i in range(abs(int((dist2p-0.5)/0.05))):
        x, y = x +0.05*cos, y +0.05*sin
        if (maph[int(x-0.02)%(size-1)][int(y-0.02)%(size-1)] or
            maph[int(x-0.02)%(size-1)][int(y+0.02)%(size-1)] or
            maph[int(x+0.02)%(size-1)][int(y-0.02)%(size-1)] or
            maph[int(x+0.02)%(size-1)][int(y+0.02)%(size-1)]):
            seen = 0
            break
    return seen

@njit()
def enemies_ai(posx, posy, enemies, maph, size, mape, swordsp, ticks, player_health):
    for en in range(len(enemies)): # friends = heatmap
        if enemies[en][8] > 0:
            x, y = int(enemies[en][0]), int(enemies[en][1])
            mape[x-1:x+2, y-1:y+2] = mape[x-1:x+2, y-1:y+2] + 1

    for en in range(len(enemies)):
        if enemies[en][8] > 0 and np.random.uniform(0,1) < 0.1: # update only % of the time            
            enx, eny, angle =  enemies[en][0], enemies[en][1], enemies[en][6]
            health, state, cooldown = enemies[en][8], enemies[en][9], enemies[en][10]
            dist2p = np.sqrt((enx-posx)**2 + (eny-posy)**2 + 1e-16)
            
            friends = mape[int(enx)][int(eny)] - 1
            if dist2p > 1.42: # add friends near the player if not too close
                friends = friends + mape[int(posx)][int(posy)]

            not_afraid = 0
            # zombies are less afraid
            if  health > 1 + enemies[en][4] or health + friends > 3 + enemies[en][4]:
                not_afraid = 1
                
            if state == 0 and dist2p < 6:  # normal
                angle = angle2p(enx, eny, posx, posy)
                angle2 = (enemies[en][6]-angle)%(2*np.pi)
                if angle2 > 11*np.pi/6 or angle2 < np.pi/6 or (swordsp >= 1 and dist2p < 3): # in fov or heard
                    if vision(posx, posy, enx, eny, dist2p, maph, size):
                        if not_afraid and ticks - cooldown > 5:
                            state = 1 # turn aggressive
                        else:
                            state = 2 # retreat
                            angle = angle - np.pi
                    else:
                        angle = enemies[en][6] # revert to original angle

            elif state == 1: # aggressive
                if dist2p < 0.6 and ticks - cooldown > 10: # perform attack, 2s cooldown
                    enemies[en][10] = ticks # reset cooldown, damage is lower with more enemies on same cell
                    player_health = player_health - np.random.uniform(0,1)/np.sqrt(1+mape[int(posx)][int(posy)])
                    state = 2
                if not_afraid: # turn to player
                    angle = angle2p(enx, eny, posx, posy)
                else: # retreat
                    state = 2
                    
            elif state == 2: # defensive
                if not_afraid and ticks - cooldown > 5:
                    state = 0
                else:
                    angle = angle2p(posx, posy, enx, eny) + np.random.uniform(-0.5, 0.5) #turn around

            enemies[en][6], enemies[en][9]  = angle+ np.random.uniform(-0.2, 0.2), state
            
    return enemies, player_health, mape

@njit()
def check_walls(posx, posy, maph, x, y): # for walking
    if not(maph[int(x-0.2)][int(y)] or maph[int(x+0.2)][int(y)] or #check all sides
           maph[int(x)][int(y-0.2)] or maph[int(x)][int(y+0.2)]):
        posx, posy = x, y
        
    elif not(maph[int(posx-0.2)][int(y)] or maph[int(posx+0.2)][int(y)] or # move only in y
             maph[int(posx)][int(y-0.2)] or maph[int(posx)][int(y+0.2)]):
        posy = y
        
    elif not(maph[int(x-0.2)][int(posy)] or maph[int(x+0.2)][int(posy)] or # move only in x
             maph[int(x)][int(posy-0.2)] or maph[int(x)][int(posy+0.2)]):
        posx = x
        
    return posx, posy

@njit()
def angle2p(posx, posy, enx, eny):
    angle = np.arctan((eny-posy)/(enx-posx+1e-16))
    if abs(posx+np.cos(angle)-enx) > abs(posx-enx):
        angle = (angle - np.pi)%(2*np.pi)
    return angle

@njit()
def sort_sprites(posx, posy, rot, enemies, maph, size, er):
    for en in range(len(enemies)):
        enemies[en][3] = 9999
        if enemies[en][8] > 0: # dont bother with the dead
            enx, eny = enemies[en][0], enemies[en][1]
            backstep = 1
            if enemies[en][9] == 1 and enemies[en][3] > 1.7 and enemies[en][3] < 10:
                backstep = -1 # avoid going closer than necessary to the player
            speed = backstep*er*(1+enemies[en][9]/2)
            cos, sin = speed*np.cos(enemies[en][6]), speed*np.sin(enemies[en][6])
            x, y = enx+cos, eny+sin
            enx, eny = check_walls(enx, eny, maph, x, y)
            if enx == enemies[en][0] or eny == enemies[en][1]: #check colisions
                enemies[en][6] = enemies[en][6] + np.random.uniform(-0.5, 0.5)
                if np.random.uniform(0,1) < 0.01:
                    enemies[en][9] = 0 # return to normal state
            enemies[en][0], enemies[en][1] = enx, eny
            
            angle = angle2p(posx, posy, enx, eny)
            angle2= (rot-angle)%(2*np.pi)
            if angle2 > 10.5*np.pi/6 or angle2 < 1.5*np.pi/6:
                dir2p = ((enemies[en][6] - angle -3*np.pi/4)%(2*np.pi))/(np.pi/2)
                dist2p = np.sqrt((enx-posx)**2+(eny-posy)**2+1e-16)
                enemies[en][2] = angle2
                enemies[en][7] = dir2p
                if vision(enx, eny, posx, posy, dist2p, maph, size):
                    enemies[en][3] = 1/dist2p

    enemies = enemies[enemies[:, 3].argsort()]
    return enemies

def spawn_enemies(number, maph, msize, posx, posy):
    enemies = []
    for i in range(number):
        x, y = np.random.randint(1, msize-2), np.random.randint(1, msize-2)
        while maph[x][y] or (x == int(posx) and y == int(posy)):
            x, y = np.random.randint(1, msize-2), np.random.randint(1, msize-2)
        x, y = x+0.5, y+0.5
        angle2p, invdist2p, dir2p = 0, 1, 0 # angle, inv dist, dir2p relative to player
        entype = np.random.choice([0,1]) # 0 zombie, 1 skeleton
        direction = np.random.uniform(0, 2*np.pi) # facing direction
        size = np.random.uniform(7, 10)
        health = size/2
        state = np.random.randint(0,3) # 0 normal, 1 aggressive, 2 defensive
        cooldown = 0 # atack cooldown
        enemies.append([x, y, angle2p, invdist2p, entype, size, direction, dir2p, health, state, cooldown])
#                       0, 1,       2,         3,      4,    5,         6,     7,      8,     9,       10
    return np.asarray(enemies)

def get_sprites(hres):
    sheet = pg.image.load('Assets/Sprites/zombie_n_skeleton4.png').convert_alpha()
    sprites = [[], []]
    swordsheet = pg.image.load('Assets/Sprites/sword1.png').convert_alpha() 
    sword = []
    for i in range(3):
        sword.append(pg.Surface.subsurface(swordsheet,(i*800,0,800,600)))
        xx = i*32
        sprites[0].append([])
        sprites[1].append([])
        for j in range(4):
            yy = j*100
            sprites[0][i].append(pg.Surface.subsurface(sheet,(xx,yy,32,100)))
            sprites[1][i].append(pg.Surface.subsurface(sheet,(xx+96,yy,32,100)))

    spsize = np.asarray(sprites[0][1][0].get_size())*hres/800

    sword.append(sword[1]) # extra middle frame
    swordsp = 0 #current sprite for the sword
    
    return sprites, spsize, sword, swordsp

def draw_sprites(surf, sprites, enemies, spsize, hres, halfvres, ticks, sword, swordsp, rotv):
    #enemies : x, y, angle2p, dist2p, type, size, direction, dir2p
    offset = int(rotv*halfvres)
    cycle = int(ticks)%3 # animation cycle for monsters
    for en in range(len(enemies)):
        if enemies[en][3] >  10:
            break
        types, dir2p = int(enemies[en][4]), int(enemies[en][7])
        cos2 = np.cos(enemies[en][2])
        scale = min(enemies[en][3], 2)*spsize*enemies[en][5]/cos2*hres/250
        vert = halfvres + halfvres*min(enemies[en][3], 2)/cos2 - offset
        hor = hres/2 - hres*np.sin(enemies[en][2])
        spsurf = pg.transform.scale(sprites[types][cycle][dir2p], scale)
        surf.blit(spsurf, (hor,vert)-scale/2)

    swordpos = (np.sin(ticks)*10*hres/800,(np.cos(ticks)*10+15)*hres/800) # sword shake
    spsurf = pg.transform.scale(sword[int(swordsp)], (hres, halfvres*2))
    surf.blit(spsurf, swordpos)

    return surf, en-1

def load_sounds():
    sounds = {}
    sounds['step'] = pg.mixer.Sound('Assets/Sounds/playerstep.mp3')
    sounds['step2'] = pg.mixer.Sound('Assets/Sounds/enemystep.mp3')
    sounds['swoosh'] = pg.mixer.Sound('Assets/Sounds/sword.mp3')
    sounds['hurt'] = pg.mixer.Sound('Assets/Sounds/damage.mp3')
    sounds['deadmonster'] = pg.mixer.Sound('Assets/Sounds/deadmonster.mp3')
    sounds['hitmonster'] = pg.mixer.Sound('Assets/Sounds/hitmonster.mp3')
    sounds['hitmonster2'] = pg.mixer.Sound('Assets/Sounds/hitmonster2.mp3')
    sounds['healthup'] = pg.mixer.Sound('Assets/Sounds/healthup.wav')
    sounds['died'] = pg.mixer.Sound('Assets/Sounds/died.wav')
    sounds['won'] = pg.mixer.Sound('Assets/Sounds/won.wav')
    sounds['music'] = pg.mixer.Sound('Assets/Sounds/battlemusic0.mp3')

    return sounds

def pause_menu(surf, menu, pause, options, click, running, m_vol, sfx_vol, sounds, newgame, font, msg, level, ticks, hres):
    adjust_res = 1
    p_mouse = pg.mouse.get_pos()
    if options == 0: # main menu
        if p_mouse[0] < 500 and p_mouse[1] > 200 and p_mouse[1] < 265: # continue
            pg.draw.rect(surf,(150,250,150),(0,200,500,65))
            if click:
                if newgame == 2:
                    newgame = 1
                else:
                    pause = 0
                pg.mouse.set_pos(400,300)
        elif p_mouse[0] < 500 and p_mouse[1] > 300 and p_mouse[1] < 365: # new game
            pg.draw.rect(surf,(150,150,250),(0,300,500,65))
            if click:
                newgame = 1
        elif p_mouse[0] < 500 and p_mouse[1] > 400 and p_mouse[1] < 465: # options
            pg.draw.rect(surf,(150,150,150),(0,400,500,65))
            if click:
                options = 1
        elif p_mouse[0] < 500 and p_mouse[1] > 500 and p_mouse[1] < 565: # leave
            pg.draw.rect(surf,(250,150,150),(0,500,500,65))
            if click:
                running = 0
        elif p_mouse[0] > 679 and p_mouse[1] > 509: # i button
            pg.draw.circle(surf,(250,150,150),(736,556), 42)
            if click:
                options = 2
        surf.blit(menu[options], (0,0))
        surf.blit(font.render(msg, 1, (255, 255, 255)), (30, 100+5*np.sin(ticks-1)))
        surf.blit(font.render(msg, 1, (30, 255, 155)), (32, 100+5*np.sin(ticks)))
        surf.blit(font.render(str(level), 1, (255, 255, 255)), (675, 275+5*np.sin(ticks-1)))
        surf.blit(font.render(str(level), 1, (255, 100, 50)), (677, 275+5*np.sin(ticks)))

    elif options == 1: # options menu
        if p_mouse[0] > 50 and  p_mouse[0] < 130 and p_mouse[1] > 220 and p_mouse[1] < 290: # -resol
            pg.draw.rect(surf,(150,250,150),(60,220,70,70))
            if click:
                adjust_res = 0.9
        elif p_mouse[0] > 650 and  p_mouse[0] < 720 and p_mouse[1] > 220 and p_mouse[1] < 290: # +resol
            pg.draw.rect(surf,(150,250,150),(650,220,70,70))
            if click:
                adjust_res = 1.1
        elif click and p_mouse[0] > 123 and  p_mouse[0] < 646 and p_mouse[1] > 360 and p_mouse[1] < 424:
            sfx_vol = (p_mouse[0] - 123)/523
        elif click and p_mouse[0] > 123 and  p_mouse[0] < 646 and p_mouse[1] > 512 and p_mouse[1] < 566:
            m_vol = (p_mouse[0] - 123)/523

        surf.blit(menu[options], (0,0))
        pg.draw.polygon(surf, (50, 200, 50), ((123, 414), (123+523*sfx_vol, 414-54*sfx_vol), (123+520*sfx_vol, 418)))
        pg.draw.polygon(surf, (50, 200, 50), ((123, 566), (123+523*m_vol, 566-54*m_vol), (123+520*m_vol, 570)))
        surf.blit(font.render(str(hres)+" x "+str(int(hres*0.375)), 1, (255, 255, 255)), (200, 220+5*np.sin(ticks-1)))
        surf.blit(font.render(str(hres)+" x "+str(int(hres*0.375)), 1, (255, 100, 50)), (202, 220+5*np.sin(ticks)))

    elif options == 2: # info
        surf.blit(menu[options], (0,0))
        
    if p_mouse[0] > 729 and p_mouse[1] < 60 : # x button
        pg.draw.circle(surf,(0,0,0),(768,31), 30)
        if click:
            if options == 0:
                if newgame == 2:
                    newgame = 1
                else:
                    pause = 0
                pg.mouse.set_pos(400,300)
            else:
                options = 0
        surf.blit(menu[options], (0,0))
                
    #draw cursor
    pg.draw.polygon(surf, (200, 50, 50), ((p_mouse), (p_mouse[0]+20, p_mouse[1]+22), (p_mouse[0], p_mouse[1]+30)))
    
    return surf, pause, options, running, newgame, adjust_res, m_vol, sfx_vol

def adjust_resolution(hres=250):
    hres = max(min(hres, 800), 80) # limit range from 80x60 to 800x600
    halfvres = int(hres*0.375) #vertical resolution/2
    mod = hres/60 #scaling factor (60° fov)
    frame = np.random.uniform(0,1, (hres, halfvres*2, 3))
    
    return hres, halfvres, mod, frame

def set_volume(m_vol, sfx_vol, sounds):
    for key in sounds.keys():
        sounds[key].set_volume(sfx_vol)
    sounds['music'].set_volume(m_vol)

def splash_screen(msg, splash, clock, font, screen):
    running = 1
    while running:
        clock.tick(60)
        surf = splash.copy()
        ticks = pg.time.get_ticks()/200
        surf.blit(font.render(msg, 1, (0, 0, 0)), (50, 500+5*np.sin(ticks-1)))
        surf.blit(font.render(msg, 1, (255, 255, 255)), (52, 500+5*np.sin(ticks)))

        p_mouse = pg.mouse.get_pos()
        pg.draw.polygon(surf, (200, 50, 50), ((p_mouse), (p_mouse[0]+20, p_mouse[1]+22), (p_mouse[0], p_mouse[1]+30)))

        screen.blit(surf, (0,0))
        pg.display.update()

        for event in pg.event.get():
            if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
                return 0
            elif event.type == pg.QUIT:
                pg.quit()
    
if __name__ == '__main__':
    main()
    pg.mixer.fadeout(1000)
    pg.time.wait(1000)
    pg.quit()
