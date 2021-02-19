#!/usr/bin/env python
'''
Copyright (C) 2016 The Crown (i.e. Her Majesty the Queen in Right of Canada)

This file is part of RAVE.

RAVE is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RAVE is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with RAVE.  If not, see <http://www.gnu.org/licenses/>.

'''
## Converts odim_source.xml to odim_radar_table.xml, option to merge auxillary odim_radar_table
#


##
# @file
# @author Peter Rodriguez, Environment and Climate Change Canada
# @date 2020-09-30

import os,sys,re
progname=os.path.basename(__file__)
#log_file='{0}.log'.format(progname)

from datetime import datetime
bgn_timestamp='{0}'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

import logging
def setup_logging_to(log_file=None):
    # create root logger
    logger=logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # create console handler
    clogh=logging.StreamHandler()
    clogh.setLevel(logging.INFO)
    logger.addHandler(clogh)
    # create log_file handler
    if log_file:
        print('Logging to : {0}'.format(log_file))
        flogh=logging.FileHandler(log_file,mode='w')
        flogh.setLevel(logging.INFO)
        logger.addHandler(flogh)
    return logger

def main(options):
    log_file=options.log_file
    logger=setup_logging_to(log_file=log_file)
    logger.info('Running {0} @ {1}'.format(progname,bgn_timestamp))

    #odim_source_file='odim_source.rave_ec.2020-09.xml'
    odim_source_file=options.inp_file
    sBGN_SOURCE_CANADA='<ca CCCC="CWAO" org="53">'
    sEND_SOURCE_CANADA='</ca>'

    #odim_table_file='odim_radar_table.xml'
    odim_table_file=options.out_file
    sINDENT='    ' #4-spaces
    table_ver='1.0'
    table_author='Peter Rodriguez'
    table_updated=bgn_timestamp[:10]
    out_fp=open(odim_table_file,'w')
    out_fp.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out_fp.write('<table ver="{0}" author="{1}" updated="{2}">\n'.format(table_ver,table_author,table_updated))

    #L_MERGE=True
    #to_merge_odim_table_file='odim_radar_table.STB_research_Xbands.xml'
    L_MERGE=options.merge_file is not None
    to_merge_odim_table_file=options.merge_file
    sBGN_MERGE_TABLE='<table'
    sEND_MERGE_TABLE='</table>'

    from collections import OrderedDict
    ordered_dict_keys=[\
        'radar_id'    ,\
        'bgn_date'    ,\
        'end_date'    ,\
        'label'       ,\
        'operator'    ,\
        'band'        ,\
        'odim_node'   ,\
        'locale'      ,\
        'admin_state' ,\
        'country'     ,\
        'wmo_id'      ,\
        'rf_call_sign',\
        'make'        ,\
        'model'       ,\
        'serial'      ,\
        'txtype'      ,\
        'poltype'     ,\
        'comment'     ,\
    ]
    dict_radar_template=OrderedDict((key,'') for key in ordered_dict_keys)
    dict_radar_template['operator']='NRP'
    dict_radar_template['country' ]='Canada'
    dict_radar_template['make'    ]='Leonardo/Rainbow5'
    dict_radar_template['comment' ]='Entry from : '+odim_source_file

    dict_Sband=dict_radar_template.copy()
    dict_Sband['band'   ]='S'
    dict_Sband['model'  ]='1700S'
    dict_Sband['txtype' ]='klystron'
    dict_Sband['poltype']='simultaneous-dual'

    dict_Xband=dict_radar_template.copy()
    dict_Xband['band'   ]='X'
    dict_Xband['model'  ]='60DX'
    dict_Xband['txtype' ]='magnetron'
    dict_Xband['poltype']='simultaneous-dual'

    # functionality removed... all cax ids assumed to be Rainbow systems for rb52odim usage
    #
    # not output to odim_table_file
    #NRP_exception_X_ids=['ca'+s for s in ['xra','xsi','xsm','xss','xti','xwl']] #pre-CWRRP, these are Cbands
    #dict_Cband=dict_radar_template.copy()
    #dict_Cband['band'   ]='C'
    #dict_Cband['make'   ]='Vaisala/IRIS'
    #dict_Cband['model'  ]=''
    #dict_Cband['txtype' ]='magnetron'
    #dict_Cband['poltype']='single'

    with open(odim_source_file,'r') as fp:
        match=False
        for line in fp:
            if sBGN_SOURCE_CANADA in line:
                match=True
                sOUT='<!-- Converted : {0} -->'.format(odim_source_file)
                logger.info(sOUT)
                out_fp.write(sOUT+'\n')
                continue
            elif sEND_SOURCE_CANADA in line:
                match=False
                continue
            elif match:
                logger.info(line.rstrip())
                (node,plc)=list(filter(None,re.split('<| plc="|">.*',line.strip())))
                (locale,admin_state)=plc.rsplit(' ',1)
                this_dict_radar=None
                if node[2] == 's':
                    this_dict_radar=dict_Sband.copy()
                elif node[2] == 'x':
                    #if node not in NRP_exception_X_ids:
                        this_dict_radar=dict_Xband.copy()
                if this_dict_radar:
                    this_dict_radar['radar_id'   ]=node.upper()
                    this_dict_radar['odim_node'  ]=node
                    this_dict_radar['locale'     ]=locale
                    this_dict_radar['admin_state']=admin_state
                    this_dict_radar['label'      ]='{band}-band at {locale}, {admin_state} ({operator})' \
                                                   .format(**this_dict_radar)
                    out_fp.write('{0}<radar id="{radar_id}" bgn_date="{bgn_date}" end_date="{end_date}">\n' \
                        .format(sINDENT,**this_dict_radar))
                    for key in ordered_dict_keys[3:]:
                        out_fp.write('{0}{1}<{2}>{3}</{2}>\n'.format(sINDENT,sINDENT,key,this_dict_radar[key]))
                    out_fp.write('{0}</radar>\n'.format(sINDENT))

    if L_MERGE:
        merge_content_arr=[]
        with open(to_merge_odim_table_file,'r') as fp:
            match=False
            for line in fp:
                if sBGN_MERGE_TABLE in line:
                    match=True
                    sOUT='<!-- Merged : {0} -->'.format(to_merge_odim_table_file)
                    logger.info(sOUT)
                    out_fp.write(sOUT+'\n')
                    continue
                elif sEND_MERGE_TABLE in line:
                    match=False
                    continue
                elif match:
                    if '<radar id=' in line: logger.info(line.rstrip())
                    merge_content_arr.append(line.rstrip())
        for sOUT in merge_content_arr:
            out_fp.write(sOUT+'\n')

    out_fp.write('</table>\n')
    out_fp.write('<!-- END XML -->\n')
    logger.info('Created : {0}'.format(odim_table_file))
    logger.info('To be installed as ../../config/odim_radar_table.xml')

