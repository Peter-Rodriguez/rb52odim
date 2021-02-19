#include <stdint.h> //for uint8_t, uint16_t, uint32_t
#include <stdio.h>
#include <ctype.h> //for toupper()
#include <stdlib.h>
#include <string.h>
#include <libgen.h> //for basename()

#include <zlib.h> //add -lz to compile

#include <libxml/tree.h> //add -lxml2 -I/usr/include/libxml2 to compile
#include <libxml/parser.h>
#include <libxml/xpath.h>
#include <libxml/xpathInternals.h>

#define L_DEBUG_OUTPUT_1 0
#define L_DEBUG_OUTPUT_2 0

#define MAX_STRING 256
#define MAX_NSTRINGS 32
#define MAX_SLICES 32
#define MAX_PARAMS MAX_NSTRINGS

#define MAX_PULSE_WIDTHS 4

//#define MINIMUM_RAINBOW_VERSION "5.0"
#define MINIMUM_RAINBOW_VERSION "5.43.10" //wrt CAX1 delivery (sensorinfo attribs have been updated)

typedef struct{
    char inp_fullfile[MAX_STRING];
    char inp_file_basename[MAX_STRING];
    char inp_file_dirname[MAX_STRING];
    char inp_file_data_type[MAX_STRING];
    char *buffer;
    size_t buffer_len;
    xmlDoc *doc;
    xmlXPathContextPtr xpathCtx;
    size_t byte_offset_blobspace;

    char rainbow_version[MAX_STRING];
    char xml_block_name[MAX_STRING];
    char xml_block_type[MAX_STRING];
    char xml_block_iso8601[MAX_STRING];

    char sensor_id[MAX_STRING];
    char sensor_name[MAX_STRING];
    char sensor_type[MAX_STRING];
    float sensor_lon_deg;
    float sensor_lat_deg;
    float sensor_alt_m;
    float sensor_wavelength_cm;
    float sensor_beamwidth_deg;

    int  history_exists;
    char history_pdfname[MAX_STRING];
    char history_ppdfname[MAX_STRING];
    char history_sdfname[MAX_STRING];
    size_t history_n_rawdatafiles;
    char history_rawdatafiles_arr[MAX_STRING][MAX_NSTRINGS];
    size_t history_n_preprocessedfiles;
    char history_preprocessedfiles_arr[MAX_STRING][MAX_NSTRINGS];

    char scan_type[MAX_STRING];
    char scan_name[MAX_STRING];
    size_t n_slices;
    char slice_iso8601_bgn[MAX_STRING][MAX_SLICES];
    char slice_iso8601_end[MAX_STRING][MAX_SLICES];
    double slice_dur_secs[MAX_SLICES];
    float angle_deg_arr[MAX_SLICES];

    float slice_nyquist_vel[MAX_SLICES];
    float slice_nyquist_wid[MAX_SLICES];
    char slice_threshold_flags[MAX_STRING][MAX_SLICES];
    float slice_bin_range_res_km[MAX_SLICES];
    float slice_bin_range_bgn_km[MAX_SLICES];
    float slice_bin_range_end_km[MAX_SLICES];
    float slice_ray_angle_res_deg[MAX_SLICES];
    float slice_ray_angle_bgn_deg[MAX_SLICES];
    float slice_ray_angle_end_deg[MAX_SLICES];
    size_t slice_pw_index[MAX_SLICES];
    float slice_pw_microsec[MAX_SLICES];
    float slice_antspeed_deg_sec[MAX_SLICES];
    float slice_antspeed_rpm[MAX_SLICES];
    size_t slice_num_samples[MAX_SLICES];
    char slice_dual_prf_mode[MAX_STRING][MAX_SLICES];
    char slice_prf_stagger[MAX_STRING][MAX_SLICES];
    float slice_hi_prf[MAX_SLICES];
    float slice_lo_prf[MAX_SLICES];
    float slice_csr_threshold[MAX_SLICES];
    float slice_sqi_threshold[MAX_SLICES];
    float slice_zsqi_threshold[MAX_SLICES];
    float slice_log_threshold[MAX_SLICES];
    float slice_noise_power_h[MAX_SLICES];
    float slice_noise_power_v[MAX_SLICES];
    float slice_radconst_h[MAX_SLICES];
    float slice_radconst_v[MAX_SLICES];

    //applicable to sub-params unless strRB5_PARAM_INFO has differently
    size_t nrays[MAX_SLICES];
    size_t nbins[MAX_SLICES];
    size_t n_elems_data[MAX_SLICES];
    size_t iray_0degN[MAX_SLICES];

    float* slice_moving_angle_start_arr[MAX_SLICES];
    float* slice_moving_angle_stop_arr[MAX_SLICES];
    float* slice_fixed_angle_start_arr[MAX_SLICES];
    float* slice_fixed_angle_stop_arr[MAX_SLICES];

    float* slice_moving_angle_arr[MAX_SLICES];
    float* slice_fixed_angle_arr[MAX_SLICES];

    size_t n_rayinfos;
    size_t n_rawdatas;
    char rayinfo_name_arr[MAX_STRING][MAX_PARAMS];
    char rawdata_name_arr[MAX_STRING][MAX_PARAMS];
} strRB5_INFO;

