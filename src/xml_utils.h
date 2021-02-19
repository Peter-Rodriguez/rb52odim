#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <libxml/tree.h> //add -I/usr/include/libxml2 -lxml2 to compile
#include <libxml/parser.h>
#include <libxml/xpath.h>
#include <libxml/xpathInternals.h>

#include <zlib.h> //for gzopen(), gzread(), gzclose()
#include <errno.h>

#define MAX_STRING 256

typedef struct{
    char inp_fullfile[MAX_STRING];
    char *buffer;
    size_t buffer_len;
    size_t byte_offset_end_of_xml;
    xmlDoc *doc;
    xmlXPathContextPtr xpathCtx;
} strXML_FILE_INFO;

//#############################################################################
// function declarations
//#############################################################################
size_t get_xpath_size(const xmlXPathContextPtr xpathCtx, char *xpath);
char *return_xpath_name(const xmlXPathContextPtr xpathCtx, char *xpath);
char *return_xpath_value(const xmlXPathContextPtr xpathCtx, char *xpath);

size_t read_file_2_buffer(char *inp_fname, char **return_buffer);
void close_file_buffer(char *buffer);

size_t find_buffer_end_of_xml(char *buffer);

int open_xml_buffer(strXML_FILE_INFO *xml_info);
void close_xml_buffer(strXML_FILE_INFO *xml_info);
