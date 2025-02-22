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
import random

#import vcGUIDesign
Ui_MainWindow, QMainWindow = loadUiType('vcGUIDesign.ui')

debugMsg = True

class vcApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)  # From the GUI design file

        # Set up some instance variables
        self.masterList = []
        self.setListAll = []
        self.chosenProps = []
        self.chosenPlotWindow = 0 # =0 for none, or number of window
        self.plot1Mode = 0 # 0 for V2, 1 for CP, more in future...
        self.plot2Mode = 0  # 0 for V2, 1 for CP, more in future...
        self.rootCrawlPath = ''
        self.vhvvPrefix = 'diffdata'  # Identify vhvv files as those starting with this
        self.autosaveFilename = 'vampCrawlerAutosave.pic'
        self.saveFilenameLineEdit.setText(self.autosaveFilename)
        self.maxBl = 8.
        self.maxBlLabel.setText('%3.2f' % self.maxBl)

        # Make connections
        self.crawlButton.clicked.connect(self.doCrawl)
        self.restoreMasterlistButton.clicked.connect(self.restoreSavedMasterlist)
        self.dateListbox.itemSelectionChanged.connect(self.updateSelections)
        self.fnameListbox.itemSelectionChanged.connect(self.updateSelections)
        self.maskListbox.itemSelectionChanged.connect(self.updateSelections)
        self.filterListbox.itemSelectionChanged.connect(self.updateSelections)
        self.selectedFilesListbox.itemSelectionChanged.connect(self.changeSelectedFile)
        self.diffdataFilesListbox.itemSelectionChanged.connect(self.changeSelectedDiffdata)
        self.plotWindowButtonNone.toggled.connect(lambda: self.changePlotWin(self.plotWindowButtonNone))
        self.plotWindowButton1.toggled.connect(lambda: self.changePlotWin(self.plotWindowButton1))
        self.plotWindowButton2.toggled.connect(lambda: self.changePlotWin(self.plotWindowButton2))
        self.plotV2CPButton.toggled.connect(lambda: self.changePlotWin(self.plotV2CPButton))
        self.saveFilenameLineEdit.editingFinished.connect(self.changeSaveFilename)
        self.crawlRootLineEdit.editingFinished.connect(self.changeCrawlRoot)
        self.maxBlSlider.valueChanged.connect(self.changeMaxBL)

        self.plot1V2Button.toggled.connect(lambda: self.changePlotMode(self.plot1V2Button))
        self.plot1CPButton.toggled.connect(lambda: self.changePlotMode(self.plot1CPButton))
        self.plot2V2Button.toggled.connect(lambda: self.changePlotMode(self.plot2V2Button))
        self.plot2CPButton.toggled.connect(lambda: self.changePlotMode(self.plot2CPButton))

        self.plot1 = mplPlotObject(self.mplWindow1, self.mplLayout1)
        self.plot2 = mplPlotObject(self.mplWindow2, self.mplLayout2)

        self.copyWin1Button.clicked.connect(self.copyFig)
        self.copyWin2Button.clicked.connect(self.copyFig)


    def doCrawl(self):
        print "doCrawl executed"
        #rootCrawlPath = '/Volumes/silo4/snert/VAMPIRESData_201603/'
        #vhvvPrefix = 'diffdata'  # Identify vhvv files as those starting with this
        #autosaveFilename = 'vampCrawlerAutosave.pic'

        masterList = []
        for dirpath, dirnames, filenames in os.walk(self.rootCrawlPath, followlinks=True):
            for fname in filenames:
                if fname.find('cubeinfo') > -1:
                    # Do stuff only if there is a cubeinfo file in the current directory
                    # Note- this method assumes there is only one cubeinfo file per dir
                    cubeInfoFilename = os.path.join(dirpath, fname)
                    print 'Found cubeinfo ' + cubeInfoFilename
                    try:
                        cubeInfo = readCubeInfo(cubeInfoFilename)
                    except:
                        print "WARNING! Couldn't read " + cubeInfoFilename + " - Ignoring, with error:"
                        print sys.exc_info()[0]
                        print ' '
                    else:
                        # Read vhvv data if it's there
                        # Each directory has a list vhvvData, each entry containing the
                        # diffdata filename and the vhvv object
                        vhvvData = []
                        for curFname in filenames:
                            if curFname.find(self.vhvvPrefix) == 0 and curFname.find('.idlvar') > -1:
                                curVhvvData = readVHVVdata(os.path.join(dirpath, curFname))
                                curVhvvEntry = [curFname, curVhvvData]
                                vhvvData.append(curVhvvEntry)

                        curEntry = [dirpath, cubeInfo, vhvvData]
                        masterList.append(curEntry)

        print 'Found total of ' + str(len(masterList)) + ' data folders'
        self.masterList = masterList
        self.setListAll = self.getAllCategoryContents()

        autosaveFileObj = open(self.autosaveFilename, 'wb')
        pickle.dump(self.masterList, autosaveFileObj)
        autosaveFileObj.close()

        # Initialise chosen properties as containing everything:
        self.chosenProps = self.setListAll
        self.refreshPropertyLists()
        self.refreshGUI()


    def restoreSavedMasterlist(self):
        restoreFileObj = open(self.autosaveFilename, 'r')
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

        # if self.chosenPlotWindow == 1:
        #     self.plot1.plotTestData()
        # if self.chosenPlotWindow == 2:
        #     self.plot2.plotTestData()


    def changeSelectedFile(self):
        useXlastChars = 50 # Only show this any characters in diffdata list box
        extnLength = 7 # Num chars in file extension (don't show)
        try:
            self.selectedFile = self.selectedFilesListbox.selectedItems()[0].text()

        except:
            print "No selection"
            pass

        else:
            if debugMsg:
                print self.selectedFile
            selectedRows = self.filterFunction()
            curRow = [sublist[0] for sublist in selectedRows].index(self.selectedFile)
            self.curVhvvData = selectedRows[curRow][2]
            self.fName = self.selectedFile.split('/')[-1]

            # Populate diffdata files list
            self.diffdataFilesListbox.blockSignals(True)
            self.diffdataFilesListbox.clear()
            for diffdataName in [vhvvRow[0] for vhvvRow in self.curVhvvData]:
                #diffDataShort = str(diffdataName).split('_')[-1]
                diffDataShort = str(diffdataName)[-useXlastChars:-extnLength]
                self.diffdataFilesListbox.addItem(diffDataShort)
            self.diffdataFilesListbox.blockSignals(False)

            self.diffdataFilesListbox.setCurrentRow(0)


            # curDiffdataRow = self.diffdataFilesListbox.currentRow()
            # if self.chosenPlotWindow == 1:
            #     self.plot1.plotVHVVdata(self.curVhvvData[curDiffdataRow], self.fName)
            # if self.chosenPlotWindow == 2:
            #     self.plot2.plotVHVVdata(self.curVhvvData[curDiffdataRow], self.fName)


    def changeSelectedDiffdata(self):
        curDiffdataRow = self.diffdataFilesListbox.currentRow()
        if self.chosenPlotWindow == 1:
            if self.plot1Mode == 0:
                self.plot1.plotVHVVdata(self.curVhvvData[curDiffdataRow], self.fName, maxBL=self.maxBl)
            else:
                self.plot1.plotDiffCPdata(self.curVhvvData[curDiffdataRow], self.fName)

        if self.chosenPlotWindow == 2:
            if self.plot2Mode == 0:
                self.plot2.plotVHVVdata(self.curVhvvData[curDiffdataRow], self.fName, maxBL=self.maxBl)
            else:
                self.plot2.plotDiffCPdata(self.curVhvvData[curDiffdataRow], self.fName)

        if self.chosenPlotWindow == 3:
            self.plot1.plotVHVVdata(self.curVhvvData[curDiffdataRow], self.fName, maxBL=self.maxBl)
            self.plot2.plotDiffCPdata(self.curVhvvData[curDiffdataRow], self.fName)


    def getAllCategoryContents(self):
        allCubeinfos = [sublist[1] for sublist in self.masterList]
        setOfMasks = set([sublist.mask for sublist in allCubeinfos])
        setOfFilters = set([sublist2[0] for sublist2 in [sublist.filters for
                                                         sublist in allCubeinfos]])
        setOfUTCs = set([sublist2[0] for sublist2 in [sublist.UTCs for
                                                      sublist in allCubeinfos]])
        yyyymmdd = []
        for UTC in setOfUTCs:
            try:
                date = dateutil.parser.parse(UTC)
                month = '%02d' % date.month
                day = '%02d' % date.day
                yyyymmdd.append(str(date.year) + month + day)
            except:
                print "ERROR: Could not parse date: "+UTC
        # Append empty date for old data:
        yyyymmdd.append('')
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
            try:
                date = dateutil.parser.parse(curRow[1].UTCs[0])
                month = '%02d' % date.month
                day = '%02d' % date.day
                yymmdd = str(date.year) + month + day
            except:
                #print "ERROR: Could not parse date: "+curRow[1].UTCs[0]
                yymmdd = ''

            if (curRow[1].mask in self.chosenProps[1] and curRow[1].filters[0] in self.chosenProps[2] and
                        yymmdd in self.chosenProps[0] and curRow[1].cubename[0] in self.chosenProps[3]):
                chosenRows.append(curRow)

        return chosenRows


    def changePlotWin(self,button):
        if button.isChecked() == True:
            if debugMsg:
                print "Selected "+button.text()
            if button.objectName() == "plotWindowButtonNone":
                self.chosenPlotWindow = 0
            if button.objectName() == "plotWindowButton1":
                self.chosenPlotWindow = 1
            if button.objectName() == "plotWindowButton2":
                self.chosenPlotWindow = 2
            if button.objectName() == "plotV2CPButton":
                self.chosenPlotWindow = 3
            self.changeSelectedDiffdata()


    def changePlotMode(self,button):
        if button.isChecked() == True:
            if button.objectName() == "plot1V2Button":
                self.plot1Mode = 0
            if button.objectName() == "plot1CPButton":
                self.plot1Mode = 1
            if button.objectName() == "plot2V2Button":
                self.plot2Mode = 0
            if button.objectName() == "plot2CPButton":
                self.plot2Mode = 1
        self.changeSelectedDiffdata()


    def changeSaveFilename(self):
        self.autosaveFilename = str(self.saveFilenameLineEdit.text())

    def changeCrawlRoot(self):
        self.rootCrawlPath = str(self.crawlRootLineEdit.text())

    def copyFig(self):
        senderButton = self.sender().objectName()
        if senderButton == 'copyWin1Button':
            canvas = self.plot1.canvas
        else:
            canvas = self.plot2.canvas
        pixmap = QtGui.QPixmap.grabWidget(canvas)
        pixmap.save('tempSave.png')
        QtGui.QApplication.clipboard().setPixmap(pixmap)

    def changeMaxBL(self):
        self.maxBl = self.maxBlSlider.value()/10.
        self.maxBlLabel.setText('%3.2f' % self.maxBl)
        self.changeSelectedDiffdata()


