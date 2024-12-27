#Sigma光機ステージコントローラー Shot-シリーズ用の測定プログラムを構築、.txtに出力する
#直動ステージ2軸まで
#1軸がx, 2軸がy

#! 3軸ステージに対応するため改造を行う　2024/07/17
#! 対応完了　　　　　　　　　　　　　　 2024/07/18

#動作としては  水平面XYを測定 Zを

import os
import sys
import time
import serial
from serial.tools import list_ports

""" ========================================"""
#押す(True) or 引く(False)（モーター側が引く）
X_moveDirection_PushTrue = True
Y_moveDirection_PushTrue = True
Z_moveDirection_PushTrue = True
#それぞれステージコントローラーの1, 2, 3 Axisに対応

#測定を開始する位置 動作方向の端から
start_x = 2.00   #mm （MAX ステージ長さ）（MIN 0 mm）
start_y = 150.00   #mm
start_z = 0.00   #mm

#測定長さ 押引 どちらも正
x = int((41000 - 0)/100)   #mm  start_xから   ステージの動作範囲に注意!
y = int((42800 - 15000)/100)   #mm  start_yから
z = int((80000 - 0)/1000)   #mm  start_zから

#測定間隔
gridInterval = 10  #mm

#出力ファイル
FileName = os.path.dirname(__file__) + "/" + "1213_MagicBoxB_schedule.txt"
#FileName = os.path.dirname(__file__) + "/" + "sample/" + str(int(time.time())) + "_" + "" + ".txt"

"""========================================="""
#ステージの移動量 1mmあたりのPulse
PulseRate = [100,100,1000,1000] #axis 1,2,3,4 pls/1mm
#OS(MS)33 100pls/mm
#SGSP20  1000pls/mm


X_PULSE_LIMIT = [-1000, 50000]
Y_PULSE_LIMIT = [0, 50000]
Z_PULSE_LIMIT = [0, 150000]

#OS(MS)33-500   -1000 ~ 49000


map = []
position = []
origin = (0,0)  #stageの機械的原点

writecount =0

