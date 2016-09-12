from PyQt4 import QtGui
import sys
import numpy as np
from scipy import io
import os
import pickle
import dateutil.parser
from PyQt4.uic import loadUiType
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt
import random

#import vcGUIDesign
Ui_MainWindow, QMainWindow = loadUiType('vcGUIDesign.ui')

class vcApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)  # From the GUI design file

        # Set up some instance variables
        self.masterList = []
        self.setListAll = []
        self.chosenProps = []

        # Make connections
        self.crawlButton.clicked.connect(self.doCrawl)
        self.restoreMasterlistButton.clicked.connect(self.restoreSavedMasterlist)
        self.dateListbox.itemSelectionChanged.connect(self.updateSelections)
        self.fnameListbox.itemSelectionChanged.connect(self.updateSelections)
        self.maskListbox.itemSelectionChanged.connect(self.updateSelections)
        self.filterListbox.itemSelectionChanged.connect(self.updateSelections)

        self.plot1 = mplPlotObject(self.mplWindow1, self.mplLayout1)
        self.plot2 = mplPlotObject(self.mplWindow2, self.mplLayout2)

    def doCrawl(self):
        print "doCrawl executed"
        rootCrawlPath = '/Volumes/silo4/snert/VAMPIRESData_201603/'
        vhvvPrefix = 'diffdata'  # Identify vhvv files as those starting with this
        autosaveFilename = 'vampCrawlerAutosave.pic'

        masterList = []
        for dirpath, dirnames, filenames in os.walk(rootCrawlPath, followlinks=True):
            for fname in filenames:
                if fname.find('cubeinfo') > -1:
                    # Do stuff only if there is a cubeinfo file in the current directory
                    # Note- this method assumes there is only one cubeinfo file per dir
                    cubeInfoFilename = os.path.join(dirpath, fname)
                    print 'Found cubeinfo ' + cubeInfoFilename
                    try:
                        cubeInfo = readCubeInfo(cubeInfoFilename)
                    except:
                        print "WARNING! Couldn't read " + cubeInfoFilename + " - Ignoring"
                    else:
                        # Read vhvv data if it's there
                        # Each directory has a list vhvvData, each entry containing the
                        # diffdata filename and the vhvv object
                        vhvvData = []
                        for curFname in filenames:
                            if curFname.find(vhvvPrefix) == 0 and curFname.find('.idlvar') > -1:
                                curVhvvData = readVHVVdata(os.path.join(dirpath, curFname))
                                curVhvvEntry = [curFname, curVhvvData]
                                vhvvData.append(curVhvvEntry)

                        curEntry = [dirpath, cubeInfo, vhvvData]
                        masterList.append(curEntry)

        print 'Found total of ' + str(len(masterList)) + ' data folders'
        self.masterList = masterList
        self.setListAll = self.getAllCategoryContents()

        autosaveFileObj = open(autosaveFilename, 'wb')
        pickle.dump(self.masterList, autosaveFileObj)
        autosaveFileObj.close()

        # Initialise chosen properties as containing everything:
        self.chosenProps = self.setListAll
        self.refreshPropertyLists()
        self.refreshGUI()


    def restoreSavedMasterlist(self):
        autosaveFilename = 'vampCrawlerAutosave.pic'
        restoreFileObj = open(autosaveFilename, 'r')
        self.masterList = pickle.load(restoreFileObj)
        restoreFileObj.close()

        # Initialise chosen properties as containing everything:
        self.setListAll = self.getAllCategoryContents()
        self.chosenProps = self.setListAll
        self.refreshPropertyLists()
        self.refreshGUI()


    def refreshGUI(self):
        selectedRows = self.filterFunction()
        self.selectedFilesListbox.clear()
        for dirpath in [sublist[0] for sublist in selectedRows]:
            self.selectedFilesListbox.addItem(dirpath)


    def refreshPropertyLists(self):
        # Update listings
        self.setListAll = self.getAllCategoryContents()

        self.dateListbox.clear()
        for text in self.setListAll[0]:
            self.dateListbox.addItem(text)
        self.dateListbox.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        self.fnameListbox.clear()
        for text in self.setListAll[3]:
            self.fnameListbox.addItem(text)
        self.fnameListbox.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        self.maskListbox.clear()
        for text in self.setListAll[1]:
            self.maskListbox.addItem(text)
        self.maskListbox.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        self.filterListbox.clear()
        for text in self.setListAll[2]:
            self.filterListbox.addItem(text)
        self.filterListbox.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)


    def updateSelections(self):
        # sender = self.sender()
        # print ["Updating selections from "+sender.objectName()]
        # for item in self.fnameListbox.selectedItems():
        #     print item.text()
        # print self.dateListbox.selectedItems()[0].text()
        # print self.fnameListbox.selectedItems.text()
        # print self.maskListbox.selectedItems.text()
        # print self.filterListbox.selectedItems.text()
        # self.fnameListbox.selectedItems()[0].text()
        selectedDates = [item.text() for item in self.dateListbox.selectedItems()]
        selectedMasks = [item.text() for item in self.maskListbox.selectedItems()]
        selectedFilters = [item.text() for item in self.filterListbox.selectedItems()]
        selectedFNames = [item.text() for item in self.fnameListbox.selectedItems()]
        self.chosenProps = [selectedDates, selectedMasks, selectedFilters, selectedFNames]
        self.refreshGUI()

        # self.rmmpl()
        # fig2 = Figure()
        # fig2Ax = fig2.add_subplot(111)
        # fig2Ax.plot(np.random.rand(100))
        # self.canvas2 = self.addPlot(fig2, self.mplWindow2, self.mplLayout2)
        # self.canvas.
        # self.fig2Ax.plot(np.random.rand(100))

        self.plot1.plotData()
        self.plot2.plotData()


    def getAllCategoryContents(self):
        allCubeinfos = [sublist[1] for sublist in self.masterList]
        setOfMasks = set([sublist.mask for sublist in allCubeinfos])
        setOfFilters = set([sublist2[0] for sublist2 in [sublist.filters for
                                                         sublist in allCubeinfos]])
        setOfUTCs = set([sublist2[0] for sublist2 in [sublist.UTCs for
                                                      sublist in allCubeinfos]])
        yyyymmdd = []
        for UTC in setOfUTCs:
            date = dateutil.parser.parse(UTC)
            month = '%02d' % date.month
            day = '%02d' % date.day
            yyyymmdd.append(str(date.year) + month + day)
        setOfyyyymmdd = set(yyyymmdd)
        setOfCubenames = set([sublist2[0] for sublist2 in [sublist.cubename for
                                                           sublist in allCubeinfos]])
        # Return a list of these sets
        setList = [setOfyyyymmdd, setOfMasks, setOfFilters, setOfCubenames]
        return setList


    def filterFunction(self):
        # Find rows in masterList that match the chosenProps

        chosenRows = []
        for curRow in self.masterList:
            date = dateutil.parser.parse(curRow[1].UTCs[0])
            month = '%02d' % date.month
            day = '%02d' % date.day
            yymmdd = str(date.year) + month + day

            if (curRow[1].mask in self.chosenProps[1] and curRow[1].filters[0] in self.chosenProps[2] and
                        yymmdd in self.chosenProps[0] and curRow[1].cubename[0] in self.chosenProps[3]):
                chosenRows.append(curRow)

        return chosenRows


    # def addPlot(self, fig, tgtWindow, tgtLayout):
    #     # Add the plot 'fig' to the layout 'tgtLayout' in the container 'tgtWindow'
    #     self.canvas = FigureCanvas(fig)
    #     #self.mplLayout1.addWidget(self.canvas)
    #     tgtLayout.addWidget(self.canvas)
    #     self.canvas.draw()
    #     self.toolbar = NavigationToolbar(self.canvas,
    #         tgtWindow, coordinates=True)
    #     tgtLayout.addWidget(self.toolbar)
    #     fig.patch.set_facecolor('none')
    #     return self.canvas
    #
    #
    # def rmmpl(self):
    #     self.mplLayout1.removeWidget(self.canvas)
    #     self.canvas.close()
    #     self.mplLayout1.removeWidget(self.toolbar)
    #     self.toolbar.close()


