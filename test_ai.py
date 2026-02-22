from deepface import DeepFace
import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    try:
        # Try detecting a face
        result = DeepFace.extract_faces(frame, detector_backend='opencv', enforce_detection=False)

        if len(result) > 0:
            x = result[0]['facial_area']['x']
            y = result[0]['facial_area']['y']
            w = result[0]['facial_area']['w']
            h = result[0]['facial_area']['h']

            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    except:
        pass

    cv2.imshow("AI Face Test", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