#指定した条件をもとに格子点を作製
def makeMap(x, y, z, gridInterval):
    xposition, yposition, zposition = 0, 0, 0

    xcount = 1 + (abs(x / gridInterval))
    ycount = 1 + (abs(y / gridInterval))
    zcount = 1 + (abs(z / gridInterval))

    xmod =  x % gridInterval
    ymod =  y % gridInterval
    zmod =  z % gridInterval
    
    X_gridInterval = gridInterval
    Y_gridInterval = gridInterval
    Z_gridInterval = gridInterval

    if not X_moveDirection_PushTrue:
        X_gridInterval = -gridInterval
        xmod = -xmod
        xposition = round((abs(X_PULSE_LIMIT[1]) + abs(X_PULSE_LIMIT[0])) / PulseRate[0])
        
    if not Y_moveDirection_PushTrue:
        Y_gridInterval = -gridInterval
        ymod = -ymod
        yposition = round((abs(Y_PULSE_LIMIT[1]) + abs(Y_PULSE_LIMIT[0])) / PulseRate[1])
        
    if not Z_moveDirection_PushTrue:
        Z_gridInterval = -gridInterval
        zmod = -zmod
        zposition = round((abs(Z_PULSE_LIMIT[1]) + abs(Z_PULSE_LIMIT[0])) / PulseRate[2])
    print(xcount, ycount, zcount, xmod, ymod, zmod)

    iz = -1
    while zcount >= 1:
        iz +=1
        iy =-1
        ybuf = ycount
        while ybuf >= 1:
            iy += 1
            ix =- 1
            xbuf = xcount
            while xbuf >= 1:
                ix += 1
                map.append((xposition+(ix*X_gridInterval), yposition+(iy*Y_gridInterval), zposition+(iz*Z_gridInterval)))
                xbuf -= 1
            else:
                if xbuf > 0:
                    # print("aaaaa")
                    map.append((xposition+(ix*X_gridInterval)+xmod, yposition+(iy*Y_gridInterval), zposition+(iz*Z_gridInterval)))

            ybuf -= 1
        else:
            if ybuf > 0:
                ix=-1
                xbuf = xcount
                while not xbuf < 1:
                    ix += 1
                    map.append((xposition+(ix*X_gridInterval), yposition+(iy*Y_gridInterval)+ymod, zposition+(iz*Z_gridInterval)))
                    xbuf -= 1
                else:
                    if xbuf >0:
                        map.append((xposition+(ix*X_gridInterval)+xmod, yposition+(iy*Y_gridInterval)+ymod, zposition+(iz*Z_gridInterval)))
                        
        zcount -= 1
                        
    else:
        if zcount > 0:
            iy =-1
            ybuf = ycount
            while not ybuf < 1:
                iy += 1
                ix =- 1
                xbuf = xcount
                while not xbuf < 1:
                    ix += 1
                    map.append((xposition+(ix*X_gridInterval), yposition+(iy*Y_gridInterval), zposition+(iz*Z_gridInterval)+zmod))
                    xbuf -= 1
                else:
                    if xbuf > 0:
                        print("aaaaa")
                        map.append(((xposition+(ix*X_gridInterval))+xmod, yposition+(iy*Y_gridInterval), zposition+(iz*Z_gridInterval)+zmod))

                ybuf -= 1
            else:
                if ybuf > 0:
                    ix=-1
                    xbuf = xcount
                    while not xbuf < 1:
                        ix += 1
                        map.append((xposition+(ix*X_gridInterval), yposition+(iy*Y_gridInterval)+ymod, zposition+(iz*Z_gridInterval)+zmod))
                        xbuf -= 1
                    else:
                        if xbuf >0:
                            map.append(((xposition+(ix*X_gridInterval))+xmod, yposition+(iy*Y_gridInterval)+ymod, zposition+(iz*Z_gridInterval)+zmod))


    print(map)


#作製したmapをステージ上の数値に変換
def makePosition(map, startPulsePoint):
    count = 0
    #position.append((0,origin[0], origin[1]))
    for point in map:
        count += 1
        position.append((count, (point[0]*PulseRate[0])+startPulsePoint[0]+X_PULSE_LIMIT[0],
                         (point[1]*PulseRate[1])+startPulsePoint[1]+Y_PULSE_LIMIT[0], 
                         (point[2]*PulseRate[2])+startPulsePoint[2]+Z_PULSE_LIMIT[0]))


#絶対パルス座標移動
def move_schedule_A(position):
    if os.path.exists(FileName):
        replace = False
        try:
            cmdVal = sys.argv[1]
            if cmdVal != "f":
                raise IndexError
            replace = True
        except IndexError:
            print("\"" + FileName + "\" already exists.")
            key = input("Do you want to Replace it?  (y/n)  >> ")
            if (key == "y" or key == "Y"):
                replace = True

        if not replace:
            print("-exit-")
            exit()

    direction = ""
    if X_moveDirection_PushTrue:
        direction = direction + "Push_"
    else:
        direction = direction + "Pull_"
        
    if Y_moveDirection_PushTrue:
        direction = direction + "Push_"
    else:
        direction = direction + "Pull_"
        
    if Z_moveDirection_PushTrue:
        direction = direction + "Push"
    else:
        direction = direction + "Pull"

    f = open(FileName, 'w')
    f.write(time.strftime('%Y/%m/%d %H:%M:%S\n'))
    f.write("X" + str(x) + " Y"  + str(y) + " Z"  + str(z) + " I" +  str(gridInterval) + " T" + str(len(position)) + " -" + direction + " -Absolute" + "\n")
    f.write("-START-\n")

    p_ = (0,0,0,0)
    print("posi len : " ,len(position))
    for p in position:
        p1 = "+P" + str(int(p[1]))
        p2 = "+P" + str(int(p[2]))
        p3 = "+P" + str(int(p[3]))
        
        if p[1] < 0: p1 = "-P" + str(int(abs(p[1])))
        if p[2] < 0: p2 = "-P" + str(int(abs(p[2])))
        if p[3] < 0: p3 = "-P" + str(int(abs(p[3])))

        if p[0] == 1: f.write("A:W" + p1 + p2 + p3 + "+P0\n")

        elif (p[1]-p_[1]==0) + (p[2]-p_[2]==0) + (p[3]-p_[3]==0) ==2:
            if (p[2]-p_[2]==0) and (p[3]-p_[3]==0): f.write("A:1" + p1 + "\n")
            
            elif (p[1]-p_[1]==0) and (p[3]-p_[3]==0): f.write("A:2" + p2 + "\n")
            
            else: f.write("A:3" + p3 + "\n")
            
        else: f.write("A:W" + p1 + p2 + p3 + "+P0\n")

        p_ = (0,p[1],p[2],p[3])

    f.write("-END-\n")

    f.close


