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
## Command-line utility for combining Rainbow 5 sweeps or volumes into a single
#  ODIM_H5 file.

## 
# @file
# @author Daniel Michelson and Peter Rodriguez, Environment and Climate Change Canada
# @date 2017-06-09

# NOTE: this code is the basis for ../Lib/rb52odim.py:combineRB5()

# Peter, 2020-Dec-10
# force use of LOCAL copy of rb52odim.py
# Let's be independent from ${RAVEROOT}=/opt/baltrad, for example
import sys
sys.path.insert(1,'../Lib/')
sys.path.insert(1,'../modules/')

import sys, os, errno
import _rave, _raveio

#import _rb52odim #Note using ../modules/_rb52odim.so
from rb52odim import * #Note using ../Lib/rb52odim.py

## Reads RB5 files and merges their contents into an output ODIM_H5 file
# @param optparse.OptionParser object
def combine(options):
    big_obj=None

    member_arr=options.ifiles.split(",")
    nMEMBERs=len(member_arr)
    for iMEMBER in range(nMEMBERs):
        inp_fullfile=member_arr[iMEMBER]
        validate(inp_fullfile)
        mb=parse_tarball_member_name(inp_fullfile,ignoredir=True)

#        import pdb; pdb.set_trace()
        if mb['rb5_ftype'] == "rawdata":
#            isrb5=_rb52odim.isRainbow5(inp_fullfile)
#            print("Processing : %s" % inp_fullfile)
#            if not isrb5:
#                print('Hmm, not a proper RB5 raw file I can handle')
#                exit()
#            else:
            if True:
#                rio=_rb52odim.readRB5(inp_fullfile) ## by FILENAME (cannot handle .gz)
                rio=singleRB5(inp_fullfile, return_rio=True) ## ../../Lib/rb52odim.py (OK w/ .gz)
                this_obj=rio.object
#                print(type(this_obj))
                if rio.objectType == _rave.Rave_ObjectType_PVOL:
                    big_obj=compile_big_pvol(big_obj,this_obj,mb,iMEMBER)
                    print("  ODIM params : %s" % big_obj.getScan(0).getParameterNames())
                else:
                    big_obj=compile_big_scan(big_obj,this_obj,mb)
                    print(" ODIM params : %s" % big_obj.getParameterNames())
    
    out_fullfile=options.ofile
    container=_raveio.new()
    container.object=big_obj
    container.save(out_fullfile)
    print("Created : %s" % out_fullfile)


if __name__=="__main__":
    from optparse import OptionParser

    usage = "usage: %prog -i <input RB5 files> -o <output ODIM_H5 file> [h]"
    parser = OptionParser(usage=usage)

    parser.add_option("-i", "--input", dest="ifiles",
                      help="Sequence of comma-separated input Rainbow 5 file names. No white spaces allowed.")

    parser.add_option("-o", "--output", dest="ofile",
                      help="Output ODIM_H5 file name.")

    (options, args) = parser.parse_args()

    if not options.ifiles or not options.ofile:
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