typedef struct{
    char xpath_bgn[MAX_STRING];
    char sparam[MAX_STRING];
    char iso8601[MAX_STRING];
    size_t blobid;
    size_t size_blob;
    size_t n_elems_data;
    size_t data_bytesize;

    size_t raw_binary_depth;
    size_t raw_binary_min;
    size_t raw_binary_max;
    size_t raw_binary_width;
    
    size_t nrays;
    size_t nbins;
    size_t iray_0degN;

    char conversion[MAX_STRING];
    float data_range_min;
    float data_range_max;
    float data_range_width;
    float data_step;
    float NODATA_val;
} strRB5_PARAM_INFO;

typedef struct{
    int  type;
    char name[MAX_STRING];
    char unit[MAX_STRING];
    char desc[MAX_STRING];
} strURPDATA;

//#############################################################################
// function declarations
//#############################################################################
size_t uncompress_this_blob(unsigned char *buf, unsigned char** return_uncompressed_blob, size_t compressed_size_blob);
char *get_xpath_iso8601_attrib(const xmlXPathContextPtr xpathCtx, char *xpath_bgn);
size_t get_blobid_buffer(strRB5_INFO *rb5_info, int req_blobid, unsigned char** return_uncompressed_blob);
void convert_raw_to_data(strRB5_PARAM_INFO *rb5_param, void **input_raw_arr, float **return_data_arr);
size_t return_param_blobid_raw(strRB5_INFO *rb5_info, strRB5_PARAM_INFO* rb5_param, void **return_raw_arr);
char *map_rb5_to_h5_param(char *sparam);
int is_rb5_param_dualpol(char *sparam);
strURPDATA what_is_this_param_to_urp(char *sparam);
void close_rb5_info(strRB5_INFO *rb5_info);
char *get_xpath_slice_attrib(const xmlXPathContextPtr xpathCtx, size_t this_slice, char *xpath_end);
int populate_rb5_info(strRB5_INFO *rb5_info, int L_VERBOSE);
strRB5_PARAM_INFO get_rb5_param_info(strRB5_INFO *rb5_info, char *xpath_bgn, int L_VERBOSE);
size_t find_in_string_arr(char arr[][MAX_NSTRINGS], size_t n, char *match);
void dump_strRB5_PARAM_INFO(strRB5_PARAM_INFO rb5_param);
void get_slice_iray_0degN(strRB5_INFO *rb5_info, int req_slice);
void reorder_by_iray_0degN(strRB5_PARAM_INFO *rb5_param, void **input_raw_arr);
void get_slice_end_iso8601(strRB5_INFO *rb5_info, int req_slice);
void get_slice_mid_angle_readbacks(strRB5_INFO *rb5_info, int req_slice);
