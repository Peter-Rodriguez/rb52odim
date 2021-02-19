/* --------------------------------------------------------------------
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
/**
 * Description
 * @file
 * @author Daniel Michelson and Peter Rodriguez, Environment Canada
 * @date 2016-08-17
 */
#ifndef RB52ODIM_H
#define RB52ODIM_H
#include <time.h>
#include "projection.h"
#include "rave_io.h"
#include "rave_object.h"
#include "rave_field.h"
#include "rave_types.h"
#include "rave_attribute.h"
#include "polarscanparam.h"
#include "polarscan.h"
#include "polarvolume.h"

#include "rave_alloc.h"
#include "time_utils.h"
#include "rb5_utils.h"
#include "xml_utils.h"

#include <zlib.h> //for gzopen(), gzread(), gzclose()
#include <ctype.h> //for tolower() & isalnum()
#include <sys/stat.h> //stat()

#include <math.h> //log10()

#define L_RB52ODIM_DEBUG 0

#include "Python.h" //$RAVEROOT/rave/mkf/def.mk defines $INCLUDE_PYTHON envvar
#define L_RAVE_PY3 (PY_MAJOR_VERSION >= 3)
#if !(L_RAVE_PY3)
//for forward compatibility, from rave-py3/include/polarvolume.h
void PolarVolume_setBeamwH(PolarVolume_t* self, double beamwidth);
void PolarVolume_setBeamwV(PolarVolume_t* self, double beamwidth);
//for forward compatibility, from rave-py3/include/polarvolume.h
void PolarScan_setBeamwH(PolarScan_t* scan, double beamwidth);
void PolarScan_setBeamwV(PolarScan_t* scan, double beamwidth);
#endif

//function declarations from "rb52odim.c"
int objectTypeFromRB5(strRB5_INFO rb5_info);
int populateParam(PolarScanParam_t* param, strRB5_INFO *rb5_info, strRB5_PARAM_INFO *rb5_param);
int populateScan(PolarScan_t* scan, strRB5_INFO *rb5_info, int this_slice);
int populateObject(RaveCoreObject* object, strRB5_INFO *rb5_info);
RaveIO_t* getRaveIObuf(const char* ifile, char **inp_buffer, size_t buffer_len);
RaveIO_t* getRaveIO(const char* ifile);
int is_regular_file(const char *path);
int isRainbow5buf(char **inp_buffer);
int isRainbow5(const char* ifile);
/* START HELPER FUNCTIONS */
int setRayAttributes(PolarScan_t* scan, strRB5_INFO *rb5_info, int this_slice);
int addLongAttribute(RaveCoreObject* object, const char* name, long value);
int addDoubleAttribute(RaveCoreObject* object, const char* name, double value);
int addStringAttribute(RaveCoreObject* object, const char* name, const char* value);
int addAttribute(RaveCoreObject* object, RaveAttribute_t* attr);
/* END HELPER FUNCTIONS */

//################################################################################

#include "rave_hlhdf_utilities.h"

/**
 * Defines the structure for the RaveIO in a volume.
 */
struct _RaveIO_t {
  RAVE_OBJECT_HEAD /** Always on top */
  RaveCoreObject* object;                 /**< the object */
  RaveIO_ODIM_Version version;            /**< the odim version */
  RaveIO_ODIM_H5rad_Version h5radversion; /**< the h5rad object version */
  RaveIO_ODIM_FileFormat fileFormat;      /**< the file format */
  char* filename;                         /**< the filename */
  HL_Compression* compression;            /**< the compression to use */
  HL_FileCreationProperty* property;       /**< the file creation properties */
  char* bufrTableDir;                      /**< the bufr table dir */
};

#endif
