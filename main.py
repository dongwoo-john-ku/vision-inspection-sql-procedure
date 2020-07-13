#-*- coding:utf-8 -*-
import sys
from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate

import client
import socket, datetime, threading, os, csv
import pandas as pd
from socket import *
import pymssql
from threading import Event
exit = Event()
import logging.handlers

if not os.path.isdir('./log'):
    os.mkdir('./log')

log_max_size = 1 * 1024 * 1024
log_file_count = 20

infoLog = logging.getLogger('infoLog')
infoLog.setLevel(logging.INFO)
infoFormatter = logging.Formatter('[%(levelname)s] %(asctime)s : (%(filename)s:%(lineno)d) > %(message)s')
infoFileHandler = logging.handlers.RotatingFileHandler(filename='./log/info.txt', maxBytes=log_max_size, backupCount=log_file_count)

infoFileHandler.setFormatter(infoFormatter)
infoLog.addHandler(infoFileHandler)

resultLog = logging.getLogger('resultLog')
resultLog.setLevel(logging.INFO)
resultFormatter = logging.Formatter('[%(levelname)s]:  %(asctime)s : %(message)s')
resultFileHandler = logging.handlers.RotatingFileHandler(filename='./log/result.txt', maxBytes=log_max_size, backupCount=log_file_count)
resultFileHandler.setFormatter(resultFormatter)
resultLog.addHandler(resultFileHandler)

