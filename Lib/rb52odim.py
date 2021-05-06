'''
Copyright (C) 2017 The Crown (i.e. Her Majesty the Queen in Right of Canada)

This file is an add-on to RAVE.

RAVE is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RAVE and this software are distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with RAVE.  If not, see <http://www.gnu.org/licenses/>.

'''
## Collected functionality for decoding and merging data from Rainbow 5 
# 


## 
# @file
# @author Daniel Michelson and Peter Rodriquez, Environment and Climate Change Canada
# @date 2017-06-14

import sys, os, math, tarfile, mimetypes, gzip, datetime
import _rb52odim
import _rave, _raveio, _polarvolume, _polarscan
import rave_tempfile
from copy import copy

## Define $RAVECONFIG relative to this module
RB52ODIMCONFIG = os.path.abspath(os.path.join(os.path.dirname(_rb52odim.__file__),'..','config'))
os.environ["RB52ODIMCONFIG"] = RB52ODIMCONFIG

ACQUISITION_UPDATE_TIME = 6  # minutes


## Rudimentary input file validation
# @param string input file name
def validate(filename):
    if not os.path.isfile(filename):
        raise IOError("Input file %s is not a regular file. Bailing ..." % filename)
    if os.path.getsize(filename) == 0:
        raise IOError("%s is zero-length. Bailing ..." % filename)


## Gunzips a (Rainbow5) file
# @param string input file name, assumed to have trailing .gz
# @returns string output file name, created by rave_tempfile
def gunzip(fstr):
    #py3 type(payload) is <class 'bytes'>, need to add 'b' read/write mode
    payload = gzip.open(fstr,'rb').read()
    fstr = rave_tempfile.mktemp(close='True')[1]
    fd = open(fstr, 'wb')
    fd.write(payload)
    fd.close()
    return fstr


## Rounds date and time to the nearest acquisition interval (minute past hour),
# assuming it is regular and starting at minute 0.
# @param string date in YYYYMMDD format
# @param string time in HHmmSS format
# @param int update interval in minutes
# @returns tuple containing date and time in the same format as input arguments
def roundDT(DATE, TIME, INTERVAL=ACQUISITION_UPDATE_TIME):
    HINTERVAL = INTERVAL / 2.0
    tm = datetime.datetime(int(DATE[:4]), int(DATE[4:6]), int(DATE[6:8]),
                           int(TIME[:2]), int(TIME[2:4]), int(TIME[4:]))
    tm += datetime.timedelta(minutes=HINTERVAL)
    tm -= datetime.timedelta(minutes=tm.minute % INTERVAL,
                             seconds=tm.second,microseconds=tm.microsecond)
    return tm.strftime('%Y%m%d'), tm.strftime('%H%M%S')


## Reads RB5 files and merges their contents into an output ODIM_H5 file
# @param string file name of input file
# @param string file name of output file
def singleRB5(inp_fullfile, out_fullfile=None, return_rio=False):
    TMPFILE = False
    validate(inp_fullfile)
    orig_ifile = copy(inp_fullfile)
    if mimetypes.guess_type(inp_fullfile)[1] == 'gzip':
        inp_fullfile = gunzip(inp_fullfile)
        TMPFILE = True
    if not _rb52odim.isRainbow5(inp_fullfile):
        raise IOError("%s is not a proper RB5 raw file" % orig_ifile)
    rio = _rb52odim.readRB5(inp_fullfile)
    if TMPFILE: os.remove(inp_fullfile)

    if out_fullfile:
        rio.save(out_fullfile)
    if return_rio:
        return rio


### Functions that do not assume tarballing. Somewhat redundant functionality
### for merging parameters/quantities from individual files/objects.

## Takes individual scan or volume files, each containing only one parameter, 
#  reads then, and appends them to a list. Input files are sorted case-
#  insensitively, so that parameters are (always) ordered consistently in the 
#  output ODIM_H5 files, not that it makes a difference.
# @param list of input file strings
# @returns list containing PolarScanCore objects
def readParameterFiles(ifiles):
    ifiles = sorted(ifiles, key=lambda s: s.lower())  # case-insensitive sort
    objects = []
    for ifile in ifiles:
        try: rio = singleRB5(ifile, return_rio=True)
        except: print("readParameterFiles: failed to read %s" % ifile)
        objects.append(rio.object)
    return objects


## Takes individual scan objects, each containing only one parameter, and 
#  compiles them into a single scan with all parameters.
# @param list of PolarScanCore objects
# @returns PolarScanCore object containing all parameters and metadata
def compileScanParameters(scans):
    # Clone the first scan to act as host for the others
    oscan = scans[0].clone()
    
    for i in range(1, len(scans)):
        scan = scans[i]
        for pname in scan.getParameterNames():  # should only be one
            if pname not in oscan.getParameterNames(): # should not be necessary
                param = scan.getParameter(pname)
                oscan.addParameter(param)

        # Check whether there are any additional attributes in a given scan
        # and add them to the output scan. No checking whether replicate
        # attributes contain the same information.
        anames = oscan.getAttributeNames()
        for aname in scan.getAttributeNames():
            if aname not in anames:
                oscan.addAttribute(aname, scan.getAttribute(aname))
            
        #expand TXpower attributes by single- & dual-pol params
        oscan=expand_txpower_by_pol(oscan,scan,pname)

    return oscan


## Compiles a multi-parameter volume from several single-parameter volumes.
#  ASSUMES that the input files are all from the same data acquisition, that
#  the scan strategies are identical, so no advanced validation is required.
#  This function is deliberately structured to pair with 
#  \ref compileScanParameters
# @param list of input PolarVolumeCore objects
# @return PolarVolumeCore object
def compileVolumeFromVolumes(volumes, adjustTime=True):
    # Use the first volume to act as host for the others. Start by removing its 
    # scans but preserving its top-level metadata attributes
    ovolume = volumes[0].clone()  # If we don't clone, we mess up the original
    nscans = ovolume.getNumberOfScans()
    while 1:
        try: ovolume.removeScan(0)
        except: break

    # Second iteration, pull out scans, merge their parameters, and add the 
    # multi-parameter scan to the output volume
    for i in range(nscans):
        scans = []
        for volume in volumes:
            scans.append(volume.getScan(i))
        oscan = compileScanParameters(scans)
        ovolume.addScan(oscan)

    # Last loop, check whether there are any additional attributes at the top
    # level in any of the input volumes. No checking whether replicate 
    # attributes contain the same information.
    anames = ovolume.getAttributeNames()
    for volume in volumes:
        for aname in volume.getAttributeNames():
            if aname not in anames:
                ovolume.addAttribute(aname, volume.getAttribute(aname))

    # Adjust to closest nomimal time
    if adjustTime:
        if ovolume.isAscendingScans():
            ovolume.date, ovolume.time  = roundDT(ovolume.date, ovolume.time)
        else:
            lowest = ovolume.getScanClosestToElevation(-90.0, 0)
            ovolume.date, ovolume.time  = roundDT(lowest.enddate, lowest.endtime)

    return ovolume


## Generates a volume from scans, based on rave_pgf_volume_plugin.generateVolume
# @param list of input PolarScanCore objects
# @return PolarVolumeCore object
def compileVolumeFromScans(scans, adjustTime=True):
    if len(scans) <= 0:
        raise AttributeError("Volume must consist of at least 1 scan")

    firstscan=False  
    volume = _polarvolume.new()

    #'longitude', 'latitude', 'height', 'time', 'date', 'source', 'beamwidth', 'beamwH', beamwV'
    #rave-py3/modules/pypolarscan.c:1712 beamwidth - DEPRECATED, Use beamwH!

    for scan in scans:
        if firstscan == False:
            firstscan = True
            volume.longitude = scan.longitude
            volume.latitude = scan.latitude
            volume.height = scan.height
            volume.beamwidth = scan.beamwidth
            if(hasattr(scan,'beamH')): volume.beamwH = scan.beamwH
            if(hasattr(scan,'beamV')): volume.beamwV = scan.beamwV
        volume.addScan(scan)

    volume.source = scan.source  # Recycle the last input, it won't necessarily be correct ...
    odim_source.CheckSource(volume)    # ... so check it!
 
    # Adjust to closest nomimal time
    if adjustTime:
        if volume.isAscendingScans():
            volume.date, volume.time  = roundDT(volume.date, volume.time)
        else:
            lowest = volume.getScanClosestToElevation(-90.0, 0)
            volume.date, volume.time  = roundDT(lowest.enddate, lowest.endtime)
    return volume


## High-level function for reading multiple input data files and merging them
#  into either a scan or volume. The first object in the list will be read and
#  its object type queried. This will determine whether the object being merged
#  is a scan or a volume.
# @param list containing input file strings
# @returns RaveIOCore object
def readRB5(filenamelist):
    objects = readParameterFiles(filenamelist)
    rio = _raveio.new()
    if _polarscan.isPolarScan(objects[0]):
        rio.object = compileScanParameters(objects)
    elif _polarvolume.isPolarVolume(objects[0]):
        rio.object = compileVolumeFromVolumes(objects)
    return rio


### Functions that assume input data are tarballed

## Reads RB5 files and merges their contents into an output ODIM_H5 file
# @param string list of input file names
# @param string output file name
# @param Boolean if True, return the RaveIOCore object containing the decoded and merged RB5 data
# @returns RaveIOCore if return_rio=True, otherwise nothing
def combineRB5(ifiles, out_fullfile=None, return_rio=False):
    big_obj=None

    nMEMBERs=len(ifiles)
    for iMEMBER in range(nMEMBERs):
        inp_fullfile=ifiles[iMEMBER]
        validate(inp_fullfile)
        mb=parse_tarball_member_name(inp_fullfile,ignoredir=True)

        if mb['rb5_ftype'] == "rawdata":
            rio=singleRB5(inp_fullfile, return_rio=True) ## w/ isRainbow5() check and handles .gz
            this_obj=rio.object
            if rio.objectType == _rave.Rave_ObjectType_PVOL:
                big_obj=compile_big_pvol(big_obj,this_obj,mb,iMEMBER)
            else:
                big_obj=compile_big_scan(big_obj,this_obj,mb)
    
    container=_raveio.new()
    container.object=big_obj
    if out_fullfile:
        container.save(out_fullfile)
    if return_rio:
        return container


## Reads a single RB5 tarball and merges its contents into an output ODIM_H5 file
# @param string input tarball file name
# @param string output file name
# @param string output base directory, only used when creating new output file name  
# @param Boolean if True, return the RaveIOCore object containing the decoded and merged RB5 data
# @returns RaveIOCore if return_rio=True, otherwise nothing
def combineRB5FromTarball(ifile, ofile, out_basedir=None, return_rio=False):
    validate(ifile)
    big_obj=None

    tar=tarfile.open(ifile)
    member_arr=tar.getmembers()
    nMEMBERs=len(member_arr)
    for iMEMBER in range(nMEMBERs):
        this_member=member_arr[iMEMBER]
        inp_fullfile=this_member.name
        mb=parse_tarball_member_name(inp_fullfile)

#XAH DPATC_replay: Special filter out for ZPHI_ITER_DEFAULT.dpatc & ZDR
        if (
            (mb['rb5_ftype'] == "rawdata") and
            not ((mb['rb5_ppdf'] == "ZPHI_ITER_DEFAULT.dpatc") and
                 (mb['nam_sparam'] == "ZDR"))
            ):

#        if mb['rb5_ftype'] == "rawdata":
            obj_mb=tar.extractfile(this_member) #EXTRACTED MEMBER OBJECT

            rb5_buffer=obj_mb.read() #NOTE: once read(), buffer is detached from obj_mb
            isrb5=_rb52odim.isRainbow5buf(rb5_buffer)
            if not isrb5:
                raise IOError("%s is not a proper RB5 buffer" % rb5_buffer)
            else:
                buffer_len=len(rb5_buffer)
