#! python2
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QCoreApplication
from NeteaseCloudMusic import CloudMusic

class Config():
    conf_dir = os.path.join(os.path.expanduser('~'), 'Netease')
    download_dir = os.path.join(conf_dir, 'Music')
    config_path = os.path.join(conf_dir, 'config.json')


class MyWindow(QWidget):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.config = Config()
        self.initUI()

    def initUI(self):
        self.createBaseNode()
        self.createAccurateDownload()
        self.createMessageBox()
        self.createProgressBar()

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.baseNode)
        mainLayout.addWidget(self.accurateDownload)
        mainLayout.addWidget(self.messageBox)
        mainLayout.addWidget(self.pbar)
        self.setLayout(mainLayout)

        self.resize(670, 440)
        self.show()

    def createBaseNode(self):
        self.baseNode = QGroupBox()
        layout = QGridLayout()

        searchLabel = QLabel("搜索：")
        searchEdit = QLineEdit()
        searchBtn = QPushButton("搜索")
        searchHbox = QHBoxLayout()
        searchHbox.addWidget(searchLabel)
        searchHbox.addWidget(searchEdit)
        searchHbox.addWidget(searchBtn)

        saveLabel = QLabel("文件保存位置：")
        self.saveEdit = QLineEdit()
        self.saveEdit.setText(self.config.download_dir)
        saveBtn = QPushButton("选择文件夹")
        saveBtn.clicked.connect(self.onSelectDir)
        saveHbox = QHBoxLayout()
        saveHbox.addWidget(saveLabel)
        saveHbox.addWidget(self.saveEdit)
        saveHbox.addWidget(saveBtn)

        nameStyLabel = QLabel("歌曲命名方式：")
        self.rb10 = QRadioButton('歌手-歌名', self)
        self.rb11 = QRadioButton('歌名-歌手', self)
        self.rbGroup = QButtonGroup(self)
        self.rbGroup.addButton(self.rb10, 10)
        self.rbGroup.addButton(self.rb11, 11)
        self.rbGroup.buttonClicked.connect(self.nameStySelect)
        nameStyHbox = QHBoxLayout()
        nameStyHbox.addWidget(nameStyLabel)
        nameStyHbox.addStretch(1)
        nameStyHbox.addWidget(self.rb10)
        nameStyHbox.addStretch(1)
        nameStyHbox.addWidget(self.rb11)
        nameStyHbox.addStretch(10)

        layout.setSpacing(10)
        #layout.addLayout(searchHbox, 1, 0)
        layout.addLayout(saveHbox, 1, 0)
        layout.addLayout(nameStyHbox, 2, 0)
        self.baseNode.setLayout(layout)

    def createAccurateDownload(self):
        self.accurateDownload = QGroupBox()  #QGroupBox("精确下载")
        layout = QGridLayout()

        self.combo = QComboBox(self)
        self.combo.addItem("歌曲ID")
        self.combo.addItem("专辑ID")
        self.combo.addItem("歌单ID")
        self.combo.activated[str].connect(self.onActivated)
        self.accEdit = QLineEdit()
        downBtn = QPushButton("下载")
        downBtn.clicked.connect(self.downloadMusic)

        layout.setSpacing(10)
        layout.addWidget(self.combo ,1,0)
        layout.addWidget(self.accEdit ,1,1)
        layout.addWidget(downBtn ,1,2)
        self.accurateDownload.setLayout(layout)

    def createMessageBox(self):
        self.messageBox = QGroupBox("Message")
        layout = QFormLayout()

        self.msgBox = QPlainTextEdit()
        layout.addRow(self.msgBox)

        self.messageBox.setLayout(layout)

    def createProgressBar(self):
        self.pbar = QProgressBar(self)
        self.pbar.resize(500, 20)
        self.pbar.setFormat("%v%")
        self.pbar.setValue(0)

    def nameStySelect(self):
        sender = self.sender()
        if sender == self.rbGroup:
            if self.rbGroup.checkedId() == 10:
                print "歌手-歌名"
            elif self.rbGroup.checkedId() == 11:
                print "歌名-歌手"
            else:
                print self.rbGroup.checkedId()

    def onActivated(self, text):
        print text
        self.accEdit.setText("")

    def onSelectDir(self):
        dirPath = QFileDialog.getExistingDirectory(self, "选择文件夹", "C:\\")
        if dirPath <> None:
            print 'dirPath = ' + dirPath
            self.config.download_dir = dirPath
            self.saveEdit.setText(dirPath)

    def downloadMusic(self):
        cloudMusic = CloudMusic(self, self.config.download_dir)
        ttype = self.combo.currentIndex()
        context = self.accEdit.text()
        if self.rbGroup.checkedId() > 0:
            nameSty = self.rbGroup.checkedId() % 2
            if ttype == 0:   #下载单曲
                if context == "":
                    info = "请输入内容"
                else:
                    info = cloudMusic.download_song_by_id(context, nameSty) #('2324487')
            elif ttype == 1:     #下载专辑
                if context == "":
                    info = "请输入内容"
                else:
                    info = cloudMusic.download_album_by_id(context, nameSty) #('234364')
            elif ttype == 2:     #下载歌单
                if context == "":
                    info = "请输入内容"
                else:
                    info = cloudMusic.download_mlist_by_id(context, nameSty) #('50812202')
                pass
        else:
            info = "请先选择歌曲命名方式"

        self.msgBox.appendPlainText(info)

class MainWindows(QMainWindow):
    def __init__(self):
        super(MainWindows, self).__init__()
        self.initUI()

    def initUI(self):
        mainView = MyWindow()
        self.setCentralWidget(mainView)

        self.statusBar().showMessage('Ready')
        exitAction = QAction('&Exit', self)       
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
 
        self.statusBar()
 
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
         
        self.resize(670, 440)
        self.setFixedSize(670, 440)
        #self.setWindowOpacity(0.5)
        self.centerInDesktop()
        self.setWindowTitle('网易云音乐/酷狗音乐下载器')
        self.show()

    #重写closeEvent方法，响应QCloseEvent事件
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', 
            "Are you sure to quit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def centerInDesktop(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindows()
    sys.exit(app.exec_())


    # http://www.cnblogs.com/archisama/p/5453260.html
    # https://wiki.python.org/moin/PyQt
    # https://blog.csdn.net/zhulove86/article/details/52563298