form_class = uic.loadUiType("main_single.ui")[0]
class myWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.c = client.ClientSocket(self)

        self.setupUi(self)
        self.pushButton.clicked.connect(self.connectClicked)
        self.pushButton_4.clicked.connect(self.historyClear)
        self.pushButton_7.clicked.connect(self.openSelectedDir)


        global stop
        stop = False
        self.btnClicked = False
        self.pushButton_3.clicked.connect(self.commandClicked)


        self.label_2.setStyleSheet("background-color: #CCCCCC;"
                                   "border-radius: 3px;"                   
                                   "color: blue;"
                                   "border-style: solid;"
                                   "border-width: 2px;"
                                   "border-color: #999999")
        self.label_5.setStyleSheet("background-color: #CCCCCC;"
                                   "border-radius: 3px;"
                                   "color: blue;"
                                   "border-style: solid;"
                                   "border-width: 2px;"
                                   "border-color: #999999")

        self.dateEdit.setDate(QDate.currentDate())
        self.dateEdit.setMaximumDate(QDate.currentDate())

        dt = datetime.datetime.now()
        self.dateEdit.setMinimumDate(QDate(dt.year, dt.month-1, dt.day))

        self.label_3.setStyleSheet("color: red;"
                            "background-color: #FFCCCC")

        self.label_19.setStyleSheet("color: red;"
                            "background-color: #FFCCCC")

        self.cameraNameList = ['ivuImage', 'v20cImage']
        self.makeDirectory(self.cameraNameList[0])
        self.makeDirectory(self.cameraNameList[1])

        self.actionNetwork.triggered.connect(self.networkConnected)
        self.actionDatabase.triggered.connect(self.dbSettingConnected)

        self.settingValueList = readEthernetSettingValue()
        self.cameraBrand = self.settingValueList[0][4]
        self.label_33.setText(self.cameraBrand)

        script_dir = os.path.dirname(__file__)
        productInfo = 'setting/productInfoReference.xlsx'
        productInfoAbs = os.path.join(script_dir, productInfo)
        self.df_productInfo = pd.read_excel(productInfoAbs, header = 0)
        self.productsList = []
        self.codeList = []
        self.standardList = []
        self.volumeList = []

        for i in range(len(self.df_productInfo)):
            self.codeList.append(self.df_productInfo[self.df_productInfo.columns[0]][i])
            self.productsList.append(self.df_productInfo[self.df_productInfo.columns[1]][i])
            self.standardList.append(self.df_productInfo[self.df_productInfo.columns[2]][i])
            self.volumeList.append(self.df_productInfo[self.df_productInfo.columns[3]][i])

        self.comboBox.setEditable(True)
        self.comboBox.lineEdit().setAlignment(QtCore.Qt.AlignHCenter)
        self.comboBox.addItems(self.productsList)
        self.comboBox.currentIndexChanged.connect(self.selectionchange)

        self.label_12.setText(str((self.codeList[self.comboBox.currentIndex()])))
        self.label_14.setText(str((self.standardList[self.comboBox.currentIndex()])))
        self.label_15.setText(str((self.volumeList[self.comboBox.currentIndex()])))

        tagInfo = 'setting/tagInfoReference.xlsx'
        tagInfoAbs = os.path.join(script_dir, tagInfo)
        self.df_tagInfo = pd.read_excel(tagInfoAbs, header = 0)
        self.inspectionNumber = len(self.df_tagInfo)

        self.label_26.setText(self.df_tagInfo[self.df_tagInfo.columns[1]][0])
        self.label_28.setText(self.df_tagInfo[self.df_tagInfo.columns[0]][0])

        self.inspectionSensor = []

        self.lineEdit.setText(readTimeIntervalValue())
        makeDirectory('imageTemp')

        readResult = readResultHistory()
        historyFirst = readResult[0]


        self.label_23.setText(historyFirst[0])
        self.label_21.setText(historyFirst[1])
        self.label_24.setText(historyFirst[2])

        if self.inspectionNumber > 1 :
            self.label_35.setText(self.df_tagInfo[self.df_tagInfo.columns[1]][1])
            self.label_37.setText(self.df_tagInfo[self.df_tagInfo.columns[0]][1])
            self.label_43.setText(self.df_tagInfo[self.df_tagInfo.columns[1]][0])
            self.label_49.setText(self.df_tagInfo[self.df_tagInfo.columns[1]][1])
            historySecond = readResult[1]
            self.label_31.setText(historySecond[0])
            self.label_39.setText(historySecond[1])
            self.label_41.setText(historySecond[2])

            self.label_40.setText('2')
        else:
            self.label_40.setText('1')


    def commandClicked(self):
        global stop
        if self.btnClicked :
            self.btnClicked = False
            exit.set()

            stop = True
            self.pushButton_3.setText('수집 시작')
            self.label_19.setText('수집 대기')
            self.label_19.setStyleSheet("color: red;"
                                   "background-color: #FFCCCC")

            self.pushButton.setEnabled(True)
            self.pushButton_4.setEnabled(True)
            self.comboBox.setEnabled(True)
            self.lineEdit.setDisabled(False)
            exit.clear()

        else:
            self.pushButton_3.setText('수집 중단')
            self.label_19.setText('수집 중')
            self.label_19.setStyleSheet("color: green;"
                                       "background-color: #7FFFD4")
            self.pushButton.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.comboBox.setEnabled(False)
            self.lineEdit.setDisabled(True)

            stop = False
            self.btnClicked = True

            self.settingValueList = readEthernetSettingValue()
            self.cameraBrand = self.settingValueList[0][4]

            t = MyThread(self.settingValueList[0][0], int(self.settingValueList[0][2]),
                         self.comboBox.currentText(), self.cameraBrand)
            self.label_33.setText(self.cameraBrand)
            try:
                t.daemon = True   # Daemon True is necessary
                t.start()
            except:
                self.label_3.setText('Threading Exception!!!')
                infoLog.info('Threading Exception')
            else:
                writeTimeIntervalValue()
                infoLog.info('Threading Started')

    def selectionchange(self):
        print(self.comboBox.currentText())
        self.label_12.setText(str((self.codeList[self.comboBox.currentIndex()])))
        self.label_14.setText(str((self.standardList[self.comboBox.currentIndex()])))
        self.label_15.setText(str((self.volumeList[self.comboBox.currentIndex()])))


    def __del__(self):
        self.c.stop()

    def connectClicked(self):
        if self.c.bConnect == False:
            self.settingValueList = readEthernetSettingValue()
            self.cameraBrand = self.settingValueList[0][4]

            ip = self.settingValueList[0][0]
            port = int(self.settingValueList[0][1])
            cmdPort = int(self.settingValueList[0][2])
            imgSize = int(self.settingValueList[0][3])
            productName = str((self.codeList[self.comboBox.currentIndex()]))
            cameraBrand = self.settingValueList[0][4]
            self.label_33.setText(self.cameraBrand)
            cameraName = 'image_' + cameraBrand
            dataPort = int(self.settingValueList[0][5])

            if self.c.connectServer(ip, port, cmdPort, cameraName, imgSize, productName, cameraBrand, self.inspectionSensor, dataPort):
                self.label_3.setText('연결 완료')
                self.label_3.setStyleSheet("color: green;"
                                    "background-color: #7FFFD4")
                self.pushButton.setText('종료')
            else:
                self.c.stop()
                self.pushButton.setText('연결')
                self.label_3.setText('미접속')
                self.label_3.setStyleSheet("color: red;"
                                    "background-color: #FFCCCC")
        else:
            try:
                self.c.stop()
            except:
                print("error occur")
            finally:
                self.pushButton.setText('연결')
                self.label_3.setText('미접속')
                self.label_3.setStyleSheet("color: red;"
                                    "background-color: #FFCCCC")

    #
    # def countSocket(self, ipAddress, port, countMode):
    #     if countMode == 'total':
    #         getHistory = b'get history totalframes\r\n'
    #     elif countMode == 'passed':
    #         getHistory = b'get history passed\r\n'
    #     elif countMode == 'failed':
    #         getHistory = b'get history Failed\r\n'
    #
    #     print('here')
    #     with socket() as s:
    #         s.connect((ipAddress, port))
    #         s.sendall(getHistory)
    #         data = s.recv(1024)
    #
    #     print('Received', repr(data))
    #     count = str(data).split('\\r\\n')[1]
    #     return count

    def historyClear(self):

        # with socket() as s:
        #     s.connect((self.settingValueList[0][0], int(self.settingValueList[0][2])))
        #     if self.cameraBrand == 'Banner':
        #         doClearHistory = b'do history clear\r\n'
        #     else:
        #         doClearHistory = b'RST'
        #     s.sendall(doClearHistory)
        #     data = s.recv(1024)
        # print('Received', repr(data))

        self.label_23.setText('0')
        self.label_21.setText('0')
        self.label_24.setText('0')

        if self.inspectionNumber > 1:
            self.label_31.setText('0')
            self.label_39.setText('0')
            self.label_41.setText('0')
        else:
            self.label_31.setText('-')
            self.label_39.setText('-')
            self.label_41.setText('-')

        now = datetime.datetime.now()
        historyClearTime = now.strftime('%Y-%m-%d %H:%M:%S')
        self.label_62.setText(historyClearTime)

        writeResultHistory(mode = 'clear')
        infoLog.info('History Cleared')

    def updateMsg(self, msg):

        countInfo = msg.split(',')
        if self.inspectionNumber == 1:
            if self.cameraBrand == "Banner":
                resultFirst = int(countInfo[0])
            else:
                resultFirstStr = countInfo[0]

                if resultFirstStr == 'P':
                    resultFirst = 1
                else:
                    resultFirst = 0

            readResult = readResultHistory()
            historyFirst = list(map(int, readResult[0]))

            if resultFirst == 1 :
                historyFirst[0] += 1
                historyFirst[1] += 1
            else:
                resultString = self.label_26.text() + ': 실패'
                resultLog.info(resultString)
                historyFirst[0] += 1
                historyFirst[2] += 1

            historyFirst = list(map(str, historyFirst))

            self.label_23.setText(historyFirst[0])
            self.label_21.setText(historyFirst[1])
            self.label_24.setText(historyFirst[2])

            writeResultHistory(historyFirst)

        else:

            if self.cameraBrand =="Banner":
                resultFirst, resultSecond = list(map(int, countInfo[0:2]))
            else:
                resultFirstStr, resultSecondStr = countInfo[0:2]

                if resultFirstStr == 'P':
                    resultFirst = 1
                else:
                    resultFirst = 0

                if resultSecondStr == 'P':
                    resultSecond = 1
                else:
                    resultSecond = 0

            readResult = readResultHistory()
            historyFirst = list(map(int, readResult[0]))
            historySecond = list(map(int, readResult[1]))

            if resultFirst == 1 and resultSecond == 1:
                historyFirst[0] += 1
                historyFirst[1] += 1
                historySecond[0] += 1
                historySecond[1] += 1
            elif resultFirst == 1 and resultSecond == 0:
                historyFirst[0] += 1
                historyFirst[1] += 1
                historySecond[0] += 1
                historySecond[2] += 1
                resultString = self.label_26.text() + ': 성공, ' + self.label_35.text() +  ': 실패'
                resultLog.info(resultString)
            elif resultFirst == 0 and resultSecond == 1:
                historyFirst[0] += 1
                historyFirst[2] += 1
                historySecond[0] += 1
                historySecond[1] += 1
                resultString = self.label_26.text() + ': 실패, ' + self.label_35.text() +  ': 성공'
                resultLog.info(resultString)
            else:
                resultString = self.label_26.text() + ': 실패, ' + self.label_35.text() +  ': 실패'
                resultLog.info(resultString)
                historyFirst[0] += 1
                historyFirst[2] += 1
                historySecond[0] += 1
                historySecond[2] += 1

            historyFirst = list(map(str, historyFirst))
            historySecond = list(map(str, historySecond))

            self.label_23.setText(historyFirst[0])
            self.label_21.setText(historyFirst[1])
            self.label_24.setText(historyFirst[2])

            self.label_31.setText(historySecond[0])
            self.label_39.setText(historySecond[1])
            self.label_41.setText(historySecond[2])

            writeResultHistory(historyFirst, historySecond)


    def updateImg(self, inspectionTimeCameraName):
        inspectionTime = inspectionTimeCameraName.split('/')[0]
        cameraName = inspectionTimeCameraName.split('/')[1]
        self.label_7.setText(inspectionTime)

    def updateDisconnect(self):
        infoLog.info('Disconnected')

    def closeEvent(self, e):
        self.c.stop()

    def openSelectedDir(self):
        print(self.dateEdit.date().toPyDate())

        cameraBrand = self.settingValueList[0][4]
        cameraName = 'image_' + cameraBrand
        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        rel_path = cameraName +'\\' + str(self.dateEdit.date().toPyDate())[:7] +'\\' + str(self.dateEdit.date().toPyDate())
        abs_file_path = os.path.join(script_dir, rel_path)
        try:
            os.startfile(abs_file_path)
        except:
            message = '아래의 경로에 저장된 이미지가 없습니다.\n' + abs_file_path
            QMessageBox.about(self, "# WARNING: ", message)

    def makeDirectory(self, folderDir):
        if not os.path.isdir(folderDir):
            os.mkdir(folderDir)

    def networkConnected(self):
        self.myDialog = myDialog()
        self.myDialog.show()

    def dbSettingConnected(self):
        self.dbDialog = dbDialog()
        self.dbDialog.show()

