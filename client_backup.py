#-*- coding:utf-8 -*-
import sys
from threading import *
from socket import *
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PIL import Image
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import time, datetime, os, sys, io, shutil, time
from datetime import timedelta
import struct


ABR_IMAGE_HEADER_SIZE = 8
IVU_IMAGE_HEADER_SIZE = 64

class Signal(QObject):
    recv_signal = pyqtSignal(str)
    recv_signalSecond = pyqtSignal(str)
    recv_image = pyqtSignal(str)
    # recv_imageDir = pyqtSignal(str)
    recv_totalCount = pyqtSignal(str)
    recv_passedCount = pyqtSignal(str)
    recv_failedCount = pyqtSignal(str)
    disconn_signal = pyqtSignal()

class ClientSocket:
    def __init__(self, parent):
        self.parent = parent
        self.recv = Signal()
        self.recv.recv_signal.connect(self.parent.updateMsg)
        self.recv.recv_signalSecond.connect(self.parent.updateMsgSecond)

        # self.recv.recv_image.connect(self.parent.updateImg)
        # self.recv.recv_imageDir.connect(self.parent.updateImgDir)
        # self.recv.recv_totalCount.connect(self.parent.totalCount)
        # self.recv.recv_passedCount.connect(self.parent.passedCount)
        # self.recv.recv_failedCount.connect(self.parent.failedCount)

        self.disconn = Signal()
        self.disconn.disconn_signal.connect(self.parent.updateDisconnect)
        self.bConnect = False
        self.imageData = []

    def __del__(self):
        self.stop()

    def connectServer(self, ip, port, cmdPort, cameraName, imgSize, productName, cameraBrand, inspectionSensor, dataPort):
        self.ip = ip
        self.port = port
        self.cmdPort = cmdPort
        self.cameraName = cameraName
        self.imgSize = imgSize
        self.dataPort = dataPort
        self.productName = productName
        self.client = socket(AF_INET, SOCK_STREAM)
        self.cameraBrand = cameraBrand

        self.inspectionSensor = inspectionSensor
        self.inspectionNumber = len(inspectionSensor)

        try:
            self.client.connect( (ip, port) )
        except Exception as e:
            print('Connect Error : ', e)
            return False
        else:
            self.bConnect = True
            self.t = Thread(target=self.receive, args=(self.client,))
            self.t.daemon = True
            self.t.start()
            print('Connected')

        return True

    def stop(self):
        self.bConnect = False
        if hasattr(self, 'client'):
            self.client.close()
            del(self.client)
            print('Client Stop')
            self.disconn.disconn_signal.emit()

    def receive(self, client):
        failedCountBuffer = 0
        failedCountSecondBuffer = 0

        # ivuImageConstSize = 1082998 #77942
        lenghthBuffer = 0

        while self.bConnect:

            folderDir = './' + self.cameraName
            dailyDir = makeDirectory(folderDir)
            productDir = dailyDir + '/' + self.productName
            if not os.path.isdir(productDir):
                os.mkdir(productDir)

            removeDt = datetime.datetime.now() - timedelta(days=60)
            removeFolderDir = folderDir + '/' + removeDt.strftime('%Y-%m')
            deleteDirectory(removeFolderDir)

            if self.cameraBrand == 'Banner':
                try:
                    recv = client.recv(self.imgSize)
                except Exception as e:
                    print('Recv() Error :', e)
                    break
                else:
                    ivuImageTotalSize = self.imgSize
                    lenghthBuffer += len(list(recv))

                    if lenghthBuffer < ivuImageTotalSize :
                        # lenghthBuffer != 1082998(Color), 77942(Black)
                        print("lenghthBuffer", lenghthBuffer)
                        print("ivuImageTotalSize", ivuImageTotalSize)
                        self.imageData.append(recv)

                    else :
                        print("lenghthBuffer", lenghthBuffer)
                        print("ivuImageTotalSize", ivuImageTotalSize)
                        self.imageData.append(recv)


                        # print("Done! length!", lenghthBuffer)
                        lenghthBuffer = 0
                        imageDataAll = b''.join(self.imageData)
                        print("len imageDataAll", len(imageDataAll))
                        print("imageDataAll", imageDataAll[IVU_IMAGE_HEADER_SIZE:IVU_IMAGE_HEADER_SIZE+40])

                        now = datetime.datetime.now()
                        try :
                            image = Image.open(io.BytesIO(imageDataAll[IVU_IMAGE_HEADER_SIZE:]))
                        except :
                            print("Image open err!")
                            lenghthBuffer = 0
                        else:
                            print("Image open ok")

                            if self.inspectionNumber == 1 :
                                totalCount = countSocket(self.ip, self.cmdPort, self.cameraName, 'total')
                                passedCount = countSocket(self.ip, self.cmdPort, self.cameraName, 'passed')
                                failedCount = countSocket(self.ip, self.cmdPort, self.cameraName, 'failed')
                                if failedCountBuffer != int(failedCount.split('/')[0]):
                                    failedCountBuffer = int(failedCount.split('/')[0])
                                    imageSaveDir = productDir + '/' + str(now.strftime("%H-%M-%S-%f")) +'.bmp'
                                else :
                                    imageSaveDir = dailyDir + '/temp.bmp'
                                image.save(imageSaveDir)
                                image.close()
                                msg = totalCount.split('/')[0] + ',' + passedCount.split('/')[0] + ',' + failedCount.split('/')[0]
                                self.recv.recv_signal.emit(msg)

                            else:
                                totalCount = countSocket(self.ip, self.cmdPort, self.cameraName, 'total', self.inspectionSensor[0])
                                passedCount = countSocket(self.ip, self.cmdPort, self.cameraName, 'passed', self.inspectionSensor[0])
                                failedCount = countSocket(self.ip, self.cmdPort, self.cameraName, 'failed', self.inspectionSensor[0])

                                totalCountSecond = countSocket(self.ip, self.cmdPort, self.cameraName, 'total', self.inspectionSensor[1])
                                passedCountSecond = countSocket(self.ip, self.cmdPort, self.cameraName, 'passed', self.inspectionSensor[1])
                                failedCountSecond = countSocket(self.ip, self.cmdPort, self.cameraName, 'failed', self.inspectionSensor[1])

                                if failedCountBuffer != int(failedCount.split('/')[0])\
                                        or failedCountSecondBuffer != int(failedCountSecond.split('/')[0]):
                                    failedCountBuffer = int(failedCount.split('/')[0])
                                    failedCountSecondBuffer = int(failedCountSecond.split('/')[0])

                                    imageSaveDir = productDir + '/' + str(now.strftime("%H-%M-%S-%f")) +'.bmp'
                                else :
                                    imageSaveDir = dailyDir + '/temp.bmp'
                                image.save(imageSaveDir)
                                image.close()
                                msg = totalCount.split('/')[0] + ',' + passedCount.split('/')[0] + ',' + failedCount.split('/')[0]
                                self.recv.recv_signal.emit(msg)
                                msgSecond = totalCountSecond.split('/')[0] + ',' + passedCountSecond.split('/')[0] + ',' + failedCountSecond.split('/')[0]
                                self.recv.recv_signalSecond.emit(msgSecond)
                        finally:
                            self.imageData = []
            else:
                try:
                    recv = client.recv(255)
                except Exception as e:
                    print('Recv() Error :', e)
                    break
                else:
                    msg = str(recv, encoding='utf-8')
                    if msg:
                        self.recv.recv_signal.emit(msg)
                        parentPath = os.path.abspath(os.path.join(os.path.dirname(__file__)))
                        print(parentPath)
                        imageTempDir = os.path.join(parentPath, 'imageTemp')
                        time.sleep(1)

                        try:
                            tempImagefileNames = os.listdir(imageTempDir)
                            print(tempImagefileNames)
                            print('here')

                            FileFormat = tempImagefileNames[0].split('.')[-1]
                        except:
                            imageTempFileDir = 'noFile'
                        else:
                            if FileFormat == 'bmp':
                                imageTempFileDir = os.path.join(imageTempDir, tempImagefileNames[0])
                                print(imageTempFileDir)
                            else:
                                imageTempFileDir = 'noImg'
                        finally:

                            if imageTempFileDir == 'noFile':
                                print("카메라에서 저장된 파일이 없습니다.")
                            elif imageTempFileDir == 'noImg':
                                print("해당폴더의 저장된 파일의 형식이 bmp 가 아닙니다.")
                                os.remove(imageTempFileDir)
                            else:
                                oldName = imageTempFileDir
                                now = datetime.datetime.now()
                                imageSaveDir = productDir + '/' + str(now.strftime("%H-%M-%S-%f")) + '.bmp'
                                # print(imageSaveDir)
                                try:
                                    os.rename(oldName, imageSaveDir)
                                except:
                                    print('image saving error')
                                else:
                                    print('image saving scss')

        self.stop()
        print("stop")

    def send(self, msg):
        if not self.bConnect:
            return
        try:
            self.client.send(msg.encode())
        except Exception as e:
            print('Send() Error : ', e)
        else:
            print('Success to send message')