class mplPlotObject:
    def __init__(self, window, layout):
        self.figureObj = Figure()
        self.canvas = FigureCanvas(self.figureObj)
        layout.addWidget(self.canvas)
        self.canvas.draw()
        toolbar = NavigationToolbar(self.canvas, window, coordinates=True)
        layout.addWidget(toolbar)
        self.figureObj.patch.set_facecolor('none')


    def plotTestData(self):
        data = [random.random() for i in range(10)]
        self.ax = self.figureObj.add_subplot(211)
        self.ax.hold(False)
        self.ax.plot(data, '*-')
        self.figureObj.tight_layout()
        self.canvas.draw()


    def plotVHVVdata(self, vhvvData, fName, maxBL = 8.):
        if debugMsg:
            print 'Plotting vhvv data for ' + vhvvData[0]
        az = vhvvData[1].bazims
        bl = vhvvData[1].blengths
        blCols = bl / np.max(bl)

        az = az[bl <= maxBL]
        vhvv = vhvvData[1].vhvv[bl <= maxBL]
        vhvverr = vhvvData[1].vhvverr[bl <= maxBL]
        vhvvu = vhvvData[1].vhvvu[bl <= maxBL]
        vhvvuerr = vhvvData[1].vhvvuerr[bl <= maxBL]
        blCols = blCols[bl <= maxBL]
        bl = bl[bl <= maxBL]

        # This is a horrible hack to get the error bar colors to match...
        self.ax = self.figureObj.add_subplot(211)
        scatterPlt = self.ax.scatter(az, vhvv, c=blCols, marker='x', alpha=0.8)
        clb = self.figureObj.colorbar(scatterPlt)
        barColor = clb.to_rgba(blCols)

        self.figureObj.clf()
        self.figureObj.suptitle(vhvvData[0])
        self.ax = self.figureObj.add_subplot(211)
        scatterPlt = self.ax.scatter(az, vhvv, c=blCols, marker='x', alpha=0.8)
        a,b,c = self.ax.errorbar(az, vhvv, yerr=vhvverr, marker='', ls='',
                             alpha=0.8, capsize=0, zorder=0)
        c[0].set_color(barColor)
        #self.ax.set_title('foo')
        sigString = "$\sigma$ = %.4f" % np.std(vhvv)
        chi2String = "$\chi^2_{null}$ = %.2f" % self.reducedChi2(vhvv, vhvverr)
        infoString = sigString + '      ' + chi2String
        self.ax.text(0.5, 0.9, infoString, horizontalalignment='center', verticalalignment='center',
                     transform = self.ax.transAxes)
        self.ax.text(0.5, 0.1, fName, horizontalalignment='center', verticalalignment='center',
                     transform=self.ax.transAxes)
        self.figureObj.tight_layout()


        self.ax = self.figureObj.add_subplot(212)
        scatterPlt = self.ax.scatter(az, vhvvu, c=blCols, marker='x', alpha=0.8)
        a,b,c = self.ax.errorbar(az, vhvvu, yerr=vhvvuerr, marker='', ls='',
                             alpha=0.8, capsize=0, zorder=0)
        c[0].set_color(barColor)
        sigString = "$\sigma$ = %.4f" % np.std(vhvvu)
        chi2String = "$\chi^2_{null}$ = %.2f" % self.reducedChi2(vhvvu, vhvvuerr)
        infoString = sigString + '      ' + chi2String
        self.ax.text(0.5, 0.9, infoString, horizontalalignment='center', verticalalignment='center',
                     transform = self.ax.transAxes)
        self.ax.text(0.5, 0.1, fName, horizontalalignment='center', verticalalignment='center',
                     transform=self.ax.transAxes)
        self.figureObj.tight_layout()
        self.canvas.draw()


    def plotDiffCPdata(self, vhvvData, fName):
        nBins = 25
        if debugMsg:
            print 'Plotting diffCP data for ' + vhvvData[0]
        try:
            vhvvData[1].diffCP
        except:
            print "No closure phase data present for this file"
        else:
            if debugMsg:
                print "Found CP Data for " + vhvvData[0]
            cp = vhvvData[1].diffCP/np.pi * 180
            cpU = vhvvData[1].diffCPu / np.pi * 180
            self.figureObj.clf()
            self.figureObj.suptitle(vhvvData[0])
            self.ax = self.figureObj.add_subplot(211)
            histPlt = self.ax.hist(cp, nBins)
            self.ax.set_xlabel('Differential closure phase (deg)')
            self.ax.set_ylabel('Frequency')
            sigString = "$\sigma$ = %.3f" % np.std(cp)
            self.ax.text(0.99, 0.9, sigString, horizontalalignment='right', verticalalignment='center',
                         transform=self.ax.transAxes)
            self.ax.text(0.99, 0.75, fName, horizontalalignment='right', verticalalignment='center',
                         transform=self.ax.transAxes)
            #self.figureObj.tight_layout()

            self.ax = self.figureObj.add_subplot(212)
            histPlt = self.ax.hist(cpU, nBins)
            self.ax.set_xlabel('Differential closure phase (deg)')
            self.ax.set_ylabel('Frequency')
            sigString = "$\sigma$ = %.3f" % np.std(cpU)
            self.ax.text(0.99, 0.9, sigString, horizontalalignment='right', verticalalignment='center',
                         transform=self.ax.transAxes)
            self.ax.text(0.99, 0.75, fName, horizontalalignment='right', verticalalignment='center',
                         transform=self.ax.transAxes)
            self.figureObj.tight_layout()
            self.canvas.draw()


    def reducedChi2(self, vhvv, vhvverr):
        # Reduced chi^2 for null hypothesis (vhvv=1)
        chi2 = np.sum( (vhvv-1.)**2 / vhvverr**2 )
        dof = len(vhvv) - 1
        return chi2 / dof


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
        try:
            self.diffCP = vhvvObj.cp
            self.diffCPerr = vhvvObj.cperr
            self.diffCPu = vhvvObj.cpu
            self.diffCPuerr = vhvvObj.cpuerr
            self.BL2H_IX = vhvvObj.BL2H_IX
            self.H2BL_IX = vhvvObj.H2BL_IX
            self.BL2BS_IX = vhvvObj.BL2BS_IX
            self.BS2BL_IX = vhvvObj.BS2BL_IX
        except:
            if debugMsg:
                print "Couldn't find diff CP data for "+vhvvFilename
        del (vhvvObj)




def main():
    if debugMsg:
        print "main() running"
        print "vampCrawler version 0.1"

    app = QtGui.QApplication(sys.argv)
    form = vcApp()
    form.show()
    app.exec_()


if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function