class MyThread(threading.Thread):
    def __init__(self, ipAddress, port, product, cameraBrand):

        threading.Thread.__init__(self)
        self.daemon = True
        self.ipAddress = ipAddress
        self.port = int(port)
        self.product = product
        self.interval = int(myMyWindow.lineEdit.text())
        self.cameraBrand = cameraBrand

    def run(self):
        while not(exit.is_set()):
            totalCount = myMyWindow.label_23.text()
            passCount = myMyWindow.label_21.text()
            failCount = myMyWindow.label_24.text()
            resultList =[passCount, failCount, totalCount]

            totalCountSecond = myMyWindow.label_31.text()
            passCountSecond = myMyWindow.label_39.text()
            failCountSecond = myMyWindow.label_41.text()
            resultListSecond =[passCountSecond, failCountSecond, totalCountSecond]

            now = datetime.datetime.now()
            curDate = str(now)[:-7]

            host, user, password, database = readDBSettingValue()
            conn = pymssql.connect(host=host, user=user, password=password, database=database)
            try:
                infoLog.info('DB 저장 시도')
                for i in range(3):
                    cursor = conn.cursor()
                    tagId = myMyWindow.label_28.text() + 'ET00' + str(i+1)
                    cursor.callproc("SP_IFR_EQP_TREND", ['0', tagId, tagId, resultList[i], curDate, ''])
                    print(resultList[i])
                    cursor.close()
                    conn.commit()

                if int(myMyWindow.label_40.text()) > 1:
                    for i in range(3):
                        cursor = conn.cursor()
                        tagId = myMyWindow.label_37.text() + 'ET00' + str(i + 1)
                        cursor.callproc("SP_IFR_EQP_TREND", ['0', tagId, tagId, resultListSecond[i], curDate, ''])
                        print(resultList[i])
                        cursor.close()
                        conn.commit()

            except:
                infoLog.info('DB 저장 오류가 발생했습니다.')
            else:
                infoLog.info('DB 저장 성공')
                myMyWindow.label_7.setText(curDate)
            finally:
                conn.close()

            if stop == True:
                break

            exit.wait(self.interval)