#相対パルス座標移動
def move_schedule_M(position):
    if os.path.exists(FileName):
        replace = False
        try:
            cmdVal = sys.argv[1]
            if cmdVal != "f":
                raise IndexError
            replace = True
        except IndexError:
            print("\"" + FileName + "\" already exists.")
            key = input("Do you want to Replace it?  (y/n)  >> ")
            if (key == "y" or key == "Y"):
                replace = True

        if not replace:
            print("-exit-")
            exit()

    
    direction = ""
    if X_moveDirection_PushTrue:
        direction = direction + "Push_"
    else:
        direction = direction + "Pull_"
        
    if Y_moveDirection_PushTrue:
        direction = direction + "Push_"
    else:
        direction = direction + "Pull_"
        
    if Z_moveDirection_PushTrue:
        direction = direction + "Push"
    else:
        direction = direction + "Pull"


    f = open(FileName, 'w')
    f.write(time.strftime('%Y/%m/%d %H:%M:%S\n'))
    f.write("x" + str(x) + " y"  + str(y) + " Z" + str(z) + " I" +  str(gridInterval) + " P" + str(len(position)) + " -" + direction + " -Relative" + "\n")
    
    f.write("-START-\n")

    p_ = (0,0,0,0)

    for p in position:
        p1 = "+P" + str(int(p[1] - p_[1]))
        p2 = "+P" + str(int(p[2] - p_[2]))
        p3 = "+P" + str(int(p[3] - p_[3]))
        
        if (p[1] - p_[1]) <= 0: p1 = "-P" + str(abs(p[1] - p_[1]))
        if (p[2] - p_[2]) <= 0: p2 = "-P" + str(abs(p[2] - p_[2]))
        if (p[3] - p_[3]) <= 0: p3 = "-P" + str(abs(p[3] - p_[3]))

        if p[0] == 1: f.write("M:W" + p1 + p2 + p3 + "+P0\n")

        elif (p[1]-p_[1]==0) + (p[2]-p_[2]==0) + (p[3]-p_[3]==0) ==2:
            if (p[2]-p_[2]==0) and (p[3]-p_[3]==0): f.write("M:1" + p1 + "\n")
            
            elif (p[1]-p_[1]==0) and (p[3]-p_[3]==0): f.write("M:2" + p2 + "\n")
            
            else: f.write("M:3" + p3 + "\n")
            
        else: f.write("M:W" + p1 + p2 + p3 + "+P0\n")
        
        p_ = (0,p[1],p[2],p[3])

    f.write("-END-\n")
    f.close

    print("-Complete-")


"""==========================================================="""


def main():
    makeMap(x,y,z,gridInterval)

    startpoint = (start_x*PulseRate[0],start_y*PulseRate[1], start_z*PulseRate[2])
    makePosition(map,startpoint)
    print(position)
    
    # move_schedule_M(position)
    move_schedule_A(position)

if __name__ == "__main__":
    main()
