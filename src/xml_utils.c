/*
 * xml_utils.c
 *
 * Author: Peter Rodriguez 2018-Jan-25
 *
 * compile: gcc -Wall -I/usr/include/libxml2 -c xml_utils.c -lxml2
 *
 */

#include "xml_utils.h"

#define L_DEBUG_OUTPUT_xml 0

//#############################################################################

size_t get_xpath_size(const xmlXPathContextPtr xpathCtx, char *xpath){
    size_t return_NULL_val=0;

    const xmlChar* xpathExpr = (const xmlChar*) xpath;

    // evaluate xpath expression
    xmlXPathObjectPtr xpathObj = xmlXPathEvalExpression(xpathExpr, xpathCtx);
    if(xpathObj == NULL) {
        fprintf(stderr,"Error: unable to evaluate xpath expression \"%s\"\n", xpathExpr);
        return(return_NULL_val);
    }

    // use xpath object
    xmlNodeSetPtr nodes = xpathObj->nodesetval;
    size_t size = (nodes) ? nodes->nodeNr : 0;
    if(size == 0) {
        if(L_DEBUG_OUTPUT_xml) fprintf(stderr,"Error: xpath expression not found \"%s\"\n", xpathExpr);
        xmlXPathFreeObject(xpathObj);
        return(return_NULL_val);
    }

    /* Cleanup */
    xmlXPathFreeObject(xpathObj);

    return(size);
}

//#############################################################################

char *return_xpath_name(const xmlXPathContextPtr xpathCtx, char *xpath){

    const xmlChar* xpathExpr = (const xmlChar*) xpath;

    // evaluate xpath expression
    xmlXPathObjectPtr xpathObj = xmlXPathEvalExpression(xpathExpr, xpathCtx);
    if(xpathObj == NULL) {
        fprintf(stderr,"Error: unable to evaluate xpath expression \"%s\"\n", xpathExpr);
        return("\0");
    }

    // use xpath object
    xmlNodeSetPtr nodes = xpathObj->nodesetval;
    size_t size = (nodes) ? nodes->nodeNr : 0;
    if(size == 0) {
        if(L_DEBUG_OUTPUT_xml) fprintf(stderr,"Error: xpath expression not found \"%s\"\n", xpathExpr);
        xmlXPathFreeObject(xpathObj);
        return("\0");
    }

    //assume uniqueness, use [position()=X] in xpath
    //having used get_xpath_size() to build looping code
    int iNode = 0; // get only 1st value at xpath
    xmlNodePtr cur = (xmlNodePtr)xpathObj->nodesetval->nodeTab[iNode];
    if(cur == NULL) {
        fprintf(stderr,"Error: NULL node at xpath expression \"%s\"\n", xpathExpr);
        xmlXPathFreeObject(xpathObj);
        return("\0");
    }
    char *value = (char *) cur->name;
//    fprintf(stdout,"debug XPATH: %s = %s\n", xpathExpr, value);

    /* Cleanup */
    xmlXPathFreeObject(xpathObj);

    return(value);
}

//#############################################################################

char *return_xpath_value(const xmlXPathContextPtr xpathCtx, char *xpath){

    const xmlChar* xpathExpr = (const xmlChar*) xpath;

    // evaluate xpath expression
    xmlXPathObjectPtr xpathObj = xmlXPathEvalExpression(xpathExpr, xpathCtx);
    if(xpathObj == NULL) {
        fprintf(stderr,"Error: unable to evaluate xpath expression \"%s\"\n", xpathExpr);
        return("\0");
    }

    // use xpath object
    xmlNodeSetPtr nodes = xpathObj->nodesetval;
    size_t size = (nodes) ? nodes->nodeNr : 0;
    if(size == 0) {
        if(L_DEBUG_OUTPUT_xml) fprintf(stderr,"Error: xpath expression not found \"%s\"\n", xpathExpr);
        xmlXPathFreeObject(xpathObj);
        return("\0");
    }

    //assume uniqueness, use [position()=X] in xpath
    //having used get_xpath_size() to build looping code
    int iNode = 0; // get only 1st value at xpath
    xmlNodePtr cur = (xmlNodePtr)xpathObj->nodesetval->nodeTab[iNode];
    if(cur == NULL) {
        fprintf(stderr,"Error: NULL node at xpath expression \"%s\"\n", xpathExpr);
        xmlXPathFreeObject(xpathObj);
        return("\0");
    }
//2020-Nov: xmlNodeGetContent function has checks for null pointers at cur, children, and content
    char *value = (char *)xmlNodeGetContent(cur->children);
//    char *value = (char *) cur->children->content;
//    fprintf(stdout,"debug XPATH: %s = %s\n", xpathExpr, value);
    /* Cleanup */
    xmlXPathFreeObject(xpathObj);

    return(value);
}