def makeDirectory(folderDir):
    if not os.path.isdir(folderDir):
        os.mkdir(folderDir)

def writeResultHistory(firstHistory = None, secondHistory = None, mode = None):
    script_dir = os.path.dirname(__file__)
    rel_path = 'setting/resultHistory.csv'
    abs_file_path = os.path.join(script_dir, rel_path)
    try:
        f = open(abs_file_path, 'w', encoding='utf-8')
    except:
        infoLog.info('결과 이력 조회 실패')
    else:
        try:
            wr = csv.writer(f)
            if mode == 'clear':
                wr.writerow([0, 0, 0])
                wr.writerow([0, 0, 0])
            else:
                if secondHistory == None:
                    wr.writerow([firstHistory[0], firstHistory[1], firstHistory[2]])
                else:
                    wr.writerow([firstHistory[0], firstHistory[1], firstHistory[2]])
                    wr.writerow([secondHistory[0], secondHistory[1], secondHistory[2]])
            f.close()
        except:
            infoLog.info('결과 이력 정보 저장에 실패 했습니다.')
        else:
            infoLog.info('결과 이력 정보 저장에 성공 했습니다.')


def readResultHistory():
    script_dir = os.path.dirname(__file__)
    rel_path = 'setting/resultHistory.csv'
    abs_file_path = os.path.join(script_dir, rel_path)
    try:
        f = open(abs_file_path, 'r', encoding='utf-8')
    except:
        infoLog.info('결과 이력 조회 실패')
    else:
        rdr = csv.reader(f)
        Value = []
        for line in rdr:
            if line != [] :
                Value.append(line)
        f.close()
    return Value


