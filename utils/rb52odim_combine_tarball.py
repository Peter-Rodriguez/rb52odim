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
# @date 2017-06-07

# NOTE: this code is the basis for ../Lib/rb52odim.py:combineRB5FromTarball()

# Peter, 2020-Dec-10
# Let's be independent to ${RAVEROOT}=/opt/baltrad, for example
import sys
sys.path.insert(1,'../Lib/')
sys.path.insert(1,'../modules/')

import sys, os, errno
import _rave, _raveio

import _rb52odim #Note using ../modules/_rb52odim.so#
# NOTE: but baked w/ /opt/baltrad/rave/lib/librb52odim.so?
# NOTE: fixed make install w/ chmod 775
from rb52odim import * #Note using ../Lib/rb52odim.py

import tarfile

## Reads RB5 files and merges their contents into an output ODIM_H5 file
# @param optparse.OptionParser object
def combine(options):
    tarball_fullfile=options.ifile
    print("Opening : %s" % tarball_fullfile)
    tb=parse_tarball_name(tarball_fullfile)

    big_obj=None

    tar=tarfile.open(tarball_fullfile)
    member_arr=tar.getmembers()
    nMEMBERs=len(member_arr)
    for iMEMBER in range(nMEMBERs):
        this_member=member_arr[iMEMBER]
        inp_fullfile=this_member.name
        mb=parse_tarball_member_name(inp_fullfile)

        if mb['rb5_ftype'] == "rawdata":
            obj_mb=tar.extractfile(this_member) #EXTRACTED MEMBER OBJECT
#            isrb5=_rb52odim.isRainbow5buf(obj_mb) #alternately arg is an OBJ
#            print("isrb5 = %s" % isrb5)

            rb5_buffer=obj_mb.read() #NOTE: once read(), buffer is detached from obj_mb
            isrb5=_rb52odim.isRainbow5buf(rb5_buffer)
            print("Processing : %s" % inp_fullfile)
            if not isrb5:
                print('Hmm, not a proper RB5 raw file I can handle')
                exit()
            else:
                buffer_len=obj_mb.size
                rio=_rb52odim.readRB5buf(inp_fullfile,rb5_buffer,buffer_len) ### by BUFFER
#                rio=_rb52odim.readRB5(inp_fullfile) ## by FILENAME
                this_obj=rio.object
#                print(type(this_obj))
#                print(this_obj.getAttributeNames())
#                import pdb; pdb.set_trace()
#                print(this_obj.getAttribute('how/RXlossV')) #optional
                if rio.objectType == _rave.Rave_ObjectType_PVOL:
                    big_obj=compile_big_pvol(big_obj,this_obj,mb,iMEMBER)
#                    print("  ODIM params : %s" % big_obj.getScan(0).getParameterNames())
                else:
                    big_obj=compile_big_scan(big_obj,this_obj,mb)
#                    print(" ODIM params : %s" % big_obj.getParameterNames())

    if not options.ofile:
        out_basefile=".".join([\
            tb['nam_site'],\
            tb['nam_timestamp'],\
            tb['nam_sdf'],\
            'h5'\
            ])
        out_basedir=options.obasedir
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
        out_fullfile=options.ofile

    container=_raveio.new()
    container.object=big_obj
    container.save(out_fullfile)
    print("Created : %s" % out_fullfile)


if __name__=="__main__":
    from optparse import OptionParser

    usage = "usage: %prog -i <input RB5 files> -o <output ODIM_H5 file> -b <output base dir for default out_filenaming> [h]"
    parser = OptionParser(usage=usage)

    parser.add_option("-i", "--input", dest="ifile",
                      help="Input Rainbow 5 tarball name.")

    parser.add_option("-o", "--output", dest="ofile",
                      help="Output ODIM_H5 file name.")

    parser.add_option("-b", "--output_base_dir", dest="obasedir",
                      help="Output base directory for default out_filenaming.")

    (options, args) = parser.parse_args()

    if not options.ifile:
        parser.print_help()
        sys.exit(errno.EINVAL)        

    if not options.ofile:
        print("Output file not specified. Defaulting to SITE/yyyy-mm-dd/SDF/SITE.yyyy-mm-dd_hhmmZ.SDF.h5")
        if not options.obasedir:
            print("Output base dir not specified. Defaulting.")
            options.obasedir="."
        print("Output base dir = %s" % options.obasedir)
        
    if options.ifile:

        # Rudimentary input file validation
        fstr = options.ifile
        if not os.path.isfile(fstr):
            print("%s is not a regular file. Bailing ..." % fstr)
            sys.exit(errno.ENOENT)
        if os.path.getsize(fstr) == 0:
            print("%s is zero-length. Bailing ..." % fstr)
            sys.exit(-1)

    combine(options)
