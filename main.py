import cv2
import os
import pickle
import face_recognition
import numpy as np
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': "",
    'storageBucket': ""
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 680)  # Width
cap.set(4, 480)  # Height

imgBackground = cv2.imread('resources/12.png')

# Import mode images in list
folderModePath = 'resources/mode'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Import the encode file
file = open('EncodeFile.p', 'rb')  # rb=reading
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studIDs = encodeListKnownWithIds
print(studIDs)
print("Encode File Loaded")

modeType = 0
counter = 0
id = -1
imgStudent = []

while True:
    success, img = cap.read()

    # Resize for faster processing
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[193:193 + 480, 149:149 + 640] = img
    imgBackground[145:145 + 579, 970:970 + 329] = imgModeList[modeType]

    if faceCurFrame:
        # Process faces
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDist = face_recognition.face_distance(encodeListKnown, encodeFace)
            #print("FaceDist", faceDist)
            #print("Matches", matches)

            matchIndex = np.argmin(faceDist)

            if matches[matchIndex]:
                #print("known face detected ")
                #print(studIDs[matchIndex])
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 155 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studIDs[matchIndex]
                if counter == 0:
                    counter = 1
                    modeType = 1

        if counter != 0:

            if counter == 1:
                studentInfo = db.reference(f'Students/{id}').get()
                print(studentInfo)

                #get img from storage
                blob = bucket.get_blob(f'images/{id}.png')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                #update data
                datetimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                                                   "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                print(secondsElapsed)

                if secondsElapsed > 30:
                    ref = db.reference(f'Students/{id}')
                    studentInfo['total_attendance'] += 1
                    ref.child('total_attendance').set(studentInfo['total_attendance'])
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    modeType = 3
                    counter = 0
                    imgBackground[145:145 + 579, 970:970 + 329] = imgModeList[modeType]

            if modeType != 3:

                if 10 < counter < 20:
                    modeType = 2

                imgBackground[145:145 + 579, 970:970 + 329] = imgModeList[modeType]

                if counter <= 10:
                    cv2.putText(imgBackground, str(studentInfo['total_attendance']), (1190, 190),
                                cv2.FONT_HERSHEY_TRIPLEX, 0.7, (255, 255, 255), 1)

                    cv2.putText(imgBackground, str(studentInfo['major']), (1137, 603),
                                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (255, 255, 255), 1)

                    cv2.putText(imgBackground, str(id), (1090, 546),
                                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (255, 255, 255), 1)

                    cv2.putText(imgBackground, str(studentInfo['standing']), (1060, 665),
                                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (100, 100, 100), 1)

                    cv2.putText(imgBackground, str(studentInfo['year']), (1150, 665),
                                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (100, 100, 100), 1)

                    cv2.putText(imgBackground, str(studentInfo['starting_year']), (1243, 666),
                                cv2.FONT_HERSHEY_TRIPLEX, 0.6, (100, 100, 100), 1)

                    cv2.putText(imgBackground, str(studentInfo['name']), (1022, 498),
                                cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 0, 0), 2)

                    imgBackground[230:230 + 216, 1026:1026 + 216] = imgStudent

                counter += 1

                if counter >= 20:
                    counter = 0
                    modeType = 0
                    studentInfo = []
                    imgStudent = []
                    imgBackground[145:145 + 579, 970:970 + 329] = imgModeList[modeType]

    else:
        modeType = 0
        counter = 0

    cv2.imshow("Face Attendance", imgBackground)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