def writeTimeIntervalValue():
    script_dir = os.path.dirname(__file__)
    rel_path = 'setting/timeIntervalReference.csv'
    abs_file_path = os.path.join(script_dir, rel_path)
    try:
        f = open(abs_file_path, 'w', encoding='utf-8')
    except:
        infoLog.info('수집주기 정보 조회 실패')
    else:
        try:
            wr = csv.writer(f)
            wr.writerow([myMyWindow.lineEdit.text()])
            f.close()
        except:
            infoLog.info('수집주기 정보 저장 실패')
        else:
            infoLog.info('수집주기 정보 저장 성공')


def readTimeIntervalValue():
    script_dir = os.path.dirname(__file__)
    rel_path = 'setting/timeIntervalReference.csv'
    abs_file_path = os.path.join(script_dir, rel_path)
    try:
        f = open(abs_file_path, 'r', encoding='utf-8')
    except:
        infoLog.info('수집주기 정보 조회 실패')
    else:
        rdr = csv.reader(f)
        timeIntervalValue = []
        for line in rdr:
            if line != [] :
                timeIntervalValue.append(line)
        f.close()
    return timeIntervalValue[0][0]


def readEthernetSettingValue():
    script_dir = os.path.dirname(__file__)
    rel_path = 'setting/cameraReference.csv'
    abs_file_path = os.path.join(script_dir, rel_path)
    try:
        f = open(abs_file_path, 'r', encoding='utf-8')
    except:
        infoLog.info('카메라 설정 파일이 경로에 존재하지 않습니다.', rel_path)
    else:
        rdr = csv.reader(f)
        settingValueList = []
        for line in rdr:
            if line != [] :
                settingValueList.append(line)
        f.close()
        print(settingValueList)
    return settingValueList