//#############################################################################

//2018-May-25: Added gzopen() & gzread() handling
size_t read_file_2_buffer(char *inp_fname, char **return_buffer){

    size_t EXIT_NULL_VAL=0;

    char *buffer=NULL;
    size_t buffer_len=0;

    //based on https://www.lemoda.net/c/gzfile-read/
    size_t chunk_len = 0x1000; // Size of the block of memory to use for chunk reading

    gzFile fp = NULL;
    fp = gzopen(inp_fname, "r");
    if (! fp) {
        fprintf (stderr, "gzopen of '%s' failed: %s.\n", inp_fname, strerror (errno));
        return(EXIT_NULL_VAL);
    }

    while (1) {
        int err;
        int bytes_read;
        unsigned char chunk[chunk_len];
        bytes_read = gzread (fp, chunk, chunk_len - 1);
//        chunk[bytes_read] = '\0';
//        printf ("%s", chunk);
        buffer_len += bytes_read;
        if (bytes_read < chunk_len - 1) {
            if (gzeof (fp)) {
                break;
            }
            else {
                const char * error_string;
                error_string = gzerror (fp, & err);
                if (err) {
                    fprintf (stderr, "Error: %s.\n", error_string);
                    return(EXIT_NULL_VAL);
                }
            }
        }
    }

    /* Allocate our buffer to that size. */
    if(L_DEBUG_OUTPUT_xml) fprintf(stdout,"buffer_len = %ld\n",buffer_len);
    buffer=malloc(sizeof(char)*(buffer_len));

    /* Go back to the start of the file. */
    if (gzseek(fp,0L,SEEK_SET) != 0) {
        fprintf(stderr,"Error while moving back to start of file\n");
        return(EXIT_NULL_VAL);
     }

    /* Read the entire file into memory. */
    if (gzread(fp,buffer,buffer_len) <= 0) {
        fprintf(stderr,"Error while reading file\n");
        return(EXIT_NULL_VAL);
    }

//    if(L_DEBUG_OUTPUT_xml) fprintf(stdout,"buffer = %s\n",buffer);

    gzclose (fp);

    *return_buffer=buffer;

    return(buffer_len);
}

//#############################################################################

void close_file_buffer(char *buffer){

    if(buffer != NULL) free(buffer);
}

//#############################################################################

size_t find_buffer_end_of_xml(char *buffer){
    
    char substring[]="<!-- END XML -->";
    char *match=strstr(buffer,substring);
    if(match == 0){
        return strlen(buffer);
    } else {
        return match-buffer+strlen(substring)+1; //count trailing \n
    }
}

//#############################################################################

int open_xml_buffer(strXML_FILE_INFO *xml_info){

    // init
    xml_info->buffer=NULL;
    xml_info->doc=NULL;
    xml_info->xpathCtx=NULL;

    //ingest XML file to buffer
    if(L_DEBUG_OUTPUT_xml) fprintf(stdout,"reading : %s\n",xml_info->inp_fullfile);
    xml_info->buffer_len=read_file_2_buffer(xml_info->inp_fullfile,&(xml_info->buffer));
    if (xml_info->buffer_len == 0) {
        fprintf(stderr,"Cannot read XML in %s\n", xml_info->inp_fullfile);
        close_xml_buffer(&(*xml_info));
        return(EXIT_FAILURE);
    }

    //find end of XML
    xml_info->byte_offset_end_of_xml=find_buffer_end_of_xml(xml_info->buffer);

    // parse the XML and get the DOM
    xml_info->doc=xmlReadMemory(xml_info->buffer, xml_info->byte_offset_end_of_xml, "noname.xml", NULL, 0);

    // create xpath evaluation context
    xml_info->xpathCtx = xmlXPathNewContext(xml_info->doc);
    if(xml_info->xpathCtx == NULL) {
        fprintf(stderr,"Error: unable to create new XPath context\n");
        close_xml_buffer(&(*xml_info));
        return(EXIT_FAILURE);
    }

    return(EXIT_SUCCESS);
}

//#############################################################################

void close_xml_buffer(strXML_FILE_INFO *xml_info){

    if(xml_info->xpathCtx != NULL) xmlXPathFreeContext(xml_info->xpathCtx); //cleanup
    if(xml_info->doc      != NULL) xmlFreeDoc(xml_info->doc); // free the document
    if(xml_info->buffer   != NULL) close_file_buffer(xml_info->buffer); // free entire file buffer
}
