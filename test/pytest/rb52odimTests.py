'''
Copyright (C) 2016 The Crown (i.e. Her Majesty the Queen in Right of Canada)

This file is an add-on to RAVE.

RAVE is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RAVE is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with RAVE.  If not, see <http://www.gnu.org/licenses/>.
------------------------------------------------------------------------*/

rb52odim unit tests

@file
@author Daniel Michelson and Peter Rodriguez, Environment and Climate Change Cananda
@date 2016-08-17
'''
import os, unittest, types, glob
import _rave
import _raveio
import _polarscan
import _polarscanparam
import _ravefield
import _rb52odim, rb52odim
import numpy as np

# see http://git.baltrad.eu/git/?p=rave.git;a=blob_plain;f=modules/rave.c
#_rave.setDebugLevel(_rave.Debug_RAVE_SPEWDEBUG)
#_rave.setDebugLevel(_rave.Debug_RAVE_DEBUG)
_rave.setDebugLevel(_rave.Debug_RAVE_WARNING) #turns off rave_hlhdf_utilities INFO : Adding group: how

## Helper functions for ODIM validation below. For some reason, unit test
#  objects can't pass tests to methods, but they can be passed to functions.

# Lib/rb52odim.py:mergeOdimScans2Pvol() added these to the top level
TOP_IGNORE=[
           'how/task'
          ,'how/TXtype'
          ,'how/beamwH'
          ,'how/beamwV'
          ,'how/polmode'
          ,'how/poltype'
          ,'how/software'
          ,'how/sw_version'
          ,'how/system'
          ,'how/wavelength'
          ,'how/comment'
          ]

# Not needed because RAVE either assigns these automagically, or they are just not relevant
IGNORE = [
    'what/version',
    'what/object', 
    'how/_orig_file_format',
    'how/noisepowerh', #accept both raw (long) or processed (double)
    'how/noisepowerv', #accept both raw (long) or processed (double)
    ] + TOP_IGNORE

def validateAttributes(utest, obj, ref_obj):
    for aname in ref_obj.getAttributeNames():
        if aname not in IGNORE:
            ref_attr = ref_obj.getAttribute(aname)
            attr = obj.getAttribute(aname)
            if isinstance(ref_attr, np.ndarray):  # Arrays get special treatment
                utest.assertTrue(np.array_equal(attr, ref_attr))
#                try: #nicer failure reporting
#                    np.testing.assert_allclose(attr, ref_attr, rtol=1e-5, atol=0) #for no remake of ref files (numpy v1.16)
#                except:
#                    print('AssertionError: aname : '+aname)
            else:
                try:
                    utest.assertEqual(attr, ref_attr)
                except AssertionError as e:
                    print('AssertionError: aname : '+aname)
                    print('ref_attr : ', ref_attr)
                    print('    attr : ',     attr)
#                    import pdb; pdb.set_trace()
#                    utest.fail(str(e))


def validateTopLevel(utest, obj, ref_obj):
    utest.assertEqual(obj.source, ref_obj.source)
    utest.assertEqual(obj.date , ref_obj.date)
    utest.assertEqual(obj.time, ref_obj.time)
    utest.assertAlmostEqual(obj.longitude, ref_obj.longitude, 12)
    utest.assertAlmostEqual(obj.latitude, ref_obj.latitude, 12)
    utest.assertAlmostEqual(obj.height, ref_obj.height, 12)
    utest.assertAlmostEqual(obj.beamwidth, ref_obj.beamwidth, 12)
    validateAttributes(utest, obj, ref_obj)


def validateScan(utest, scan, ref_scan):
    utest.assertEqual(scan.source, ref_scan.source)
    utest.assertEqual(scan.date, ref_scan.date)
    utest.assertEqual(scan.time, ref_scan.time)
    utest.assertEqual(scan.startdate, ref_scan.startdate)
    utest.assertEqual(scan.starttime, ref_scan.starttime)
    utest.assertEqual(scan.enddate, ref_scan.enddate)
    utest.assertEqual(scan.endtime, ref_scan.endtime)
    utest.assertAlmostEqual(scan.longitude, ref_scan.longitude, 12)
    utest.assertAlmostEqual(scan.latitude, ref_scan.latitude, 12)
    utest.assertAlmostEqual(scan.height, ref_scan.height, 12)
    utest.assertAlmostEqual(scan.beamwidth, ref_scan.beamwidth, 12)
    utest.assertAlmostEqual(scan.elangle, ref_scan.elangle, 12)
    utest.assertEqual(scan.nrays, ref_scan.nrays)
    utest.assertEqual(scan.nbins, ref_scan.nbins)
    utest.assertEqual(scan.a1gate, ref_scan.a1gate)
    utest.assertEqual(scan.rscale, ref_scan.rscale)
    utest.assertEqual(scan.rstart, ref_scan.rstart)
    for pname in ref_scan.getParameterNames():