def readDBSettingValue():
    script_dir = os.path.dirname(__file__)
    rel_path = 'setting/dbReference.csv'
    abs_file_path = os.path.join(script_dir, rel_path)
    try:
        f = open(abs_file_path, 'r', encoding='utf-8')
    except:
        infoLog.info('카메라 설정 파일이 경로에 존재하지 않습니다.', rel_path)
    else:
        rdr = csv.reader(f)
        settingValueList = []
        for line in rdr:
            if line != [] :
                settingValueList.append(line)
        f.close()

    return settingValueList[0]

#
# def readInspectionSettingValue():
#     script_dir = os.path.dirname(__file__)
#     rel_path = 'setting/tagInfoReference.csv'
#     abs_file_path = os.path.join(script_dir, rel_path)
#     try:
#         f = open(abs_file_path, 'r', encoding='utf-8-sig')
#     except:
#         print('검사 설정 파일이 경로에 존재하지 않습니다.')
#     else:
#         rdr = csv.reader(f)
#         settingValueList = []
#         for line in rdr:
#             if line != [] :
#                 settingValueList.append(line)
#         f.close()
#         print(settingValueList)
#
#     return settingValueList[0]


def readMasterParameterSettingValue():
    script_dir = os.path.dirname(__file__)
    rel_path = 'setting/masterParameterReference.csv'
    abs_file_path = os.path.join(script_dir, rel_path)
    try:
        f = open(abs_file_path, 'r', encoding='utf-8-sig')
    except:
        infoLog.info('파일이 경로에 존재하지 않습니다.', rel_path)
    else:
        rdr = csv.reader(f)
        settingValueList = []
        for line in rdr:
            if line != [] :
                settingValueList.append(line)
        f.close()
        print(settingValueList)

    return settingValueList[0]


class myDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = uic.loadUi("setting_single.ui", self)
        self.settingValueList = readEthernetSettingValue()
        self.masterParameterSettingValue = readMasterParameterSettingValue()
        self.ui.lineEdit.setText(self.settingValueList[0][0])
        self.ui.lineEdit_2.setText(self.settingValueList[0][1])
        self.ui.lineEdit_5.setText(self.settingValueList[0][2])
        self.ui.lineEdit_10.setText(self.settingValueList[0][3])
        self.ui.lineEdit_6.setText(self.settingValueList[0][5])

        print(self.settingValueList[0][4])
        self.comboBox.setCurrentText(self.settingValueList[0][4])

        self.comboBox.currentIndexChanged.connect(self.selectionchange)
        self.ui.pushButton.clicked.connect(self.writeEthernetSettingValue)


    def selectionchange(self):
        print(self.comboBox.currentText())
        if self.comboBox.currentIndex() == 0:
            self.ui.lineEdit_2.setText(self.masterParameterSettingValue[0])
            self.ui.lineEdit_5.setText(self.masterParameterSettingValue[1])
        else:
            self.ui.lineEdit_2.setText(self.masterParameterSettingValue[2])
            self.ui.lineEdit_5.setText(self.masterParameterSettingValue[3])

        # self.label_12.setText(str((self.codeList[self.comboBox.currentIndex()])))
        # self.label_14.setText(str((self.standardList[self.comboBox.currentIndex()])))
        # self.label_15.setText(str((self.volumeList[self.comboBox.currentIndex()])))

    def writeEthernetSettingValue(self):
        ip = self.ui.lineEdit.text()
        imagePort = self.ui.lineEdit_2.text()
        comPort = self.ui.lineEdit_5.text()
        imgSize = self.ui.lineEdit_10.text()
        cameraType = self.ui.comboBox.currentText()
        dataPort = self.ui.lineEdit_6.text()

        script_dir = os.path.dirname(__file__)
        rel_path = 'setting/cameraReference.csv'
        abs_file_path = os.path.join(script_dir, rel_path)

        try:
            f = open(abs_file_path, 'w', encoding='utf-8')
        except:
            infoLog.info('카메라 설정 파일이 경로에 존재하지 않습니다.', rel_path)
        else:
            try:
                wr = csv.writer(f)
                wr.writerow([ip, imagePort, comPort, imgSize, cameraType, dataPort])
                f.close()
            except:
                infoLog.info('카메라 설정 정보 저장에 실패했습니다.')
            else:
                infoLog.info('카메라 설정 정보 저장에 성공했습니다.')

class dbDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = uic.loadUi("settingDB.ui", self)
        self.settingValueList = readDBSettingValue()
        self.ui.lineEdit.setText(self.settingValueList[0])
        self.ui.lineEdit_2.setText(self.settingValueList[1])
        self.ui.lineEdit_3.setText(self.settingValueList[2])
        self.ui.lineEdit_4.setText(self.settingValueList[3])
        self.ui.pushButton.clicked.connect(self.writeSettingValue)

    def writeSettingValue(self):
        host = self.ui.lineEdit.text()
        user = self.ui.lineEdit_2.text()
        password = self.ui.lineEdit_3.text()
        database = self.ui.lineEdit_4.text()

        script_dir = os.path.dirname(__file__)
        rel_path = 'setting/dbReference.csv'
        abs_file_path = os.path.join(script_dir, rel_path)

        try:
            f = open(abs_file_path, 'w', encoding='utf-8')
        except:
            infoLog.info('DB 접속 설정 파일이 경로에 존재하지 않습니다.', rel_path)
        else:
            try:
                wr = csv.writer(f)
                wr.writerow([host, user, password, database])
                f.close()
            except:
                infoLog.info('DB접속 설정 정보 저장에 실패했습니다.')
            else:
                infoLog.info('DB접속 설정 정보 저장에 성공했습니다.')

class inspectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = uic.loadUi("setting_inspection.ui", self)
        self.settingValueList = readEthernetSettingValue()
        self.masterParameterSettingValue = readMasterParameterSettingValue()
        self.ui.lineEdit.setText(self.settingValueList[0][0])
        self.ui.lineEdit_2.setText(self.settingValueList[0][1])
        self.ui.lineEdit_5.setText(self.settingValueList[0][2])
        self.ui.lineEdit_10.setText(self.settingValueList[0][3])

        self.comboBox.lineEdit().setAlignment(QtCore.Qt.AlignHCenter)

        print(self.settingValueList[0][4])

        self.comboBox.setEditable(True)
        self.comboBox.setCurrentText(self.settingValueList[0][4])
        self.comboBox.currentIndexChanged.connect(self.selectionchange)
        self.ui.pushButton.clicked.connect(self.writeEthernetSettingValue)

    def selectionchange(self):
        print(self.comboBox.currentText())
        if self.comboBox.currentIndex() == 0:
            self.ui.lineEdit_2.setText(self.masterParameterSettingValue[0])
            self.ui.lineEdit_5.setText(self.masterParameterSettingValue[1])
        else:
            self.ui.lineEdit_2.setText(self.masterParameterSettingValue[2])
            self.ui.lineEdit_5.setText(self.masterParameterSettingValue[3])

    def writeEthernetSettingValue(self):
        ip = self.ui.lineEdit.text()
        imagePort = self.ui.lineEdit_2.text()
        comPort = self.ui.lineEdit_5.text()
        imgSize = self.ui.lineEdit_10.text()
        cameraType = self.ui.comboBox.currentText()

        script_dir = os.path.dirname(__file__)
        rel_path = 'setting/cameraReference.csv'
        abs_file_path = os.path.join(script_dir, rel_path)

        try:
            f = open(abs_file_path, 'w', encoding='utf-8')
        except:
            infoLog.info('카메라 설정 파일이 경로에 존재하지 않습니다.', rel_path)
        else:
            try:
                wr = csv.writer(f)
                wr.writerow([ip, imagePort, comPort, imgSize, cameraType])
                f.close()
            except:
                infoLog.info('카메라 설정 정보 저장에 실패했습니다.')
            else:
                infoLog.info('카메라 설정 정보 저장에 성공했습니다.')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myMyWindow = myWindow()
    myMyWindow.show()
    sys.exit(app.exec_())
