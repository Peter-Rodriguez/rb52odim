/* --------------------------------------------------------------------
Copyright (C) 2016 The Crown (i.e. Her Majesty the Queen in Right of Canada)

This file is part of RAVE.

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
/**
 * Command-line binary for rb52odim
 * @file
 * @author Daniel Michelson and Peter Rodriguez, Environment Canada
 * @date 2016-08-17
 */
#include <string.h>
#include "rb52odim.h"
#include "rave_debug.h"

/**
 * Command-line rb5_2_odim
 *
 * Compile: make -f Makefile.w_rb5_2_odim_main
 *
 * Debug: valgrind --leak-check=full --show-reachable=yes ./rb5_2_odim -i ../test/2015120916511800dBZ.ele -o dummy.ele.h5
 * Debug: valgrind --leak-check=full --show-reachable=yes ./rb5_2_odim -i ../test/2016081612320300dBZ.azi -o dummy.azi.h5
 * Debug: valgrind --leak-check=full --show-reachable=yes ./rb5_2_odim -i ../test/2015120916500500dBZ.azi -o dummy.azi.h5
 *        valgrind --leak-check=full --show-reachable=yes ./rb5_2_odim -i ../test/2016092614304000dBZ.vol -o dummy.vol.h5
 *        valgrind --leak-check=full --show-reachable=yes ./rb5_2_odim -i ../test/2016092617103700ALL.vol -o dummy.ALL.vol.h5 > rb5_2_odim.vol.run.txt 2>&1
 *
 */
int main(int argc,char *argv[]) {
    int RETURN_FAILURE = -1;
    int ret = 0;
    int i;
    const char *ifile=NULL, *ofile=NULL;

    /* call this before any of your code */
    Rave_initializeDebugger();
    Rave_setDebugLevel(RAVE_SPEWDEBUG);

    RaveIO_t* raveio = RAVE_OBJECT_NEW(&RaveIO_TYPE);
    RaveCoreObject* object = NULL;
    int rot = Rave_ObjectType_UNDEFINED;

    if (argc!=5) {
      printf("usage: %s -i RB5_file -o ODIM_H5_file\n", argv[0]);
      return 1;
    }

    for (i=1;i<argc;i++) {
      if (strcmp(argv[i], "-i") == 0) {
        i++;
        ifile = argv[i];
      }
      else if (strcmp(argv[i], "-o") == 0) {
        i++;
        ofile = argv[i];
      }
      else {
        printf("usage: %s -i RB5_file -o ODIM_H5_file\n", argv[0]);
        return RETURN_FAILURE;
      }
    }

//#############################################################################

// Doesn't handle .gz, replaced by rb52odim.c:isRainbow5buf()
//    if (isRainbow5(ifile) != 0) {
//        fprintf(stderr,"ERROR! This is something other than a proper RB5 raw file : %s\n", ifile);
//        return RETURN_FAILURE;
//    }
//    return EXIT_SUCCESS; //forced

//#############################################################################

    // Peter-Rodriguez hack for command-line version
    if(getenv("RB52ODIMCONFIG")==NULL){
//      fprintf(stderr,"Error cannot getenv(\"RB52ODIMCONFIG\")\n");
      char sCWD[MAX_STRING]="\0";
      getcwd(sCWD, sizeof(sCWD));
      char sCMD[MAX_STRING]="\0";
      strcpy(sCMD,"RB52ODIMCONFIG=");
      strcat(sCMD,sCWD);
      fprintf(stderr,"Setting: %s to cwd = %s\n","RB52ODIMCONFIG",sCWD);
      putenv(sCMD);
    }

//#############################################################################

    //use open_xml_buffer() to ingest file
    char *inp_fname=(char *)ifile;
    strXML_FILE_INFO xml_info;
    strcpy(xml_info.inp_fullfile,inp_fname);
    if(open_xml_buffer(&xml_info) != 0) {
      fprintf(stderr,"Error cannot process file = %s\n", inp_fname);
      return(EXIT_FAILURE);
    }

    //get RB5 top level info
    //init with xml_info
    strRB5_INFO rb5_info;
    strcpy(rb5_info.inp_fullfile,xml_info.inp_fullfile);
    rb5_info.buffer=xml_info.buffer;
    rb5_info.buffer_len=xml_info.buffer_len;
    rb5_info.byte_offset_blobspace=xml_info.byte_offset_end_of_xml;
    rb5_info.doc=xml_info.doc;
    rb5_info.xpathCtx=xml_info.xpathCtx;

    int L_VERBOSE=0;
    if(populate_rb5_info(&rb5_info,L_VERBOSE) != 0) {
      fprintf(stderr,"Error cannot process file = %s\n", inp_fname);
      return RETURN_FAILURE;
    }

//#############################################################################

    /* If the RB5 file contains a scan or a pvol, create equivalent object */
    rot = objectTypeFromRB5(rb5_info);
    if (rot == Rave_ObjectType_PVOL) {
      object = (RaveCoreObject*)RAVE_OBJECT_NEW(&PolarVolume_TYPE);
    } else {
      if(rot == Rave_ObjectType_SCAN) {
        object = (RaveCoreObject*)RAVE_OBJECT_NEW(&PolarScan_TYPE);
      } else return RETURN_FAILURE;
    }

    /* Map RB5 object(s) to Toolbox ones. */
    ret = populateObject(object, &rb5_info);

    /* Set the object into the I/O container and write an HDF5 file */
    RaveIO_setObject(raveio, object);
    ret = RaveIO_save(raveio, ofile);
    RaveIO_close(raveio);

    //spoof /what/object='ELEV'
    if(strcmp(rb5_info.scan_type,"ele") == 0){
        char* H5_string=NULL;
        char* H5_path=NULL;

        //rave_io.c: RaveIO_save()
        RaveIO_setFilename(raveio, ofile);
        printf("Filename = '%s\n", raveio->filename);
        printf("HL_isHDF5File = %d\n", HL_isHDF5File(raveio->filename));

        HL_NodeList* nodelist = NULL;
        nodelist = HLNodeList_read(raveio->filename);
        HLNodeList_selectAllNodes(nodelist);
        HLNodeList_fetchMarkedNodes(nodelist);

        H5_path="/what/version";
        RaveHL_getStringValue(nodelist, &H5_string, H5_path);
        printf("%s = %s\n", H5_path, H5_string);
        
        H5_path="/what/object";
        RaveHL_getStringValue(nodelist, &H5_string, H5_path);
        printf("%s = %s\n", H5_path, H5_string);

        //rave_hlhdf_utilities.c: RaveHL_getStringValue()
        static const char value[]="ELEV";
        HL_Node* node = NULL;
        node = HLNodeList_getNodeByName(nodelist, H5_path);
        HLNode_setScalarValue(node, strlen(value) + 1, (unsigned char*)value, "string", -1);

        RaveHL_getStringValue(nodelist, &H5_string, H5_path);
        printf("%s = %s\n", H5_path, H5_string);

        HLNodeList_setFileName(nodelist, raveio->filename);
        HLNodeList_write(nodelist, raveio->property, raveio->compression);
        HLNodeList_free(nodelist);
    }


    RAVE_OBJECT_RELEASE(raveio);
    RAVE_OBJECT_RELEASE(object);

    close_rb5_info(&rb5_info);
    xmlCleanupParser(); // free globals in main() only for thread safety & valgrind

    return ret;
}