###################################################################################################

if __name__ == "__main__":
    from optparse import OptionParser

    usage  = "\n  %prog -i <inp_file> -o <out_file> [-m <merge_file>] [-l <log_file>] [h]"
    usage += "\n\nDescription:"
    usage += "\n  Converts odim_source.xml to odim_radar_table.xml (for use by rb52odim decode module)"
    usage += "\n Option --merge_file, to merge auxillary odim_radar_table.xml file."
    usage += "\n\nExample:"
    usage += "\n  %prog -i odim_source.rave_ec.2020-09.xml -m odim_radar_table.STB_research_Xbands.xml -o odim_radar_table.rave_ec.2020-09.xml -l my_log.txt"

    parser = OptionParser(usage=usage)

    parser.add_option("-i", "--inp_file", dest="inp_file",
                      help="Name of input 'odim_source.xml' file.")

    parser.add_option("-o", "--out_file", dest="out_file",
                      help="Name of output file to write.")

    parser.add_option("-m", "--merge_file", dest="merge_file",
                      help="Name of input 'odim_radar_table.xml' file to merge.")

    parser.add_option("-l", "--log_file", dest="log_file",
                      help="Name of log file to write.")

    (options, args) = parser.parse_args()

    if not options.inp_file or not options.out_file:
        parser.print_help()
        sys.exit()

    main(options)