class mplPlotObject:
    def __init__(self, window, layout):
        self.figureObj = Figure()
        self.canvas = FigureCanvas(self.figureObj)
        layout.addWidget(self.canvas)
        self.canvas.draw()
        toolbar = NavigationToolbar(self.canvas, window, coordinates=True)
        layout.addWidget(toolbar)
        self.figureObj.patch.set_facecolor('none')

    def plotData(self):
        data = [random.random() for i in range(10)]
        self.ax = self.figureObj.add_subplot(111)
        self.ax.hold(False)
        self.ax.plot(data, '*-')
        self.figureObj.tight_layout()
        self.canvas.draw()


class readCubeInfo:
    def __init__(self, cubeInfoFilename):
        # Get useful metadata from cubeinfo file
        cubeinfoObj = io.readsav(cubeInfoFilename, python_dict=False, verbose=False)
        self.UTCs = cubeinfoObj.olog.utc[0]
        self.filters = cubeinfoObj.olog.filter[0]
        self.ras = cubeinfoObj.olog.ra[0]
        self.decs = cubeinfoObj.olog.dec[0]
        self.mask = cubeinfoObj.olog.mask[0]
        self.adate = cubeinfoObj.olog.adate[0]
        self.emgains = cubeinfoObj.olog.emgain[0]
        self.mffile = cubeinfoObj.plog.mf_file[0]
        self.pkflux = cubeinfoObj.framestats.pkflx[0]
        self.totflux = cubeinfoObj.framestats.totflx[0]
        self.cubename = cubeinfoObj.olog.cube_fname[0][0]
        del (cubeinfoObj)


class readVHVVdata:
    def __init__(self, vhvvFilename):
        vhvvObj = io.readsav(vhvvFilename, python_dict=False, verbose=False)
        self.vhvv = vhvvObj.vhvv
        self.vhvverr = vhvvObj.vhvverr
        self.vhvvu = vhvvObj.vhvvu
        self.vhvvuerr = vhvvObj.vhvvuerr
        self.blengths = vhvvObj.blengths
        self.bazims = vhvvObj.bazims
        del (vhvvObj)




def main():
    print "main() running"

    app = QtGui.QApplication(sys.argv)
    form = vcApp()

    # fig1 = Figure()
    # fig1Ax = fig1.add_subplot(111)
    # fig1Ax.plot(np.random.rand(100))
    # form.canvas1 = form.addPlot(fig1, form.mplWindow1, form.mplLayout1)
    # form.fig2 = Figure()
    # form.fig2Ax = form.fig2.add_subplot(111)
    # form.fig2Ax.plot(np.random.rand(100))
    # form.canvas2 = form.addPlot(form.fig2, form.mplWindow2, form.mplLayout2)

    form.show()
    app.exec_()


if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function
