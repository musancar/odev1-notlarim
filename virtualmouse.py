import cv2
import numpy as np
import hand as htm
import time
import autopy
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import pyautogui as pg



#################################
wCam, hCam = 640, 480    #burda kameranın boyutunu ayaraladık
frameR = 150  # FRAME REDUCTİON
smoothening = 7
#################################

pTime = 0
cloclX, clockY = 0, 0
plockX, plockY = 0, 0

cap = cv2.VideoCapture(0)
cap.set(3,wCam)
cap.set(4, hCam)

detector = htm.handDetector(detectionCon=0.7, maxHands=1)

################################################## #####
######### just mouse
wScr, hScr = autopy.screen.size()   # ekran boyutunu verir benimki 1536.0 864.0    videoda 1920 1080 ona göre hesapla

#########################################################
################################################## #####
######### just volume
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
# volume.GetMute()
# volume.GetMasterVolumeLevel()
volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0
area = 0
colorVol = (255, 0, 0)

#########################################################



while True:
    success, img = cap.read()

    # Find Hand
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img, draw=True)
    if len(lmList) !=0:

        #Filter based on size
        area = (bbox[2]-bbox[0])* (bbox[3]-bbox[1]) // 100
        #print(area)
        if 300 <area < 700: # burda elin yakınlık ayarını yaptık


            # Find distance between index  and thumb
            length, img, lineInfo = detector.findDistance(4, 8, img)
            #print(length)


            #convert volume
            volBar = np.interp(length, [25, 195], [400, 150])
            volPer = np.interp(length, [25, 195], [0, 100])


            #reduce resolution to make it smoother   burda seviyenin 1 1 değilde 5 5 artmasını sağlayıp küçük titreşimlerde mesafe değişiminde az etkilenmesini sağladık
            smoothness = 10
            volPer = smoothness * round(volPer / smoothness)

            #check fingers up
            fingers = detector.fingersUp()

            #print(fingers)

            #if pinky is down set volume
            if not fingers[4]:
                volume.SetMasterVolumeLevelScalar(volPer/100, None)
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, ( 0, 255, 0), cv2.FILLED)
                colorVol = (0, 255, 0)
                #time.sleep(0.25) eğer biraz yavaşlatmak duraksatmak istersen kullan
            else:
                colorVol = (255, 0, 0)




    # dravings
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0),3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)
    cVol = int(volume.GetMasterVolumeLevelScalar()*100)
    cv2.putText(img, f'Vol Set: {int(cVol)}', (400, 50), cv2.FONT_HERSHEY_COMPLEX, 1, colorVol, 3)


    #2. get the tip of index and middle fingers
    if len(lmList) !=0:
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

        #3. check which fingers up
        fingers = detector.fingersUp()

        cv2.rectangle(img, (frameR, frameR), (wCam-frameR, hCam-frameR), (255, 0, 255), 2)

        #4. only Index finger : moving mode
        if fingers[1]==1 and fingers[2]==0:

            #5. convert coordinates

            x3 = np.interp(x1, (frameR,wCam-frameR), (0, wScr))
            y3 = np.interp(y1, (frameR,hCam-frameR), (0, hScr))

            #6. smoothen values
            clockX = plockX + (x3-plockX) / smoothening
            clockY = plockY + (y3-plockY) / smoothening

            #7. move mouse
            autopy.mouse.move(wScr-clockX, clockY)
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plockX, plockY = clockX, clockY

        #8. both index and middle fingers up: clicking mode
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            # 9. find distance between fingers
            length, img, lineInfo = detector.findDistance(8, 12, img)
            #print(length)

            # 10. click mouse if distance short
            if length <30:

                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.click()
                #autopy.mouse.click()

                # Sağ butona bas.


######################################################

            if length > 80:

                pg.click(button='right')
#########################################################

        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4]== 0:
            pg.mouseDown(button='left')#Farenin sol butonuna bas



        if fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4]== 1:
            pg.mouseUp(button='left')#Farenin sol butonundan çek

        #pg.KEYBOARD_KEYS

    """
    # frame rate
    cTime = time.time()
    fps = 1/(cTime-pTime)
    pTime = cTime

    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)
     """

    cv2.imshow("Img",img)
    cv2.waitKey(1)  #*****************burda 1 ms lik gecikme verir  HATA VERİNCE ARTTIR