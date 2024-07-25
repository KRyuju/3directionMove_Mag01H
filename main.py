
#! 3軸ステージに対応するため改造を行う　2024/07/19

#! 3軸ステージに対応するため改造を行う　2024/07/19

import os
import time
import cv2
import numpy
import serial

# import Image
# import read_image_mag01h
import stage_control

#! スタート前 チェックリスト
"""
0. 全ての機器の電源は入っているか 測定範囲内に障害物は無いか

1. MeasureSetting.pyを回して、測定のスケジュールを作製したか
2. 測定スケジュール, 測定データのファイル名は正しいか
3. 測定回数、開始時の原点出しの有無は正しいか 

fin
"""

#?----------------------------------------
average = 3

#開始,終了時に機械原点を出すか
startCheckOrigin = False
endCheckOrigin = False

save_file = os.path.dirname(__file__) + "/" + "MeasureData/" + str(int(time.time())) + "_" + "" + ".txt"

move_schedule = "./sample/"


#?----------------------------------------


stageParameter = {}
THM1176Parameter = {}

if startCheckOrigin or endCheckOrigin:
    confirm = input(" \"CheckOrigin\" command is enabled. Confirm?  (y/n) >> ")
    if confirm != "y":
        exit()

def setup():
    global stageParameter, THM1176Parameter
    stageParameter = stage_control.setup(move_schedule)
    
    stageParameter.update({"startCheckOrigin":startCheckOrigin})
    stageParameter.update({"endCheckOrigin":endCheckOrigin})

    # Image.Parameter("Parameters")

    print(THM1176Parameter)
    print(stageParameter)

    if os.path.exists(save_file):
        print("\"" + save_file + "\" already exists.")
        key = input("Do you want to Replace it?  (y/n)  >> ")
        if (key == "y" or key == "Y"):
            print("-replace")
        else:
            print("-exit-")
            exit()

    f = open(save_file, "w")
    f.write("#------------------------------------\n")
    f.write(time.strftime('%Y/%m/%d %H:%M:%S') + "  start\n")
    f.write("x, y, z, status, B, Bx, By, Bz   " + str(average) + " Measure/1point\n")
    f.write("Area : " + stageParameter["RouteInfo"]+ " A" + str(average) + "\n")
    f.write("#------------------------------------\n")
    f.close

    print("setup end")


def main():
    LastTime = time.time()

    Window = "Time Display"
    cv2.namedWindow(Window, cv2.WINDOW_NORMAL)
    
    setup()

    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    f = open(save_file, "a")

    ser = ""
    if stageParameter["ControllerStatus"]:
        ser = serial.Serial(stageParameter["ControllerPortName"], 9600)
    
    #ser = serial.Serial("COM11", 9600)
    
    FLAG = "WAIT"

    print("ser start")

    x = int(stageParameter["RouteInfo"].split()[0][1:])
    y = int(stageParameter["RouteInfo"].split()[1][1:])
    z = int(stageParameter["RouteInfo"].split()[2][1:])
    interval = [int(stageParameter["RouteInfo"].split()[3][1:])] * 3
    mode = (stageParameter["RouteInfo"].split()[5][1:]).split("_")
    x_now = 0
    y_now = 0
    z_now = 0

    if mode[0] == "Pull": interval[0] = -interval[0]
    if mode[1] == "Pull": interval[1] = -interval[1]
    if mode[2] == "Pull": interval[2] = -interval[2]


    print(x,y,z)

    move_step = 0
    measureCount = 0

    start_time = time.time()
    while True:
        elaps_time = time.time() - start_time

        if (elaps_time) < 0.1: continue  #loopTime  PC負荷対策

        current = "now  " + f'{round((elaps_time//3600)):03}' + " : " + f'{round(((elaps_time%3600)//60)):02}' + " : " + f'{round(elaps_time%60):02}'

        eta_time = (elaps_time * ((len(stageParameter["RouteMap"])-move_step)/(move_step+0.00001)))
        ETA = "ETA   " + f'{round((eta_time//3600)):03}' + " : " + f'{round(((eta_time%3600)//60)):02}' + " : " + f'{round(eta_time%60):02}'

        img = 255 * (numpy.ones((100, 350, 3), dtype=numpy.uint8))
        cv2.putText(img, current, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)
        cv2.putText(img, ETA, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

        cv2.imshow("Time Display", img)

        if cv2.waitKey(1) & 0xFF == ord('q'): # Q key長押しで強制終了
            print("exit")
            time.sleep(2)
            break

        if FLAG == "MOVE":
            if not stage_control.move(ser, stageParameter["RouteMap"], move_step, (stageParameter["startCheckOrigin"],stageParameter["endCheckOrigin"])):
                break

            print("x"+ str(x_now), "y"+str(y_now))

            move_step +=1
            FLAG = "WAIT"

            if x_now == x:
                x_now = 0
                y_now += interval[1]
                continue

            if move_step >= 3:

                x_now += interval[0]
            
                if x_now > x:
                    x_now = x

        elif FLAG == "WAIT":
            # print("wait")
            if stage_control.wait(ser):
                FLAG = "MEASURE"

        elif FLAG == "MEASURE":
            if move_step <= 1:
                FLAG = "MOVE"
                continue

            if measureCount == 0:
                f = open(save_file, "a")

            #! Mag_data = THM1176.read_THM1176(THM1176Parameter)

            # result = pyTHM1176.measure_one(pyTHM1176.probe()).split()
            # result = pyTHM1176.measure_Average(pyTHM1176.probe(), 10).split()

            ret, img = cap.read()

            cv2.imshow("cadhf", img)

            # Mag_data = read_image_mag01h.read_Mag01H(img, (x_now, y_now, measureCount))
            time.sleep(1)

            # print("res", result)

            # Mag_data = ["True", result[8], result[2], result[4], result[6]]

            Mag_data = [True, 222.22, 222.29, 222.29, 222.29]


            # Mag_data = 0

            if Mag_data[0]:
                print(str(measureCount+1) + "/" + str(average), Mag_data, end="\n\n")

                Mag_data[0:0] = (x_now, y_now, 0)

                for i in range(len(Mag_data)):
                    if i != 0: f.write(",")
                    f.write(str(Mag_data[i]))
                    
                f.write("\n")

                measureCount += 1

            if measureCount >= average and stage_control.wait(ser):
                measureCount = 0
                f.close()
                FLAG = "MOVE"

            
    

        LastTime = time.time()

    with open(save_file, mode="r+") as f:
        l = f.readlines()

    l.insert(2,time.strftime('%Y/%m/%d %H:%M:%S') + "  end\n")

    with open(save_file, mode='w') as f:
        f.writelines(l)


if __name__ == "__main__":
    main()