#                print('### inp_fullfile = %s (%ld)' % (inp_fullfile,  buffer_len))
                rio=_rb52odim.readRB5buf(inp_fullfile,rb5_buffer,buffer_len) ## by BUFFER
                this_obj=rio.object

                if rio.objectType == _rave.Rave_ObjectType_PVOL:
                    big_obj=compile_big_pvol(big_obj,this_obj,mb,iMEMBER)
                else:
                    big_obj=compile_big_scan(big_obj,this_obj,mb)

    #auto output filename (as needed)
    if not ofile and not return_rio:
        tb=parse_tarball_name(ifile)
        out_basefile=".".join([\
            tb['nam_site'],\
            tb['nam_timestamp'],\
            tb['nam_sdf'],\
            'h5'\
            ])
        out_fulldir=os.path.join(\
            out_basedir,\
            tb['nam_site'],\
            tb['nam_date'],\
            tb['nam_sdf']\
            )
        if not os.path.exists(out_fulldir):
            os.makedirs(out_fulldir)
        out_fullfile=os.path.join(out_fulldir,out_basefile)
    else:
        out_fullfile=ofile

    container=_raveio.new()
    container.object=big_obj
    if out_fullfile:
        container.save(out_fullfile)
    if return_rio:
        return container


## Read multiple RB5 scan tarballs and output a single ODIM_H5 PVOL file or, alternatively, a RaveIOCore object. This is a simple wrapper for reading the input data required by \ref mergeOdimScans2Pvol
# @param list of input tarball files, each containing RB5 sweep moment files
# @param string output file name
# @param Boolean if True, return the RaveIOCore object containing the merged ODIM data
# @param string cycle time interval in minutes
# @param string combined task name
# @returns RaveIOCore if return_rio=True, otherwise nothing
def combineRB5Tarballs2Pvol(ifiles, out_fullfile=None, return_rio=False, interval=None, taskname=None):
    rio_arr = []

    for ifile in ifiles:
        validate(ifile)
        rio = combineRB5FromTarball(ifile, None, None, True)
        if rio: rio_arr.append(rio)

    return mergeOdimScans2Pvol(rio_arr, out_fullfile, return_rio, interval, taskname)


## Merge multiple ODIM_H5 SCAN contents into an output ODIM_H5 PVOL file or, alternatively, a RaveIOCore object
# @param list of RaveIOCore objects (ODIM_H5 SCANs)
# @param string output file name
# @param Boolean if True, return the RaveIOCore object containing the merged ODIM data
# @param string cycle time interval in minutes
# @param string combined task name
# @returns RaveIOCore if return_rio=True, otherwise nothing
def mergeOdimScans2Pvol(rio_arr, out_fullfile=None, return_rio=False, interval=None, taskname=None):
    pvol=None

    if not interval:
        interval=5
    if not taskname:
        taskname='dummy'

    nSCANs=len(rio_arr)
    for iSCAN in range(nSCANs):
        rio=rio_arr[iSCAN]

        if rio.objectType != _rave.Rave_ObjectType_SCAN:
            raise IOError("Expecting obj_SCAN not : %s" % type(rio.object))
        else:
            scan=rio.object
            #scan.getAttributeNames()
            #print(scan.getAttribute('how/task'))

            if pvol is None: #clone
                pvol=_polarvolume.new()
                pvol.source=scan.source
                import datetime as dt
                scan_iso8601="-".join([scan.date[0:4],scan.date[4:6],scan.date[6:9]])+"T"+\
                             ":".join([scan.time[0:2],scan.time[2:4],scan.time[4:7]])
                scan_systime=float(dt.datetime.strptime(scan_iso8601,'%Y-%m-%dT%H:%M:%S').strftime("%s"))
                cycle_nsecs=float(interval)*60.
                cycle_systime=scan_systime - scan_systime%cycle_nsecs
                cycle_iso8601=dt.datetime.fromtimestamp(cycle_systime).isoformat()

                pvol.date=''.join(cycle_iso8601[:10].split('-'))
                pvol.time=''.join(cycle_iso8601[11:].split(':'))
                pvol.longitude=scan.longitude
                pvol.latitude=scan.latitude
                pvol.height=scan.height
                #rave-py3/modules/pypolarscan.c:1712 beamwidth - DEPRECATED, Use beamwH!
                pvol.beamwidth=scan.beamwidth
                if(hasattr(scan,'beamH')): pvol.beamwH = scan.beamwH
                if(hasattr(scan,'beamV')): pvol.beamwV = scan.beamwV

                pvol.addAttribute("how/task", taskname)
       	        for s_attrib in [
                    "how/TXtype",
                    "how/beamwH", #optional
                    "how/beamwV", #optional
                    "how/polmode",
                    "how/poltype",
                    "how/software",
                    "how/sw_version",
                    "how/system",
                    "how/wavelength",
                    ]:
                    if s_attrib in scan.getAttributeNames():
                        pvol.addAttribute(s_attrib, scan.getAttribute(s_attrib))

            pvol.addScan(scan)

    container=_raveio.new()
    container.object=pvol
    if out_fullfile:
        container.save(out_fullfile)
    if return_rio:
        return container