#        print 'pname : '+pname
        utest.assertEqual(scan.hasParameter(pname), 
                           ref_scan.hasParameter(pname))
        param = scan.getParameter(pname)
        ref_param = ref_scan.getParameter(pname)
        data, ref_data = param.getData(), ref_param.getData()
        utest.assertTrue(np.array_equal(data, ref_data))
        validateAttributes(utest, param, ref_param)
    validateAttributes(utest, scan, ref_scan)
    
def validateMergedPvol(self, new_pvol, iSCAN, ref_RB5_TARBALL):
    new_scan = new_pvol.getScan(iSCAN)
    # Aha, scan.time NE scan.starttime; getScan() uses parent pvol for time!
    new_scan.time=new_scan.starttime

    ref_rio = rb52odim.combineRB5FromTarball(ref_RB5_TARBALL, None, return_rio=True)
    self.assertTrue(ref_rio.objectType is _rave.Rave_ObjectType_SCAN)
    ref_scan = ref_rio.object

    # Note: ref_scan only has 1 param to loop upon
    validateTopLevel(self, new_scan, ref_scan)
    validateScan(self, new_scan, ref_scan)


class rb52odimTest(unittest.TestCase):
    BAD_RB5_VOL  = "../org/2008053002550300dBZ.vol" #volume version="5.22.6"
    GOOD_RB5_VOL = "../org/2016092614304000dBZ.vol" #volume version="5.43.11"
    GOOD_RB5_AZI = "../org/2016081612320300dBZ.azi" #volume version="5.43.11"
    NEW_H5_VOL = "../new/2016092614304000dBZ.vol.new.h5"
    NEW_H5_AZI = "../new/2016081612320300dBZ.azi.new.h5"
    REF_H5_VOL = "../ref/2016092614304000dBZ.vol.ref.h5"  # Assumes that these reference files are ODIM compliant
    REF_H5_AZI = "../ref/2016081612320300dBZ.azi.ref.h5"  
    FILELIST_RB5 = [\
        "../org/Dopvol1_A.azi/2015120916500500dBuZ.azi",\
        "../org/Dopvol1_A.azi/2015120916500500dBZ.azi",\
        "../org/Dopvol1_A.azi/2015120916500500PhiDP.azi",\
        "../org/Dopvol1_A.azi/2015120916500500RhoHV.azi",\
        "../org/Dopvol1_A.azi/2015120916500500SQI.azi",\
        "../org/Dopvol1_A.azi/2015120916500500uPhiDP.azi",\
        "../org/Dopvol1_A.azi/2015120916500500V.azi",\
        "../org/Dopvol1_A.azi/2015120916500500W.azi",\
        "../org/Dopvol1_A.azi/2015120916500500ZDR.azi"\
        ] #volume version="5.43.10"
    NEW_H5_FILELIST = "../new/caxah_dopvol1a_20151209T1650Z.by_filelist.new.h5"
    REF_H5_FILELIST = "../ref/caxah_dopvol1a_20151209T1650Z.by_filelist.ref.h5"
    RB5_TARBALL_DOPVOL1A = "../org/caxah_dopvol1a_20151209T1650Z.azi.tar.gz"
    RB5_TARBALL_DOPVOL1B = "../org/caxah_dopvol1b_20151209T1650Z.azi.tar.gz"
    RB5_TARBALL_DOPVOL1C = "../org/caxah_dopvol1c_20151209T1650Z.azi.tar.gz"
    NEW_H5_TARBALL_DOPVOL1A = "../new/caxah_dopvol1a_20151209T1650Z.azi.new.h5"
    NEW_H5_TARBALL_DOPVOL1B = "../new/caxah_dopvol1b_20151209T1650Z.azi.new.h5"
    NEW_H5_TARBALL_DOPVOL1C = "../new/caxah_dopvol1c_20151209T1650Z.azi.new.h5"
    REF_H5_TARBALL_DOPVOL1B = "../ref/caxah_dopvol1b_20151209T1650Z.azi.ref.h5"
    NEW_H5_MERGED_PVOL = "../new/caxah_dopvol_20151209T1650Z.vol.new.h5"
    REF_H5_MERGED_PVOL = "../ref/caxah_dopvol_20151209T1650Z.vol.ref.h5"
    CASRA_AZI_dBZ = "../org/CASRA_2017121520051400dBZ.azi.gz" #volume version="5.51.3"
    CASRA_AZI = "../org/CASRA*azi.gz"
    CASRA_VOL = "../org/CASRA*vol.gz"
    REF_CASRA_H5_SCAN = "../ref/CASRA_20171215200514_scan.ref.h5"
    REF_CASRA_H5_PVOL = "../ref/CASRA_20171215200003_pvol.ref.h5"

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testWrongInput(self):
        status = _rb52odim.isRainbow5(self.REF_H5_AZI)
        self.assertFalse(status)

    def testIsBadRB5Input(self):
        status = _rb52odim.isRainbow5(self.BAD_RB5_VOL)
        self.assertFalse(status)

    def testIsGoodRB5Input(self):
        status = _rb52odim.isRainbow5(self.GOOD_RB5_VOL)
        self.assertTrue(status)

    #2020-Jan-14: isRainbow5() now handles .gz files
    def testIsGoodRB5gzInput(self):
        status = _rb52odim.isRainbow5(self.CASRA_AZI_dBZ)
        self.assertTrue(status)

    def testReadRB5Azi(self):
        rio = _rb52odim.readRB5(self.GOOD_RB5_AZI)
        self.assertTrue(rio.objectType is _rave.Rave_ObjectType_SCAN)
        scan = rio.object
        ref_scan = _raveio.open(self.REF_H5_AZI).object
        validateTopLevel(self, scan, ref_scan)
        validateScan(self, scan, ref_scan)

    def testReadRB5Vol(self):
        rio = _rb52odim.readRB5(self.GOOD_RB5_VOL)
        self.assertTrue(rio.objectType is _rave.Rave_ObjectType_PVOL)
        pvol = rio.object
        ref_pvol = _raveio.open(self.REF_H5_VOL).object
        self.assertEqual(pvol.getNumberOfScans(), ref_pvol.getNumberOfScans())
        validateTopLevel(self, pvol, ref_pvol)
        for i in range(pvol.getNumberOfScans()):
            scan = pvol.getScan(i)
            ref_scan = ref_pvol.getScan(i)
            validateScan(self, scan, ref_scan)

    def testSingleRB5Azi(self):
        rb52odim.singleRB5(self.GOOD_RB5_AZI,out_fullfile=self.NEW_H5_AZI)
        new_rio = _raveio.open(self.NEW_H5_AZI)
        ref_rio = _raveio.open(self.REF_H5_AZI)
        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_SCAN)
        new_scan, ref_scan = new_rio.object, ref_rio.object
        validateTopLevel(self, new_scan, ref_scan)
        validateScan(self, new_scan, ref_scan)
        os.remove(self.NEW_H5_AZI)

    def testSingleRB5Vol(self):
        rb52odim.singleRB5(self.GOOD_RB5_VOL,out_fullfile=self.NEW_H5_VOL)
        new_rio = _raveio.open(self.NEW_H5_VOL)
        ref_rio = _raveio.open(self.REF_H5_VOL)
        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_PVOL)
        new_pvol, ref_pvol = new_rio.object, ref_rio.object
        self.assertEqual(new_pvol.getNumberOfScans(), ref_pvol.getNumberOfScans())
        validateTopLevel(self, new_pvol, ref_pvol)
        for i in range(new_pvol.getNumberOfScans()):
            new_scan = new_pvol.getScan(i)
            ref_scan = ref_pvol.getScan(i)
            validateScan(self, new_scan, ref_scan)
        os.remove(self.NEW_H5_VOL)

    def testCombineRB5Files(self):
        rb52odim.combineRB5(self.FILELIST_RB5, out_fullfile=self.NEW_H5_FILELIST)
        new_rio = _raveio.open(self.NEW_H5_FILELIST)
        ref_rio = _raveio.open(self.REF_H5_FILELIST)
        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_SCAN)
        new_scan, ref_scan = new_rio.object, ref_rio.object
        validateTopLevel(self, new_scan, ref_scan)
        validateScan(self, new_scan, ref_scan)
        os.remove(self.NEW_H5_FILELIST)

    def testCombineRB5FilesReturnRIO(self):
        new_rio = rb52odim.combineRB5(self.FILELIST_RB5, return_rio=True)
        ref_rio = _raveio.open(self.REF_H5_FILELIST)
        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_SCAN)
        new_scan, ref_scan = new_rio.object, ref_rio.object
        validateTopLevel(self, new_scan, ref_scan)
        validateScan(self, new_scan, ref_scan)

    def testCombineRB5FromTarball(self):
        rb52odim.combineRB5FromTarball(self.RB5_TARBALL_DOPVOL1B, self.NEW_H5_TARBALL_DOPVOL1B)
        new_rio = _raveio.open(self.NEW_H5_TARBALL_DOPVOL1B)
        ref_rio = _raveio.open(self.REF_H5_TARBALL_DOPVOL1B)
        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_SCAN)
        new_scan, ref_scan = new_rio.object, ref_rio.object
        validateTopLevel(self, new_scan, ref_scan)
        validateScan(self, new_scan, ref_scan)
        os.remove(self.NEW_H5_TARBALL_DOPVOL1B)

    def testCombineRB5FromTarballReturnRIO(self):
        new_rio = rb52odim.combineRB5FromTarball(self.RB5_TARBALL_DOPVOL1B, None, return_rio=True)
        ref_rio = _raveio.open(self.REF_H5_TARBALL_DOPVOL1B)
        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_SCAN)
        new_scan, ref_scan = new_rio.object, ref_rio.object
        validateTopLevel(self, new_scan, ref_scan)
        validateScan(self, new_scan, ref_scan)

    def testMergeOdimScans2Pvol(self):
        rb52odim.combineRB5FromTarball(self.RB5_TARBALL_DOPVOL1A, self.NEW_H5_TARBALL_DOPVOL1A)
        rb52odim.combineRB5FromTarball(self.RB5_TARBALL_DOPVOL1B, self.NEW_H5_TARBALL_DOPVOL1B)
        rb52odim.combineRB5FromTarball(self.RB5_TARBALL_DOPVOL1C, self.NEW_H5_TARBALL_DOPVOL1C)
        FILELIST_H5_TARBALL=[\
            self.NEW_H5_TARBALL_DOPVOL1A,\
            self.NEW_H5_TARBALL_DOPVOL1B,\
            self.NEW_H5_TARBALL_DOPVOL1C,\
            ]
        rio_arr = [_raveio.open(x) for x in FILELIST_H5_TARBALL]
        rb52odim.mergeOdimScans2Pvol(rio_arr, self.NEW_H5_MERGED_PVOL, interval=5, taskname='DOPVOL')
        new_rio = _raveio.open(self.NEW_H5_MERGED_PVOL)
        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_PVOL)
        new_pvol = new_rio.object
        self.assertEqual(new_pvol.getNumberOfScans(), 3)
        validateMergedPvol(self, new_pvol, 0, self.RB5_TARBALL_DOPVOL1A)
        validateMergedPvol(self, new_pvol, 1, self.RB5_TARBALL_DOPVOL1B)
        validateMergedPvol(self, new_pvol, 2, self.RB5_TARBALL_DOPVOL1C)
        
        os.remove(self.NEW_H5_TARBALL_DOPVOL1A)
        os.remove(self.NEW_H5_TARBALL_DOPVOL1B)
        os.remove(self.NEW_H5_TARBALL_DOPVOL1C)
        os.remove(self.NEW_H5_MERGED_PVOL)

    def testCombineRB5Tarballs2Pvol(self):
        ifiles = [self.RB5_TARBALL_DOPVOL1A,
                  self.RB5_TARBALL_DOPVOL1B, 
                  self.RB5_TARBALL_DOPVOL1C]

        # Should not be necessary to write self.NEW_H5_MERGED_PVOL and then
        # read it for validation, but per-scan what/time validation fails if 
        # rio_new is returned in memory and used instead. 
        # This could be a bug in RAVE.
        rb52odim.combineRB5Tarballs2Pvol(ifiles, self.NEW_H5_MERGED_PVOL, 
                                         False, 5, "DOPVOL")
        new_rio = _raveio.open(self.NEW_H5_MERGED_PVOL)
        ref_rio = _raveio.open(self.REF_H5_MERGED_PVOL)
        new_pvol, ref_pvol = new_rio.object, ref_rio.object

        self.assertTrue(new_rio.objectType is _rave.Rave_ObjectType_PVOL)
        self.assertEqual(new_pvol.getNumberOfScans(), 
                          ref_pvol.getNumberOfScans())
        validateTopLevel(self, new_pvol, ref_pvol)
        for i in range(new_pvol.getNumberOfScans()):
            new_scan = new_pvol.getScan(i)
            ref_scan = ref_pvol.getScan(i)
            validateScan(self, new_scan, ref_scan)

        os.remove(self.NEW_H5_MERGED_PVOL)

    def testGunzip(self):
        fstr = rb52odim.gunzip(self.CASRA_AZI_dBZ)
        self.assertTrue(_rb52odim.isRainbow5(fstr))
        os.remove(fstr)

    def testRoundDT(self):
        DATE, TIME = '20171222', '235914'  # input
        refd, reft = '20171223', '000000'  # output
        newd, newt = rb52odim.roundDT(DATE, TIME)
        self.assertTrue(newd, refd)
        self.assertTrue(newt, reft)

    # Somewhat construed way of testing readParameterFiles()
    def testReadParameters(self):
        scan = rb52odim.readParameterFiles([self.CASRA_AZI_dBZ])[0]
        ref = _raveio.open(self.REF_CASRA_H5_SCAN).object
        for pname in ref.getParameterNames():
            if pname != 'DBZH':
                ref.removeParameter(pname)
        validateScan(self, scan, ref)

    def testCompileScanParameters(self):
        scans = rb52odim.readParameterFiles(glob.glob(self.CASRA_AZI))
        oscan = rb52odim.compileScanParameters(scans)
        ref = _raveio.open(self.REF_CASRA_H5_SCAN).object
        validateScan(self, oscan, ref)

    def testCompileVolumeFromVolumes(self):
        volumes = rb52odim.readParameterFiles(glob.glob(self.CASRA_VOL))
        ovolume = rb52odim.compileVolumeFromVolumes(volumes)
        ref = _raveio.open(self.REF_CASRA_H5_PVOL).object
        validateTopLevel(self, ovolume, ref)
        for i in range(ovolume.getNumberOfScans()):
            oscan = ovolume.getScan(i)
            rscan = ref.getScan(i)
            oscan.date, oscan.time = rscan.date, rscan.time # times are not aligned until the pvol is written to disk, so this is a workaround
            validateScan(self, oscan, rscan)

    def testReadRB5(self):
        rio = rb52odim.readRB5([self.CASRA_AZI_dBZ])
        self.assertTrue(rio.objectType, _rave.Rave_ObjectType_SCAN)

    def testCompileVolumeFromVolumes_vs_CombineRB5FilesReturnRIO(self):
        files = glob.glob(self.CASRA_VOL) #unsorted
        ifiles = sorted(files, key=lambda s: s.lower())  # case-insensitive sort
        #Note: compiled/combined scan's Attribute('how/peakpwr') is set by first param encountered!
        #need files sorted as rb52odim.readParameterFiles() contains file sorting!
        volumes = rb52odim.readParameterFiles(ifiles)
        compile_pvol = rb52odim.compileVolumeFromVolumes(volumes, adjustTime=False)
        combine_rio = rb52odim.combineRB5(ifiles, return_rio=True) #no adjustTime() functionality
        combine_pvol = combine_rio.object
        validateTopLevel(self, compile_pvol, combine_pvol)
        for i in range(compile_pvol.getNumberOfScans()):
            compile_scan = compile_pvol.getScan(i)
            combine_scan = combine_pvol.getScan(i)
            validateScan(self, compile_scan, combine_scan)

