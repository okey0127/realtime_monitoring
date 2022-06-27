import cv2
print(1)
cap = cv2.VideoCapture(-1)
print(2)
cap.set(3, 1080)
cap.set(4, 720)


while True:
    ret, frame = cap.read()
    if ret:
        cv2.imshow(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWondows()