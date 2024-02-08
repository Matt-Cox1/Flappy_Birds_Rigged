import cv2

class WebcamHandler:
    def __init__(self, resolution=(640, 480)):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise IOError("Cannot open webcam")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if self.face_cascade.empty():
            raise IOError("Failed to load Haar Cascade for face detection")

    def track_face(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            cv2.imshow('Face Tracking', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop_camera()
        cv2.destroyAllWindows()

    def stop_camera(self):
        if self.cap:
            self.cap.release()

    def __del__(self):
        self.stop_camera()

if __name__ == "__main__":
    webcam = WebcamHandler()
    webcam.track_face()
