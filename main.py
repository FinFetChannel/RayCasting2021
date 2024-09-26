# /// script
# dependencies = [
#  "numpy",
# ]
# ///
import numpy as np
import pygame as pg
import pygame.surfarray
import asyncio
import math


async def main():
    FOV = 60
    pg.init()
    pg.display.set_caption("Dead and - A Python game by FinFET, thanks for playing!")
    font = pg.font.SysFont("Courier New", 70)
    
    sounds = load_sounds()
    m_vol, sfx_vol, music = 0.4, 0.5, 0
    set_volume(m_vol, sfx_vol, sounds)
    sounds['music'+str(music)].play(-1)
    
    stepdelay = pg.time.get_ticks()/200
    stepdelay2 = stepdelay
    click, clickdelay = 0, stepdelay
    
    screen = pg.display.set_mode((800,600))
        
    running, pause, options, newgame = 1, 1, 0, 2
    clock = pg.time.Clock()
    pg.mouse.set_visible(False)
    pg.event.set_grab(1)
    timer = 0
    hres, halfvres, mod, frame, half_frame = adjust_resolution()
    fullscreen = 0
    level, player_health, swordsp, story = 0, 0, 0, 0

    #sky1, floor, wall, door, window, enemies
    level_textures = [[0, 1, 0, 0, 1, 4], #level 0
                      [0, 2, 1, 1, 0, 3], #level 1
                      [1, 0, 2, 1, 1, 4], #level 2
                      [1, 3, 1, 0, 0, 1], #level 3
                      [2, 1, 2, 1, 1, 0], #level 4
                      [2, 0, 0, 0, 0, 2]] #level 5

    menu = [pg.image.load('Assets/Textures/menu0.png').convert_alpha()]
    menu.append(pg.image.load('Assets/Textures/options.png').convert_alpha())
    menu.append(pg.image.load('Assets/Textures/credits.png').convert_alpha())
    menu.append(pg.image.load('Assets/Textures/menu1.png').convert_alpha())
    hearts = apply_colorkey('Assets/Textures/hearts.png')#.convert_alpha()
    colonel = pg.image.load('Assets/Sprites/colonel1.png').convert_alpha()
    hearts2 = pg.Surface.subsurface(hearts,(0,0,max(1,player_health*10),20))
    exit1 = apply_colorkey('Assets/Textures/exit.png')#.convert_alpha()
    exit2 = 1
    exits = [pg.Surface.subsurface(exit1,(0,0,50,50)), pg.Surface.subsurface(exit1,(50,0,50,50))]
    splash = []
    for i in range(4):
        splash.append(pg.image.load('Assets/Textures/splash'+str(i)+'.jpg').convert())
    blood = apply_colorkey('Assets/Textures/blood0.png', (255, 0, 0))
    blood_size = np.asarray(blood.get_size())
    sky1 = hearts.copy() # initialize with something to adjust resol on start
    msg = "Dead and, web version"
    surf = splash[0].copy()
    await splash_screen(msg, splash[0], clock, font, screen)
    msg = " "
    fps = 60
    enable_floor = 1
    
    while running:
        pg.display.update()
        ticks = pg.time.get_ticks()/200
        er = min(clock.tick()/500, 0.3)
        if not pause and (player_health <= 0 or (exit2 == 0  and int(posx) == exitx and int(posy) == exity)):
            msg = ' '
            if player_health <= 0:
                sounds['died'].play()
                newgame = 2
                surf = splash[3].copy()
            else:
                level += 1
                player_health = min(player_health+2, 20)
                sounds['won'].play()
                newgame = 1
                if level > 5:
                    level, newgame = 0, 2
                    sounds['died'].play()
                    surf = splash[2].copy()
                    surf.blit(font.render('Total time: ' + str(round(timer,1)), 1, (255, 255, 255)), (20, 525))
                else:
                    msg = "Cleared level " + str(level-1)+'!'
            await splash_screen(msg, surf, clock, font, screen)
            pause, clickdelay = 1, ticks
            pg.time.wait(500)

        if pg.mouse.get_pressed()[0]:
            if swordsp < 1 and not pause:
                swordsp, damage_mod = 1, 1
            if pause and ticks - clickdelay > 1:
                click, clickdelay = 1, ticks
                sounds['healthup'].play()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                    
            if event.type == pg.KEYDOWN:
                if event.key == ord('p') or event.key == pg.K_ESCAPE:
                    if not pause:
                        pause = 1
                    else:
                        if options > 0:
                            options = 0
                        elif newgame == 0:
                            pause = 0
                    pg.mouse.set_pos(400,300)

        if  pause:
            clock.tick(60)

            surf2, pause, options, running, newgame, adjust_res, m_vol, sfx_vol, story = pause_menu(
                surf.copy(), menu, pause, options, click, running, m_vol, sfx_vol, sounds, newgame, font, msg, level, ticks, hres, story)

            screen.blit(surf2, (0,0))
            click = 0
            
            if newgame == 1:
                newgame, pause = 0, not(pause)
                if player_health <= 0 or msg[0] != 'C':
                    surf = splash[1].copy()
                    await splash_screen(' ', surf, clock, font, screen)
                    level, player_health, timer = 0, 20, -0.1

                if np.random.randint(0, 2) != music:
                    sounds['music'+str(music)].fadeout(1000)
                    music = int(not(music))
                    sounds['music'+str(music)].play(-1)
                
                msg = 'Loading...'
                surf2 = surf.copy()
                surf2.blit(font.render(msg, 1, (255, 255, 255)), (30, 500))
                surf2.blit(font.render(msg, 1, (30, 255, 155)), (32, 502))
                screen.blit(surf2, (0,0))
                pg.display.update()
                msg = 'Kill the monsters!'

                if story:
                    posx, posy, rot, rotv, maph, mapc, exitx, exity, stepscount, size = load_map(level)
                    nlevel = level_textures[level]
                    
                else:
                    size = np.random.randint(10+level*2, 16+level*2)
                    nenemies = size #number of enemies
                    posx, posy, rot, rotv, maph, mapc, exitx, exity, stepscount = gen_map(size)
                    nlevel = [np.random.randint(0,3), #sky1
                              np.random.randint(0,4), #floorwall
                              np.random.randint(0,3), #wall
                              np.random.randint(0,2), #door
                              np.random.randint(0,2), #window
                              np.random.randint(0,5), #enemies
                              ]

                nenemies = level**2 + 10 + level #number of enemies
                sprites, spsize, sword, swordsp = get_sprites(nlevel[5])
                sky1, floor, textures = load_textures(nlevel)
                avg_floor = (np.mean(floor[:,:,0]),np.mean(floor[:,:,1]),np.mean(floor[:,:,2]))

                sky = pg.transform.smoothscale(sky1, (12*hres*60/FOV, 3*halfvres*2))
                enemies = spawn_enemies(nenemies, maph, size, posx, posy, level/2)
                hearts2 = pg.Surface.subsurface(hearts,(0,0,max(1,player_health*10),20))
                exit2, damage_mod, blood_scale = 1, 1, 1
                mape, minimap = np.zeros((size, size)), np.zeros((size, size, 3))
                sounds['healthup'].play()

        else:
            timer = timer + er/2

            offset = -rotv*halfvres
            if enable_floor > 1:
                surf = floorcasting(posx, posy, rot, FOV, 1/mod, frame, floor, offset)
            elif enable_floor == 1:
                surf = floorcasting(posx, posy, rot, FOV, 2/mod, half_frame, floor, offset/2)
                surf = pg.transform.scale2x(surf)
            else:
                surf = pg.surface.Surface((hres, halfvres*2))
                surf.fill(avg_floor)
            sub_sky = pg.Surface.subsurface(sky, (math.degrees(rot%(2*math.pi)*hres/FOV), halfvres*2-offset, hres, halfvres+offset))
            surf.blit(sub_sky, (0, 0))
            raycast_walls(surf, 1/mod, FOV, maph, posx, posy, rot, offset, textures, mapc)

            mape = np.zeros((size, size))
            health = player_health
            enemies, player_health, mape = enemies_ai(posx, posy, enemies, maph, size, mape, swordsp, ticks, player_health, nenemies, level/3)
            enemies = sort_sprites(posx-0.2*np.cos(rot), posy-0.2*np.sin(rot), rot, enemies, maph, size, er/3)
            if exit2 == 0:
                surf = draw_colonel(surf, colonel, posx-0.2*np.cos(rot), posy-0.2*np.sin(rot), exitx+0.5, exity+0.5,
                                    hres, halfvres, rot, rotv, maph, size)
            surf, en = draw_sprites(surf, sprites, enemies, spsize, hres, halfvres, ticks, sword, swordsp, rotv)
            
            if int(swordsp) > 0 and damage_mod < 1:
                blood_scale = blood_scale*(1 + 2*er)
                scaled_blood = pg.transform.scale(blood, 4*blood_scale*blood_size*hres/800)
                surf.blit(scaled_blood, np.asarray([hres/2, halfvres]) - 2*blood_scale*blood_size*hres/800)
            #surf = pg.transform.scale2x(surf)
            surf = pg.transform.scale(surf, (800, 600))
            surf.blit(hearts2, (20,20))

            if exit2 == 0:
                minimap[int(posx)][int(posy)] = (50, 50, 255)
                surfmap = pg.surfarray.make_surface(minimap.astype('uint8'))
                surfmap = pg.transform.scale(surfmap, (size*5, size*5))
                surf.blit(surfmap,(20, 50), special_flags=pg.BLEND_ADD)
                minimap[int(posx)][int(posy)] = (100, 100, 0)

            surf.blit(font.render(str(round(timer,1)), 1, (255, 255, 255)), (20, 525))
            surf.blit(exits[exit2], (730,20))
            screen.blit(surf, (0,0))
            

            if health > player_health:
                hearts2 = pg.Surface.subsurface(hearts,(0,0,max(1,player_health*10),20))
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
                    damage_mod = 1        
                    while enemies[en][3] < 10 and damage_mod > 0.4  and en >= 0:
                        x = posx -0.2*np.cos(rot) + np.cos(rot + np.random.uniform(0, 0.05))/enemies[en][3]
                        y = posy -0.2*np.sin(rot) + np.sin(rot + np.random.uniform(0, 0.05))/enemies[en][3]
                        z = 0.5 + np.sin(rotv*-0.392699)/enemies[en][3]
                        dist2en = np.sqrt((enemies[en][0]-x)**2 + (enemies[en][1]-y)**2)
                        if dist2en < 0.1 and z > 0 and z < 0.07*enemies[en][5]:
                            if z > 0.05*enemies[en][5]:
                                enemies[en][8] = enemies[en][8] - np.random.uniform(0,2)*2
                            else:
                                enemies[en][8] = enemies[en][8] - np.random.uniform(0,2)
                        
                            enemies[en][10] = ticks
                            x = enemies[en][0] + 0.1*np.cos(rot)
                            y = enemies[en][1] + 0.1*np.sin(rot)
                            if maph[int(x)][int(y)] == 0:
                                enemies[en][0]= (x + enemies[en][0])/2 # push back
                                enemies[en][1]= (y + enemies[en][1])/2
                            if damage_mod == 1:
                                blood_scale = enemies[en][3]
                                sounds['swoosh'].play()
                                if enemies[en][4]:
                                    sounds['hitmonster2'].set_volume(min(1, enemies[en][3])*sfx_vol)
                                    sounds['hitmonster2'].play()
                                else:
                                    sounds['hitmonster'].set_volume(min(1, enemies[en][3])*sfx_vol)
                                    sounds['hitmonster'].play()
                            damage_mod = damage_mod*0.5
                            if enemies[en][8] < 0:
                                sounds['deadmonster'].set_volume(min(1, enemies[en][3])*sfx_vol)
                                sounds['deadmonster'].play()
                                nenemies = nenemies - 1
                                if nenemies == 0:
                                    exit2, msg = 0, "Find the master!"
