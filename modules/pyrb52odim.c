/* --------------------------------------------------------------------
Copyright (C) 2020 The Crown (i.e. Her Majesty the Queen in Right of Canada)

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
 * Python wrapper to RB52ODIM
 * @file
 * @author Daniel Michelson, Environment Canada
 * @date 2015-10-28
 * @author Peter Rodriguez, Environment Canada
 * @date 2020-09-01, upgrade to use Python >2.6 and Python 3 compatibility file
 */
#include "pyrb52odim_compat.h"
#include "arrayobject.h"
#include "rave.h"
#include "rave_debug.h"
#include "pyraveio.h"
#include "pypolarvolume.h"
#include "pypolarscan.h"
#include "pyrave_debug.h"
#include "rb52odim.h"

/**
 * Debug this module
 */
PYRAVE_DEBUG_MODULE("_rb52odim");

/**
 * Sets a Python exception.
 */
#define Raise(type,msg) {PyErr_SetString(type,msg);}

/**
 * Sets a Python exception and goto tag
 */
#define raiseException_gotoTag(tag, type, msg) \
{PyErr_SetString(type, msg); goto tag;}

/**
 * Sets a Python exception and return NULL
 */
#define raiseException_returnNULL(type, msg) \
{PyErr_SetString(type, msg); return NULL;}

/**
 * Error object for reporting errors to the Python interpreter
 */
static PyObject *ErrorObject;

/**
 * Verifies if buffer is of proper RB5 raw file contents that can be handled
 * @param[in] Buffer with the RB5 file contents
 * @returns Python boolean True or False
 */
static PyObject* _isRainbow5buf_func(PyObject* self, PyObject* args) {
  const char* filename;
  char* rb5_buffer;
  Py_ssize_t buffer_len;

//testing if PyObject
  PyObject *obj = NULL;  
  PyObject *result = NULL;
  if (!PyArg_ParseTuple(args, "O", &obj)) {;
    return PyBool_FromLong(0);  /* False */
  }
//py2  if (PyObject_TypeCheck(obj, &PyBaseString_Type)) {;
  if (PyObject_TypeCheck(obj, &PyBaseObject_Type)) {;
    if (!PyArg_ParseTuple(args, "s#", &rb5_buffer, &buffer_len)) {
        return PyBool_FromLong(0);  /* False */
    }

    if (!isRainbow5buf(&rb5_buffer)) return PyBool_FromLong(1);  /* True */
    else return PyBool_FromLong(0);  /* False */

  } else if (PyObject_TypeCheck(obj, &PyBaseObject_Type)) {
    fprintf(stdout,"A Python Object was passed\n");
    result=PyObject_GetAttrString(obj, "name");
    PyArg_Parse(result,"s",&filename);
    Py_DECREF(result);
    fprintf(stdout,"filename = %s\n",filename);
    size_t buffer_len=0;
    result=PyObject_GetAttrString(obj, "size");
    PyArg_Parse(result,"l",&buffer_len);
    Py_DECREF(result);
    fprintf(stdout,"buffer_len = %ld\n",buffer_len);
    char *buffer=NULL; //which will take on the Python buffer
    result=PyObject_CallMethod(obj, "read", NULL);
    PyArg_Parse(result,"s",&buffer);
    Py_DECREF(result);
    fprintf(stdout,"READ buffer = %.250s\n",buffer);
    if (!isRainbow5buf(&buffer)) {
        return PyBool_FromLong(1);  /* True */
    } else return PyBool_FromLong(0);  /* False */
  }

  return PyBool_FromLong(0);  /* False */

}

/**
 * Verifies if file is a proper RB5 raw file that can be handled
 * @param[in] String with the RB5 file name
 * @returns Python boolean True or False
 */
static PyObject* _isRainbow5_func(PyObject* self, PyObject* args) {
  const char* filename;

  if (!PyArg_ParseTuple(args, "s", &filename)) {
    return Py_None;
  }

  if (!is_regular_file(filename)) return PyBool_FromLong(0);  /* False */

  if (!isRainbow5(filename)) return PyBool_FromLong(1);  /* True */
  else return PyBool_FromLong(0);  /* False */

}

/**
 * Reads an RB5 buffer
 * @param[in] Buffer with the RB5 file contents
 * @returns PyRave_IO object containing a PolarVolume_t or PolarScan_t
 */
static PyObject* _readRB5buf_func(PyObject* self, PyObject* args) {
  const char* filename;
  char* rb5_buffer;
  Py_ssize_t ignore_count = 0;
  Py_ssize_t buffer_len = 0;
  PyRaveIO* result = NULL;
  RaveIO_t* raveio = NULL;

  if (!PyArg_ParseTuple(args, "ss#l", &filename, &rb5_buffer, &ignore_count, &buffer_len)) {
    return Py_None;
  }
 
  //Copy Python's buffer. Needed for close_rb5_info()'s free(rb5_info->buffer)
  /* my_rb5_buffer is freed in xml_utils.c:close_file_buffer, so we can't 
     allocate memory for it using RAVE_MALLOC */
  char* my_rb5_buffer=malloc(sizeof(char)*(buffer_len));
  memcpy(my_rb5_buffer,rb5_buffer,(size_t)buffer_len);

  raveio = getRaveIObuf((char *)filename,&my_rb5_buffer,(size_t)buffer_len);
  result = PyRaveIO_New(raveio);
  RAVE_OBJECT_RELEASE(raveio);
  if (result->raveio) return (PyObject*)result;
  else return Py_None;
}

/**
 * Reads an RB5 file
 * @param[in] String with the RB5 file name
 * @returns PyRave_IO object containing a PolarVolume_t or PolarScan_t
 */
static PyObject* _readRB5_func(PyObject* self, PyObject* args) {
  const char* filename;
  PyRaveIO* result = NULL;
  RaveIO_t* raveio = NULL;

  if (!PyArg_ParseTuple(args, "s", &filename)) {
    return Py_None;
  }

  raveio = getRaveIO(filename);
  result = PyRaveIO_New(raveio);
  RAVE_OBJECT_RELEASE(raveio);
  if (result->raveio) return (PyObject*)result;
  else return Py_None;
}


static struct PyMethodDef _rb52odim_functions[] =
{
  { "isRainbow5buf", (PyCFunction) _isRainbow5buf_func, METH_VARARGS },
  { "isRainbow5",    (PyCFunction) _isRainbow5_func,    METH_VARARGS },
  { "readRB5buf",    (PyCFunction) _readRB5buf_func,    METH_VARARGS },
  { "readRB5",       (PyCFunction) _readRB5_func,       METH_VARARGS },
  { NULL, NULL }
};

/**
 * Initialize the _rb52odim module
 */
MOD_INIT(_rb52odim)
{
  PyObject* module = NULL;
  PyObject* dictionary = NULL;
  
  MOD_INIT_DEF(module, "_rb52odim", NULL/*doc*/, _rb52odim_functions);
  if (module == NULL) {
    return MOD_INIT_ERROR;
  }

  dictionary = PyModule_GetDict(module);
  ErrorObject = PyErr_NewException("_rb52odim.error", NULL, NULL);
  if (ErrorObject == NULL || PyDict_SetItemString(dictionary, "error", ErrorObject) != 0) {
    Py_FatalError("Can't define _rb52odim.error");
    return MOD_INIT_ERROR;
  }

  import_pyraveio();
  import_pypolarvolume();
  import_pypolarscan();
  import_array(); /*To make sure I get access to numpy*/
  PYRAVE_DEBUG_INITIALIZE;
  return MOD_INIT_SUCCESS(module);
}

/*@} End of Module setup */