### Convenience functions follow ###


def parse_tarball_name(fullfile):
    fulldir=os.path.dirname(fullfile)
    basefile=os.path.basename(fullfile)
    elem_arr=basefile[:-len('.tar.gz')].split("_")
    nELEMs=len(elem_arr)
    nam_site=elem_arr[0]
    nam_yyyymmddhhmm=elem_arr[1]
    nam_iso8601=nam_yyyymmddhhmm[ 0: 4]+'-'+\
                nam_yyyymmddhhmm[ 4: 6]+'-'+\
                nam_yyyymmddhhmm[ 6: 8]+' '+\
                nam_yyyymmddhhmm[ 8:10]+':'+\
                nam_yyyymmddhhmm[10:12]+':00'
    nam_date=nam_iso8601[0:10]
    nam_hhmmZ=nam_yyyymmddhhmm[8:12]+'Z'
    nam_timestamp=nam_date+'_'+nam_hhmmZ
    nam_sdf="_".join(elem_arr[2:])

    return{\
        'fullfile':fullfile,\
        'fulldir': fulldir,\
        'basefile':basefile,\
        'nam_site':nam_site,\
        'nam_yyyymmddhhmm':nam_yyyymmddhhmm,\
        'nam_iso8601':nam_iso8601,\
        'nam_date':nam_date,\
        'nam_hhmmZ':nam_hhmmZ,\
        'nam_timestamp':nam_timestamp,\
        'nam_sdf':nam_sdf\
        }


def parse_tarball_member_name(fullfile,ignoredir=False):
    fulldir=os.path.dirname(fullfile)
    basefile=os.path.basename(fullfile).split('_')[-1] #strip 'sSITE_' prefix, not part of tarball member syntax
    nam_yyyymmddhhmmss=basefile[0:14]
    nam_iso8601=nam_yyyymmddhhmmss[ 0: 4]+'-'+\
                nam_yyyymmddhhmmss[ 4: 6]+'-'+\
                nam_yyyymmddhhmmss[ 6: 8]+' '+\
                nam_yyyymmddhhmmss[ 8:10]+':'+\
                nam_yyyymmddhhmmss[10:12]+':'+\
                nam_yyyymmddhhmmss[12:14]
    nam_file_ver=basefile[14:16]
    dot_loc=basefile.find(".")
    nam_sparam=basefile[16:dot_loc]
    nam_scan_type=basefile[dot_loc+1:]

    if bool(ignoredir):
        rb5_date=""
        rb5_sdf=""
        rb5_ppdf=""
        rb5_site=""
        rb5_ftype="rawdata"
    else:
        elem_arr=fulldir.split("/")
        nELEMs=len(elem_arr)
        rb5_date=elem_arr[nELEMs-1]
        rb5_sdf=elem_arr[nELEMs-2]
        if not rb5_sdf.endswith(nam_scan_type): #check for ppdf
            rb5_ppdf=rb5_sdf
            rb5_sdf="" #unknown until decode
        else:
            rb5_ppdf=""
        rb5_site=elem_arr[nELEMs-3]
        rb5_ftype=elem_arr[nELEMs-4]

    return {\
        'fullfile':fullfile,\
        'fulldir':fulldir,\
        'basefile':basefile,\
        'nam_yyyymmddhhmmss':nam_yyyymmddhhmmss,\
        'nam_iso8601':nam_iso8601,\
        'nam_file_ver':nam_file_ver,\
        'nam_sparam':nam_sparam,\
        'nam_scan_type':nam_scan_type,\
        'rb5_date':rb5_date,\
        'rb5_sdf':rb5_sdf,\
        'rb5_ppdf':rb5_ppdf,\
        'rb5_site':rb5_site,\
        'rb5_ftype':rb5_ftype,\
        }