def deleteDirectory(folderDir):
    if os.path.isdir(folderDir):
        shutil.rmtree(folderDir)

def makeDirectory(folderDir):
    if not os.path.isdir(folderDir):
        os.mkdir(folderDir)
    dt = datetime.datetime.now()
    monthlyDir = folderDir + '/' + dt.strftime('%Y-%m')

    if not os.path.isdir(monthlyDir) :
        os.mkdir(monthlyDir)
    dailyDir = monthlyDir + '/' + dt.strftime('%Y-%m-%d')
    if not os.path.isdir(dailyDir) :
        os.mkdir(dailyDir)
    return dailyDir

def countSocket(ipAddress, port, cameraName, countMode, inspectionSensor=None):
    if inspectionSensor == None :
        if countMode == 'total':
            getHistory = b'get history totalframes\r\n'
        elif countMode == 'passed':
            getHistory = b'get history passed\r\n'
        elif countMode == 'failed':
            getHistory = b'get history failed\r\n'
    else:
        if countMode == 'total':
            getHistory = ('get history <'+ inspectionSensor + '> ' + 'totalframes\r\n').encode('ascii')
        elif countMode == 'passed':
            getHistory = ('get history <'+ inspectionSensor + '> ' + 'passed\r\n').encode('ascii')
        elif countMode == 'failed':
            getHistory = ('get history <'+ inspectionSensor + '> ' + 'failed\r\n').encode('ascii')

    print(inspectionSensor, getHistory)

    with socket() as s2:
        s2.connect((ipAddress, port))
        s2.sendall(getHistory)
        data = s2.recv(1024)
    print('Received', repr(data))
    count = str(data).split('\\r\\n')[1] +'/' + cameraName
    return count
