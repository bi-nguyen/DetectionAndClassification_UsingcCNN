import sys
# pip install pyqt5
from PyQt5.QtWidgets import QApplication, QMainWindow
from Yolov5 import Ui_MainWindow
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal,Qt
import numpy as np
import cv2 as cv
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
from time import time
import torch
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self)
        self.thread = {}
        self.uic.Button_start.clicked.connect(self.start_screen)
        self.uic.Button_stop.clicked.connect(self.stop_screen)
    def closeEvent(self, event):
        print("yub")
        if len(self.thread) != 0 :
            self.stop_screen()
    def start_screen(self):
        self.thread[1] = ThreadPlus(index = 1)
        self.thread[1].start()
        self.thread[1].signal.connect(self.show_webcam)
    def stop_screen(self):
        self.thread[1].stop()
    def show_webcam(self,cv_img):
        img = self.convert_cv2qt(cv_img)
        self.uic.label.setPixmap(img)
    def convert_cv2qt(self,cv_img):
        img = cv.cvtColor(cv_img,cv.COLOR_BGR2RGB)
        h,w,nc = img.shape
        bytes_per_line = nc * w
        convert_to_Qt_format = QtGui.QImage(img.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(800, 600, Qt.KeepAspectRatio) #giữ tỉ lệ khung hình tránh bị rã
        return QPixmap.fromImage(p)        


class ThreadPlus(QtCore.QThread):
    signal = pyqtSignal(np.ndarray)
    def __init__(self,index=None):
        super(ThreadPlus,self).__init__()
        self.index = index
        self.device = None
        self.out_file = None
        self.classes = None
        self.model = None
        self.gg = True
        self.player = None
        self.index = index
        print("start threading", self.index)
    def run(self):
        if self.index:
            self.model = self.load_model()  # load model
            self.classes = self.model.names
            self.out_file = "Labeled_Video.avi"
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(self.device)
            self.run_program()
    def get_video_from_url(self):
        """
        Creates a new video streaming object to extract video frame by frame to make prediction on.
        :return: opencv2 video capture object, with lowest quality frame available for video.
        """
        return cv.VideoCapture("D:\\git\\VideoDN30s.mp4")  # "D:/8.Record video/movie.mp4"

    def load_model(self):
        """
        Loads Yolo5 model from pytorch hub.
        :return: Trained Pytorch model.
        """
        #model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt')
        #model = torch.hub.load('./CarDetection', 'custom','.\\best.pt',source='local') 
        return model

    def score_frame(self, frame):
        """
        Takes a single frame as input, and scores the frame using yolo5 model.
        :param frame: input frame in numpy/list/tuple format.
        :return: Labels and Coordinates of objects detected by model in the frame.
        """
        
        self.model.to(self.device)
        frame = [frame]
        results = self.model(frame)
        labels, cord = results.xyxyn[0][:, -1].cpu().numpy(), results.xyxyn[0][:, :-1].cpu().numpy()
        
        return labels, cord

    def class_to_label(self, x):
        """
        For a given label value, return corresponding string label.
        :param x: numeric label
        :return: corresponding string label
        """
        
        return self.classes[int(x)]

    def plot_boxes(self, results, frame):
        """
        Takes a frame and its results as input, and plots the bounding boxes and label on to the frame.
        :param results: contains labels and coordinates predicted by model on the given frame.
        :param frame: Frame which has been scored.
        :return: Frame with bounding boxes and labels ploted on it.
        """
        print("yes3")
        labels, cord = results
        n = len(labels)
        x_shape, y_shape = frame.shape[1], frame.shape[0]
        print(x_shape)
        for i in range(n):
            row = cord[i]
            print("ddd", round(cord[i][4], 2))
            if row[4] >= 0.2:
                x1, y1, x2, y2 = int(row[0] * x_shape), int(row[1] * y_shape), int(row[2] * x_shape), int(row[3] * y_shape)
                bgr = (0, 255, 0)
                cv.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)
                cv.putText(frame, self.class_to_label(labels[i]) + " " + str(round(row[4], 2)), (x1, y1), cv.FONT_HERSHEY_SIMPLEX, 0.9, bgr, 2)

        return frame

    def run_program(self):
        """
        This function is called when class is executed, it runs the loop to read the video frame by frame,
        and write the output into a new file.
        :return: void
        """
        self.player = self.get_video_from_url()
        assert self.player.isOpened()
        x_shape = int(self.player.get(cv.CAP_PROP_FRAME_WIDTH))
        y_shape = int(self.player.get(cv.CAP_PROP_FRAME_HEIGHT))
        four_cc = cv.VideoWriter_fourcc(*"MJPG")
        out = cv.VideoWriter(self.out_file, four_cc, 20, (x_shape, y_shape))
        
        while True:
            start_time = time()
            ret, frame = self.player.read()
            assert ret
            results = self.score_frame(frame)
            frame = self.plot_boxes(results, frame)
            end_time = time()
            fps = 1 / (np.round(end_time - start_time, 3))
            print(f"Frames Per Second : {round(fps,2)} FPS")
            # out.write(frame)
            self.signal.emit(frame)
            if not self.gg:
                print("stop capture video")
                break  
    def stop(self):
        print("stop threading", self.index)
        # self.player.release()
        # cv.destroyAllWindows()
        self.terminate()

    def pause_stream(self):
        self.gg = False







if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())