def compile_big_scan(big_scan,scan,mb):
    sparam_arr=scan.getParameterNames()
    #assume 1 param per scan of input tar_member
    if len(sparam_arr) != 1 :
        raise IOError('Too many sparams: %s' % sparam_arr)
        return

    sparam=sparam_arr[0]
    param=scan.getParameter(sparam)
#    print('sparam',sparam)






    if big_scan is None:
        big_scan=scan.clone() #clone
        big_scan.removeParameter(sparam) #remove existing param

    if mb['rb5_ppdf'] != "":
        old_sparam=sparam
        rb5_ppdf=mb['rb5_ppdf']
        new_sparam=old_sparam+rb5_ppdf[rb5_ppdf.find("."):]
        scan.removeParameter(old_sparam) #make orphan
        param.quantity=new_sparam #update orphan
        scan.addParameter(param) #add orphan
        sparam=new_sparam #update sparam

#    big_sparam_arr=big_scan.getParameterNames()
#    print('big_sparam_arr',big_sparam_arr)
    #WARNING : Different number of rays/bins for various parameters are not allowed (polarscan.c:566)
    #*** AttributeError: Failed to add parameter to scan
    #check sorting of scans
    big_scan.addParameter(param) #add

    #expand TXpower attributes by single- & dual-pol params
    big_scan=expand_txpower_by_pol(big_scan,scan,sparam)

    return big_scan


def expand_txpower_by_pol(oscan,scan,sparam):
    import re
    dual_pol_param_list=('ZDR RHOHV PHIDP KDP'    ).split(' ')
    sing_pol_param_list=('T DBZ VRAD WRAD SNR SQI').split(' ')
    if      any(re.match('(U)?'+pattern ,sparam) for pattern in dual_pol_param_list) \
    and not any(re.match(pattern+'(H|V)',sparam) for pattern in sing_pol_param_list):
        aprefix='dual-pol_'
    else:
        aprefix='single-pol_'

    anames = oscan.getAttributeNames()
    aroot_list=('TXpower peakpwr avgpwr').split(' ')
    for aroot in aroot_list:
        org_aname='how/'+aroot
        new_aname='how/'+aprefix+aroot
        if new_aname not in anames:
            oscan.addAttribute(new_aname,scan.getAttribute(org_aname))

    return oscan


def compile_big_pvol(big_pvol,pvol,mb,iMEMBER):
    nSCANs=pvol.getNumberOfScans()
    if big_pvol is None: #clone
        big_pvol=pvol.clone()

    for iSCAN in range(nSCANs):
        if iMEMBER == 0:
            big_scan=None #begin with empty scans (removes existing param)
        else:
            big_scan=big_pvol.getScan(iSCAN)
#            print('big_scan',iSCAN,np.degrees(big_scan.elangle),big_scan.nrays,big_scan.nbins)
        this_scan=pvol.getScan(iSCAN)
#        print('this_scan',iSCAN,np.degrees(this_scan.elangle),this_scan.nrays,this_scan.nbins)
        big_scan=compile_big_scan(big_scan,this_scan,mb)
        big_pvol.removeScan(iSCAN)
        big_pvol.addScan(big_scan)
        big_pvol.sortByElevations(pvol.isAscendingScans()) # resort inside scan loop to match input pvol order

    return big_pvol


if __name__=="__main__":
    pass
