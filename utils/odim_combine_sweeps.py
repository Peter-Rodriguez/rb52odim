#!/usr/bin/env python
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
## Command-line utility for combining multiple ODIM_H5 SCAN files into a single
#  ODIM_H5 PVOL file.

## 
# @file
# @author Daniel Michelson and Peter Rodriguez, Environment and Climate Change Canada
# @date 2017-06-09

#NOTE this code is the basis for ../Lib/rb52odim.py:mergeOdimScans2Pvol()

import sys, os, errno
import _rave, _raveio, _polarvolume

## Ingests multiple ODIM_H5 SCAN files and merges their contents into an output ODIM_H5 PVOL file
# @param optparse.OptionParser object
def combine(options):
    pvol=None

    sweep_arr=options.ifiles.split(",")
    nSWEEPs=len(sweep_arr)
    for iSWEEP in range(nSWEEPs):
        fullfile=sweep_arr[iSWEEP]
        rio=_raveio.open(fullfile)

        if rio.objectType != _rave.Rave_ObjectType_SCAN:
            print("Expecting input components to be obj_SCAN not : %s" % type(rio.object))
            exit()
        else:
            scan=rio.object
            #scan.getAttributeNames()
            #print(scan.getAttribute('how/task'))
            #import pdb; pdb.set_trace()

            if pvol is None: #clone
                pvol=_polarvolume.new()
                pvol.source=scan.source
                import datetime as dt
                scan_iso8601="-".join([scan.date[0:4],scan.date[4:6],scan.date[6:9]])+"T"+\
                             ":".join([scan.time[0:2],scan.time[2:4],scan.time[4:7]])
                scan_systime=float(dt.datetime.strptime(scan_iso8601,'%Y-%m-%dT%H:%M:%S').strftime("%s"))
                cycle_nsecs=float(options.interval)*60.
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

                pvol.addAttribute("how/task", options.taskname)
                for s_attrib in [
                    "how/TXtype",
#not in REF                    "how/beamwH", #optional
#not in REF                    "how/beamwV", #optional
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

    out_fullfile=options.ofile
    container=_raveio.new()
    container.object=pvol
    container.save(out_fullfile)
    print("Created : %s" % out_fullfile)


if __name__=="__main__":
    from optparse import OptionParser

    usage = "usage: %prog -i <input ODIM_H55 SCAN files> -o <output ODIM_H5 PVOL file> -c <cycle time interval in minutes> -t <combined task name> [h]"
    parser = OptionParser(usage=usage)

    parser.add_option("-i", "--input", dest="ifiles",
                      help="Sequence of comma-separated input ODIM_H5 SCAN file names. No white spaces allowed.")

    parser.add_option("-o", "--output", dest="ofile",
                      help="Output ODIM_H5 PVOL file name.")

    parser.add_option("-c", "--cycle_time_interval_mins", dest="interval",
                      help="Output ODIM_H5 file name.")

    parser.add_option("-t", "--task_name", dest="taskname",
                      help="Combined task name.")

    (options, args) = parser.parse_args()

    if not options.ifiles or \
       not options.ofile or \
       not options.interval or \
       not options.taskname:
        parser.print_help()
        sys.exit(errno.EINVAL)        

    if options.ifiles:

        # Rudimentary input file validation
        fstrs = options.ifiles.split(",")
        for fstr in fstrs:
            if not os.path.isfile(fstr):
                print("%s is not a regular file. Bailing ..." % fstr)
                sys.exit(errno.ENOENT)
            if os.path.getsize(fstr) == 0:
                print("%s is zero-length. Bailing ..." % fstr)
                sys.exit(-1)

    combine(options)
