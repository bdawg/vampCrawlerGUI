import pickle
import numpy as np
import matplotlib.pyplot as plt

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


autosaveFilename = 'vampCrawlerAutosave.pic'
restoreFileObj = open(autosaveFilename, 'r')
masterList = pickle.load(restoreFileObj)
restoreFileObj.close()

vhvvdata=masterList[0][2][0]
az = vhvvdata[1].bazims
bl = vhvvdata[1].blengths
blCols = bl/8.
plt.figure()
plt.clf()
scatterPlot = plt.scatter(az, vhvvdata[1].vhvv, c=blCols, marker='x', alpha=0.8)
clb = plt.colorbar(scatterPlot)
clb.ax.yaxis.set_visible(False)
a,b,c = plt.errorbar(az, vhvvdata[1].vhvv, yerr=vhvvdata[1].vhvverr, marker='', ls='',
                     alpha=0.8, capsize=0, zorder=0)
barColor = clb.to_rgba(blCols)
c[0].set_color(barColor)
plt.show()
