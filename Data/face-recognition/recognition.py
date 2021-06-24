import cv2
import os
import numpy as np
import time
import pickle
from PIL import Image

class Recognition():
    def __init__(self):
        self.face_detector = cv2.CascadeClassifier("/usr/local/lib/python3.5/dist-packages/zumi/util/src/haarcascade_frontalface_default.xml")
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.name = None
        self.streaming = True
        self.streaming_image = None
        self.cap = 0
        self.data_path = '/home/pi/Zumi_Content/Data/face-recognition/'

    def makeLabel(self):
        labels = 0
        write = False

        if not os.path.exists(self.data_path + "labels.pickle"):
            with open(self.data_path + 'labels.pickle', 'wb') as labelFile:
                pickle.dump({}, labelFile, protocol=pickle.HIGHEST_PROTOCOL)

        with open(self.data_path + 'labels.pickle', 'rb') as labelFile:
            labels = pickle.load(labelFile)
            names = list(labels.values())

            if not self.name in names and self.name is not None:
                number = len(labels)
                labels[number] = self.name
                write = True

        if write:
            with open(self.data_path + 'labels.pickle', 'wb') as labelFile:
                pickle.dump(labels, labelFile, protocol=pickle.HIGHEST_PROTOCOL)

    def save_image(self, image):
        if not os.path.isdir(self.data_path + 'faces'):
            os.makedirs(self.data_path + 'faces')
        file_name = self.data_path + 'faces/'

        if self.name is not None:
            number = 0
            lists = os.listdir(self.data_path + 'faces')
            for list in lists:
                if self.name in list:
                    number += 1

            file_name = file_name + self.name + '_' + str(number) + '.jpg'
            cv2.imwrite(file_name, image)

    def makeDataset(self, image):
        self.makeLabel()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(gray, 1.2, 5)

        for(x, y, w, h) in faces:
            cv2.rectangle(image, (x,y), (x+w, y+h), (255,255,255), 4)
            face_image = gray[y:y+h, x:x+w]
            self.save_image(face_image)
            self.cap += 1

            cv2.rectangle(gray, (x,y), (x+w, y+h), (255,255,255), 4)

        if self.streaming == True:
            self.streaming_image = cv2.resize(gray, (128, 64))

    def getImagesAndLabels(self, path):
        labels = 0

        with open(self.data_path + 'labels.pickle', 'rb') as labelFile:
            labels = pickle.load(labelFile)

        imagePaths = [os.path.join(path,f) for f in os.listdir(path)]

        faces = []
        ids = []

        for imagePath in imagePaths:
            PIL_img = Image.open(imagePath).convert('L')
            img_numpy = np.array(PIL_img, 'uint8')

            name = os.path.split(imagePath)[-1].split('_')[0]
            id = -1
            for label in labels:
                if labels[label] == name:
                    id = label

            faces.append(img_numpy)
            ids.append(id)

        return faces, ids


    def trainModel(self):
        faces, ids = self.getImagesAndLabels(self.data_path + 'faces')
        self.recognizer.train(faces, np.array(ids))
        if not os.path.isdir(self.data_path + 'trainer'):
            os.makedirs(self.data_path + 'trainer')
        self.recognizer.save(self.data_path + 'trainer/trainer.yml')

    def recognition(self, image):
        labels = 0

        with open(self.data_path + 'labels.pickle', 'rb') as labelFile:
            labels = pickle.load(labelFile)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(gray, 1.2, 5)

        for(x, y, w, h) in faces:
            cv2.rectangle(image, (x,y), (x+w, y+h), (255,255,255), 4)
            Id = self.recognizer.predict(gray[y:y+h, x:x+w])
            name = labels[Id[0]]
            cv2.putText(image, name, (x, y-5), self.font, 1, (255,255,255), 3)
            print(name)

            cv2.rectangle(gray, (x,y), (x+w, y+h), (255,255,255), 4)
            cv2.putText(gray, name, (x, y-5), self.font, 0.5, (255,255,255), 3)

        if self.streaming == True:
            self.streaming_image = cv2.resize(gray, (128, 64))

    def deleteDataset(self, name):
        imagePaths = [os.path.join(self.data_path + 'faces',f) for f in os.listdir(self.data_path + '/faces')]
        for imagePath in imagePaths:
            imgName = os.path.split(imagePath)[-1].split('_')[0]
            if imgName == name:
                os.remove(imagePath)
        labels = 0
        with open(self.data_path + 'labels.pickle', 'rb') as labelFile:
            labels = pickle.load(labelFile)
        for key in labels.keys():
            if labels.get(key) == name:
                del labels[key]
                break
        with open(self.data_path + 'labels.pickle', 'wb') as labelFile:
            pickle.dump(labels, labelFile, protocol=pickle.HIGHEST_PROTOCOL)

        print("Training model...")
        self.trainModel()
        print("Done!")

    def deleteAllDatasets(self):
        path = self.data_path + 'faces'
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        for imagePath in imagePaths:
            os.remove(imagePath)
        os.remove(self.data_path + 'labels.pickle')
        os.remove(self.data_path + 'trainer/trainer.yml')
        