##                                if np.random.uniform(0,1) < 0.3:
##                                    player_health = min(player_health+0.5, 20)
##                                    hearts2 = pg.Surface.subsurface(hearts,(0,0,player_health*10,20))
##                                    sounds['healthup'].play()                           
                        en = en - 1

                    if damage_mod == 1:
                        sounds['swoosh2'].play()                        
                swordsp = (swordsp + er*10)%4

            fps = int(clock.get_fps())
            if fps < 20 and enable_floor > 0:
                enable_floor -= 1

            elif fps > 45 and enable_floor < 2:
                enable_floor += 1

            
            #pg.display.set_caption("Health: "+str(round(player_health, 1))+" Enemies: " + str(nenemies) + " FPS: " + str(fps)+ ' '+str(enable_floor)+' '+ msg)
            posx, posy, rot, rotv = movement(pg.key.get_pressed(), posx, posy, rot, maph, er, rotv)
##            pg.mouse.set_pos(400,300)
        if adjust_res != 1:
            hres, halfvres, mod, frame, half_frame  = adjust_resolution(int(hres*adjust_res))
            sky = pg.transform.smoothscale(sky1, (12*hres*60/FOV, 3*halfvres*2))
            adjust_res = 1 
        await asyncio.sleep(0)

def floorcasting(x_pos, y_pos, rot, FOV, mod, frame, floor, offset):
    size = floor.shape
    screen_size = frame.shape#screen.get_size()
    halfvres = int(screen_size[1]/2)
    hres = int(screen_size[0])
    n_pixels = int(halfvres - offset)
    ns = halfvres/((halfvres - offset +0.1-np.linspace(0, halfvres- offset, n_pixels)))# depth

    for i in range(hres):
        rot_i = rot + math.radians(i*mod - FOV*0.5)
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(rot_i-rot)
        xs, ys = x_pos+ns*cos/cos2, y_pos+ns*sin/cos2
        xxs, yys = ((50*xs)%size[0]).astype('int'), ((50*ys)%size[1]).astype('int')
        frame[i][2*halfvres-n_pixels:] = floor[np.flip(xxs),np.flip(yys)]#* shade 

    return pg.surfarray.make_surface(frame)

def raycast_walls(screen, mod, FOV, mapa, x_pos, y_pos, rot, offset, textures, mapc):
    horizontal_res, vertical_res = screen.get_size()
    # blit_list = []
    for i in range(horizontal_res): #vision loop
        rot_i = rot + math.radians(i*mod - FOV*0.5)
        x1, y1, x2, y2, dist_near, dist_far = lodev_DDA(x_pos, y_pos, rot_i, mapa)
        draw_wall_slice(x2, y2, dist_far, mod, FOV, textures, screen, mapc, mapa, vertical_res, offset, i, 3)
        draw_wall_slice(x1, y1, dist_near, mod, FOV, textures, screen, mapc, mapa, vertical_res, offset, i)

def draw_wall_slice(x, y, dist, mod, FOV, textures, screen, mapc, mapa, vertical_res, offset, i, shift=1):
    
    texture = mapa[int(x)][int(y)] - 1
    if texture > 2 and shift == 1:
        texture = 1
    else: texture = 2
    text_coord = x%1
    if text_coord < 0.001 or text_coord > 0.999:
        text_coord = y%1
    scale = int(vertical_res/max(0.2, dist*math.cos(math.radians(i*mod-FOV*0.5))))
    color = mapc[int(x)][int(y)]
    texture_size = textures[texture].get_size()
    subsurface = pg.Surface.subsurface(textures[texture], (texture_size[0]*text_coord, 0, 1, texture_size[1]))
    resized = pg.transform.smoothscale(subsurface, (1,scale))
    tint = pygame.Surface((1,scale))
    if x%1 > y%1:
        color = (color[0]//3, color[1]//3, color[2]//3)
    tint.fill(color)
    tint.set_alpha(60)
    resized.blit(tint, (0,0))
    screen.blit(resized, (i, (vertical_res-shift*scale)*0.5+offset))

def lodev_DDA(x, y, rot_i, mapa):
    sizeX = len(mapa) - 1
    sizeY = len(mapa[0]) - 1
    sin, cos = math.sin(rot_i), math.cos(rot_i)
    norm = math.sqrt(cos**2 + sin**2)
    rayDirX, rayDirY = cos/norm + 1e-16, sin/norm + 1e-16
    x1, y1, x2, y2, dist_near, dist_far = 0, 0, 0, 0, 999, 999

    mapX, mapY = int(x), int(y)

    deltaDistX, deltaDistY = abs(1/rayDirX), abs(1/rayDirY)

    if rayDirX < 0:
        stepX, sideDistX = -1, (x - mapX) * deltaDistX
    else:
        stepX, sideDistX = 1, (mapX + 1.0 - x) * deltaDistX
        
    if rayDirY < 0:
        stepY, sideDistY = -1, (y - mapY) * deltaDistY
    else:
        stepY, sideDistY = 1, (mapY + 1 - y) * deltaDistY

    for i in range(30):
        if (sideDistX < sideDistY):
            sideDistX += deltaDistX
            mapX += stepX
            dist = sideDistX
            side = 0
            if mapX < 0 or mapX > sizeX:
                return x1, y1, x2, y2, dist_near, dist_far
        else:
            sideDistY += deltaDistY
            mapY += stepY
            dist = sideDistY
            side = 1
            if mapY < 0 or mapY > sizeY:
                return x1, y1, x2, y2, dist_near, dist_far
        if (mapa[mapX][mapY] > 0 and dist_near == 999) or mapa[mapX][mapY] > 2:
            if side:
                dist2 = dist - deltaDistY + 0.0001
            else:
                dist2 = dist - deltaDistX + 0.0001
            if dist_near == 999:
                dist_near = dist2
                x1 = (x + rayDirX*dist_near)%sizeX
                y1 = (y + rayDirY*dist_near)%sizeY
            if mapa[mapX][mapY] > 2:
                dist_far = dist2
                x2 = (x + rayDirX*dist_far)%sizeX
                y2 = (y + rayDirY*dist_far)%sizeY
                break
        
    return x1, y1, x2, y2, dist_near, dist_far  

def movement(pressed_keys, posx, posy, rot, maph, et, rotv):
    x, y, diag = posx, posy, 0
    p_mouse = pg.mouse.get_rel()
    if abs(p_mouse[0]) > 1:
        rot = rot + et*p_mouse[0]/20
    if abs(p_mouse[1]) > 1:
        rotv = rotv + et*p_mouse[1]/20
        rotv = np.clip(rotv, -0.99, .99)

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
    mapc = np.random.random_integers(0,255, (size,size,3)) 
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

def load_map(level):
    mapc = pg.surfarray.array3d(pg.image.load('Assets/Levels/map'+str(level)+'.png'))
    size = len(mapc)
    maph = np.random.choice([1, 2, 3, 4], (size,size))
    colors = np.asarray([[0,0,0], [255,255,255], [127,127,127]])
    posx, exitx = None, None
    for i in range(size):
        for j in range(size):
            color = mapc[i][j]
            if (color == colors[0]).all() or (color == colors[1]).all() or (color == colors[2]).all():
                maph[i][j] = 0
                if (color == colors[1]).all():
                    posx, posy = i+0.5, j+0.5
                if (color == colors[2]).all():
                    exitx, exity = i, j
                 
    while posx == None: # if no start is found
        x, y = np.random.randint(1, size), np.random.randint(1, size)
        if (mapc[x][y] == colors[0]).all():
            posx, posy = x+0.5, y+0.5
            
    while exitx == None: # if no exit is found
        x, y = np.random.randint(1, size), np.random.randint(1, size)
        if (mapc[x][y] == colors[0]).all():
            exitx, exity = x, y
            
    rot, rotv, stepscount = np.pi/4, 0, posx + posy
    
    return posx, posy, rot, rotv, maph, mapc, exitx, exity, stepscount, size

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

def enemies_ai(posx, posy, enemies, maph, size, mape, swordsp, ticks, player_health, nenemies, level=0):
    if nenemies < 5: # teleport far enemies closer
        for en in range(len(enemies)): # mape = enemies heatmap
            if enemies[en][8] > 0:
                enx, eny =  enemies[en][0], enemies[en][1]
                dist2p = np.sqrt((enx-posx)**2 + (eny-posy)**2 + 1e-16)
                if dist2p > 10:
                    for i in range(10):
                        x, y = np.random.randint(1, size), np.random.randint(1, size)
                        dist2p = np.sqrt((x+0.5-posx)**2 + (y+0.5-posy)**2 + 1e-16)
                        if dist2p > 6 and dist2p < 8 and maph[x][y] == 0:
                            enemies[en][0], enemies[en][1] = x + 0.5, y + 0.5
                            break

    for en in range(len(enemies)): # mape = enemies heatmap
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
            if  health > 1 + enemies[en][4] - level or health + friends > 3 + enemies[en][4] - level:
                not_afraid = 1
                
            if state == 0 and dist2p < 6:  # normal
                angle = angle2p(enx, eny, posx, posy)
                angle2 = (enemies[en][6]-angle)%(2*np.pi)
                if angle2 > 11*np.pi/6 or angle2 < np.pi/6 or (swordsp >= 1 and dist2p < 3): # in fov or heard
                    if vision(posx, posy, enx, eny, dist2p, maph, size):
                        if not_afraid and ticks - cooldown > 5:
                            state = 1 # turn aggressive
                        elif dist2p < 2:
                            state = 2 # retreat
                            angle = angle - np.pi
                    else:
                        angle = enemies[en][6] # revert to original angle

            elif state == 1: # aggressive
                if dist2p < 0.8 and ticks - cooldown > 10: # perform attack, 2s cooldown
                    enemies[en][10] = ticks # reset cooldown, damage is lower with more enemies on same cell
                    player_health = player_health - np.random.uniform(0.5, 1 + level/2)/np.sqrt(1+mape[int(posx)][int(posy)])
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

def angle2p(posx, posy, enx, eny):
    angle = np.arctan((eny-posy)/(enx-posx+1e-16))
    if abs(posx+np.cos(angle)-enx) > abs(posx-enx):
        angle = (angle - np.pi)%(2*np.pi)
    return angle

def sort_sprites(posx, posy, rot, enemies, maph, size, er):
    for en in range(len(enemies)):
        enemies[en][3] = 9999
        if enemies[en][8] > 0: # dont bother with the dead
            enx, eny = enemies[en][0], enemies[en][1]
            backstep = 1
            if enemies[en][9] == 1 and enemies[en][3] > 1.7 and enemies[en][3] < 10:
                backstep = -1 # avoid going closer than necessary to the player
            speed = backstep*er*(2+enemies[en][9]/2)
            cos, sin = speed*np.cos(enemies[en][6]), speed*np.sin(enemies[en][6])
            x, y = enx+cos, eny+sin
            enx, eny = check_walls(enx, eny, maph, x, y)
            if enx == enemies[en][0] and eny == enemies[en][1]:
                x, y = enx-cos, eny-sin
                enx, eny = check_walls(enx, eny, maph, x, y)
                if enx == enemies[en][0] and eny == enemies[en][1]:
                    if maph[int(x)][int(y)] == 0:
                        enx, eny = x, y
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

def spawn_enemies(number, maph, msize, posx, posy, level=0):
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
        health = size/2 + level/3
        state = np.random.randint(0,3) # 0 normal, 1 aggressive, 2 defensive
        cooldown = 0 # atack cooldown
 #                       0, 1,       2,         3,      4,    5,         6,     7,      8,     9,       10
        enemies.append([x, y, angle2p, invdist2p, entype, size, direction, dir2p, health, state, cooldown])
    return np.asarray(enemies)

def get_sprites(level):
    sheet = apply_colorkey('Assets/Sprites/zombie_n_skeleton'+str(level)+'.png')
    sprites = [[], []]
    swordsheet = apply_colorkey('Assets/Sprites/gun2.png')
    sword = []
    for i in range(3):
        sword.append(pg.Surface.subsurface(swordsheet,(i*800,0,800,600)))
        xx = i*32
        sprites[0].append([])
        sprites[1].append([])
        for j in range(4):
            yy = j*100
            sprites[0][i].append(pg.Surface.subsurface(sheet,(xx,yy,32,50)))
            sprites[1][i].append(pg.Surface.subsurface(sheet,(xx+96,yy,32,50)))

    spsize = np.asarray(sprites[0][1][0].get_size())

    sword.append(sword[1]) # extra middle frame
    swordsp = 0 #current sprite for the sword
    
    return sprites, spsize, sword, swordsp

def apply_colorkey(path, colorkey=(55,55,55)):
    image = pg.image.load(path)
    new_image = image.copy()
    new_image.fill(colorkey)
    new_image.blit(image,(0,0))
    new_image.set_colorkey(colorkey)
    
    return new_image

def draw_sprites(surf, sprites, enemies, spsize, hres, halfvres, ticks, sword, swordsp, rotv):
    #enemies : x, y, angle2p, dist2p, type, size, direction, dir2p
    offset = int(rotv*halfvres)
    cycle = int(ticks)%3 # animation cycle for monsters
    for en in range(len(enemies)):
        if enemies[en][3] >  10:
            break
        types, dir2p = int(enemies[en][4]), int(enemies[en][7])
        cos2 = np.cos(enemies[en][2])
        scale = min(enemies[en][3], 2)*spsize*enemies[en][5]/cos2*hres/800
        vert = halfvres + halfvres*min(enemies[en][3], 2)/cos2 - offset
        hor = hres/2 - hres*np.sin(enemies[en][2])
        #if enemies[en][3] > 0.333:
        spsurf = pg.transform.scale(sprites[types][cycle][dir2p], scale)
        #else:
        #    spsurf = pg.transform.smoothscale(sprites[types][cycle][dir2p], scale)
        surf.blit(spsurf, (hor,vert)-scale)

    swordpos = (np.sin(ticks)*10*hres/800,(np.cos(ticks)*10+15)*hres/800) # sword shake
    spsurf = pg.transform.scale(sword[int(swordsp)], (hres, halfvres*2))
    surf.blit(spsurf, swordpos)

    return surf, en-1

def draw_colonel(surf, colonel, posx, posy, enx, eny, hres, halfvres, rot, rotv, maph, size):
    angle = angle2p(posx, posy, enx, eny)
    angle2= (rot-angle)%(2*np.pi)
    if angle2 > 10.5*np.pi/6 or angle2 < 1.5*np.pi/6:
        dist2p = np.sqrt((enx-posx)**2+(eny-posy)**2+1e-16)
        if vision(enx, eny, posx, posy, dist2p, maph, size):
            offset = int(rotv*halfvres)
            cos2 = np.cos(angle2)
            spsize = np.asarray(colonel.get_size())
            scale = min(1/dist2p, 2)*spsize*6/cos2*hres/800
            vert = halfvres + halfvres*min(1/dist2p, 2)/cos2 - offset
            hor = hres/2 - hres*np.sin(angle2)
            if dist2p < 3:
                spsurf = pg.transform.scale(colonel, scale)
            else:
                spsurf = pg.transform.smoothscale(colonel, scale)
            surf.blit(spsurf, (hor,vert)-scale/2)
    return surf

def load_sounds():
    sounds = {}
    sounds['step'] = pg.mixer.Sound('Assets/Sounds/playerstep.ogg')
    sounds['step2'] = pg.mixer.Sound('Assets/Sounds/enemystep.ogg')
    sounds['swoosh'] = pg.mixer.Sound('Assets/Sounds/gun.ogg')
    sounds['swoosh2'] = pg.mixer.Sound('Assets/Sounds/gun2.ogg')
    sounds['hurt'] = pg.mixer.Sound('Assets/Sounds/damage.ogg')
    sounds['deadmonster'] = pg.mixer.Sound('Assets/Sounds/deadmonster.ogg')
    sounds['hitmonster'] = pg.mixer.Sound('Assets/Sounds/hitmonster.ogg')
    sounds['hitmonster2'] = pg.mixer.Sound('Assets/Sounds/hitmonster2.ogg')
    sounds['healthup'] = pg.mixer.Sound('Assets/Sounds/healthup.ogg')
    sounds['died'] = pg.mixer.Sound('Assets/Sounds/died.ogg')
    sounds['won'] = pg.mixer.Sound('Assets/Sounds/won.ogg')
    sounds['music0'] = pg.mixer.Sound('Assets/Sounds/battlemusic0.ogg')
    sounds['music1'] = pg.mixer.Sound('Assets/Sounds/battlemusic1.ogg')

    return sounds

def pause_menu(surf, menu, pause, options, click, running, m_vol, sfx_vol, sounds, newgame, font, msg, level, ticks, hres, story):
    adjust_res = 1
    p_mouse = pg.mouse.get_pos()
    if options == 0: # main menu
        if p_mouse[0] < 600 and p_mouse[1] > 200 and p_mouse[1] < 265: # continue
            pg.draw.rect(surf,(150,250,150),(0,200,600,65))
            if click:
                if newgame == 2:
                    newgame, story = 1, 1
                else:
                    pause = 0
                pg.mouse.set_pos(400,300)
        elif p_mouse[0] < 600 and p_mouse[1] > 300 and p_mouse[1] < 365: # new game
            pg.draw.rect(surf,(150,150,250),(0,300,600,65))
            if click:
                if newgame == 0:
                    newgame = 1
                else:
                    newgame, story = 1, 0
        elif p_mouse[0] < 600 and p_mouse[1] > 400 and p_mouse[1] < 465: # options
            pg.draw.rect(surf,(150,150,150),(0,400,600,65))
            if click:
                options = 1
        elif p_mouse[0] < 600 and p_mouse[1] > 500 and p_mouse[1] < 565: # leave
            pg.draw.rect(surf,(250,150,150),(0,500,600,65))
            if click:
                if newgame == 0:
                    newgame = 2
                else:
                    running = 0
        elif p_mouse[0] > 679 and p_mouse[1] > 509: # i button
            pg.draw.circle(surf,(250,150,150),(736,556), 42)
            if click:
                options = 2
        if newgame == 0:
            surf.blit(menu[3], (0,0))
        else:
            surf.blit(menu[0], (0,0))
        if newgame == 0:
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
            set_volume(m_vol, sfx_vol, sounds)
        elif click and p_mouse[0] > 123 and  p_mouse[0] < 646 and p_mouse[1] > 512 and p_mouse[1] < 566:
            m_vol = (p_mouse[0] - 123)/523
            set_volume(m_vol, sfx_vol, sounds)
            
        surf.blit(menu[options], (0,0))
        pg.draw.polygon(surf, (50, 200, 50), ((123, 414), (123+523*sfx_vol, 414-54*sfx_vol), (123+520*sfx_vol, 418)))
        pg.draw.polygon(surf, (50, 200, 50), ((123, 566), (123+523*m_vol, 566-54*m_vol), (123+520*m_vol, 570)))
        surf.blit(font.render(str(hres)+" x "+str(4*int(hres*0.75/4)), 1, (255, 255, 255)), (200, 220+5*np.sin(ticks-1)))
        surf.blit(font.render(str(hres)+" x "+str(4*int(hres*0.75/4)), 1, (255, 100, 50)), (202, 220+5*np.sin(ticks)))

    elif options == 2: # info
        surf.blit(menu[options], (0,0))
        
    if options > 0 and p_mouse[0] > 729 and p_mouse[1] < 60 : # x button
        pg.draw.circle(surf,(0,0,0),(768,31), 30)
        if click:
            options = 0
        surf.blit(menu[options], (0,0))
                
    #draw cursor
    pg.draw.polygon(surf, (200, 50, 50), ((p_mouse), (p_mouse[0]+20, p_mouse[1]+22), (p_mouse[0], p_mouse[1]+30)))
    
    return surf, pause, options, running, newgame, adjust_res, m_vol, sfx_vol, story

def adjust_resolution(hres=210):
    hres = (hres//4)*4
    hres = max(min(hres, 800), 80) # limit range from 80x60 to 800x600
    halfvres = int(hres*0.375/4)*4 #vertical resolution/2
    mod = hres/60 #scaling factor (60° fov)
    frame = np.random.randint(0,255, (hres, halfvres*2, 3))
    frame_half = np.random.randint(0,255, (hres//2, halfvres*2//2, 3))
    
    return hres, halfvres, mod, frame, frame_half

def set_volume(m_vol, sfx_vol, sounds):
    for key in sounds.keys():
        sounds[key].set_volume(sfx_vol)
    sounds['music0'].set_volume(m_vol)
    sounds['music1'].set_volume(m_vol)

async def splash_screen(msg, splash, clock, font, screen):
    running = 1
    clickdelay = 0
    while running:
        clickdelay += 1
        clock.tick(60)
        surf = splash.copy()
        ticks = pg.time.get_ticks()/200
        surf.blit(font.render(msg, 1, (0, 0, 0)), (50, 450+5*np.sin(ticks-1)))
        surf.blit(font.render(msg, 1, (255, 255, 255)), (52, 450+5*np.sin(ticks)))

        p_mouse = pg.mouse.get_pos()
        pg.draw.polygon(surf, (200, 50, 50), ((p_mouse), (p_mouse[0]+20, p_mouse[1]+22), (p_mouse[0], p_mouse[1]+30)))

        screen.blit(surf, (0,0))
        pg.display.update()

        for event in pg.event.get():
            if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN and clickdelay > 50:
                return
            elif event.type == pg.QUIT:
                pg.quit()
        if clickdelay == 180:
            msg = "Press any key..."
        await asyncio.sleep(0)

def load_textures(textures):
    sky1 = pg.image.load('Assets/Textures/skybox'+str(textures[0])+'.jpg').convert()
    sky = pg.surface.Surface((sky1.get_size()[0]*2, sky1.get_size()[1]))
    sky.blit(sky1, (0,0))
    sky.blit(sky1, (sky1.get_size()[0],0))
    floor = pg.image.load('Assets/Textures/floor'+str(textures[1])+'.jpg').convert()
    wall = pg.image.load('Assets/Textures/wall'+str(textures[2])+'.jpg').convert()
    bwall = pg.transform.smoothscale(pg.image.load('Assets/Textures/wall'+str(textures[2])+'.jpg'), (25,25)).convert()
    bwall = pg.transform.smoothscale(bwall, (100,100)).convert()
    door = pg.image.load('Assets/Textures/door'+str(textures[3])+'.jpg').convert()
    window = pg.image.load('Assets/Textures/window'+str(textures[4])+'.jpg').convert()
    size = wall.get_size()
    if textures[0]%3 > 0: # darker at night
        tint = pygame.Surface(size)
        tint.fill('#000000')
        tint.set_alpha(150)
        floor.blit(tint,(0,0))
        wall.blit(tint,(0,0))
        bwall.blit(tint,(0,0))
        door.blit(tint,(0,0))
        window.blit(tint,(0,0))

    full_wall = pygame.Surface((size[0]*3, size[1]*3))
    for i in range(3):
        for j in range(3):
            full_wall.blit(wall, (size[0]*i,size[1]*j))
    full_window = full_wall.copy()
    full_window.blit(window, size)
    full_door = full_wall.copy()
    full_door.blit(door, size)
    full_door.blit(door, (size[0],size[1]*2))
    textures_list = [full_wall, full_door, full_window]
    floor = pg.surfarray.array3d(floor)

    return sky, floor, textures_list
    

if __name__ == '__main__':
    pg.mixer.init()
    asyncio.run(main())
    pg.mixer.fadeout(1000)
    pg.time.wait(1000)
    pg.quit()