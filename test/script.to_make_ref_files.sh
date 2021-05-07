#!/bin/bash

#execute from test dir
base_dir=$(pwd)/..
cd ${base_dir}/test

#NOTE do first: for ${base_dir}/src/rb5_2_odim command-line version (remember to 'make -f Makefile.w_rb5_2_odim_main')
export RB52ODIMCONFIG=${base_dir}/config 

#NOTE: must 'make clean' from ${base_dir} for modules/_rb52odim.so to update too
#and 'make install'
rm ${base_dir}/Lib/*.pyc
#rm */*.so #src/librb52odim.so & modules/_rb52odim.so

##check and modify as needed, added to .gitignore
bak_suffix=2018-Mar-21.bak
bak_suffix=2020-Dec-08.bak
bak_suffix=2021-May-06.bak
rsync -av ref ref_${bak_suffix}

echo Making... REF_H5_VOL and REF_H5_AZI
${base_dir}/src/rb5_2_odim -i org/2016092614304000dBZ.vol -o ref/2016092614304000dBZ.vol.ref.h5
${base_dir}/src/rb5_2_odim -i org/2016081612320300dBZ.azi -o ref/2016081612320300dBZ.azi.ref.h5

echo Making... REF_H5_FILELIST
#problem with extraneous 'how/RXlossV'=str('')=0.0 getting into H5 <--- importing ${RAVEROOT}/Lib/_rb52odim.so!!!
#fixed make install
# see utils/test__rb52odim_combine_files.py.sh
${base_dir}/utils/rb52odim_combine_files.py \
-i \
org/Dopvol1_A.azi/2015120916500500dBuZ.azi,\
org/Dopvol1_A.azi/2015120916500500dBZ.azi,\
org/Dopvol1_A.azi/2015120916500500PhiDP.azi,\
org/Dopvol1_A.azi/2015120916500500RhoHV.azi,\
org/Dopvol1_A.azi/2015120916500500SQI.azi,\
org/Dopvol1_A.azi/2015120916500500uPhiDP.azi,\
org/Dopvol1_A.azi/2015120916500500V.azi,\
org/Dopvol1_A.azi/2015120916500500W.azi,\
org/Dopvol1_A.azi/2015120916500500ZDR.azi \
-o \
ref/caxah_dopvol1a_20151209T1650Z.by_filelist.ref.h5
echo
#exit

echo Making... REF_H5_TARBALL_DOPVOL1B
#see utils/test__rb52odim_combine_tarball.py.sh
${base_dir}/utils/rb52odim_combine_tarball.py \
-i org/caxah_dopvol1a_20151209T1650Z.azi.tar.gz \
-o ref/caxah_dopvol1a_20151209T1650Z.azi.ref.h5
${base_dir}/utils/rb52odim_combine_tarball.py \
-i org/caxah_dopvol1b_20151209T1650Z.azi.tar.gz \
-o ref/caxah_dopvol1b_20151209T1650Z.azi.ref.h5
${base_dir}/utils/rb52odim_combine_tarball.py \
-i org/caxah_dopvol1c_20151209T1650Z.azi.tar.gz \
-o ref/caxah_dopvol1c_20151209T1650Z.azi.ref.h5
echo

echo Making... REF_H5_MERGED_PVOL
#see utils/test__odim_combine_sweeps.py.sh
${base_dir}/utils/odim_combine_sweeps.py \
-c 5 \
-t DOPVOL \
-i \
ref/caxah_dopvol1a_20151209T1650Z.azi.ref.h5,\
ref/caxah_dopvol1b_20151209T1650Z.azi.ref.h5,\
ref/caxah_dopvol1c_20151209T1650Z.azi.ref.h5 \
-o \
ref/caxah_dopvol_20151209T1650Z.vol.ref.h5
echo

##./rb52odim_combine_files.py previously couldn't handle .gz files
#for f in CASRA*.???.gz; do
#    gunzip -dvc $f > ${f%%.gz}
#done

echo Making... REF_CASRA_H5_SCAN
${base_dir}/utils/rb52odim_combine_files.py \
-i \
org/CASRA_2017121520051400dBuZ.azi.gz,\
org/CASRA_2017121520051400dBZ.azi.gz,\
org/CASRA_2017121520051400PhiDP.azi.gz,\
org/CASRA_2017121520051400RhoHV.azi.gz,\
org/CASRA_2017121520051400SQI.azi.gz,\
org/CASRA_2017121520051400uPhiDP.azi.gz,\
org/CASRA_2017121520051400V.azi.gz,\
org/CASRA_2017121520051400W.azi.gz,\
org/CASRA_2017121520051400ZDR.azi.gz \
-o \
ref/CASRA_20171215200514_scan.ref.h5
echo

#failing, because cannot add .vol as compile_big_scan is across sparam_arr[] as from combineRB5FromTarball()
#./rb52odim_combine_files.py \
#-i \
#org/CASRA_2017121520000300dBuZ.vol.gz,\
#org/CASRA_2017121520000300dBZ.vol.gz,\
#org/CASRA_2017121520000300PhiDP.vol.gz,\
#org/CASRA_2017121520000300RhoHV.vol.gz,\
#org/CASRA_2017121520000300SQI.vol.gz,\
#org/CASRA_2017121520000300uPhiDP.vol.gz,\
#org/CASRA_2017121520000300V.vol.gz,\
#org/CASRA_2017121520000300W.vol.gz,\
#org/CASRA_2017121520000300ZDR.vol \
#-o ref/CASRA_20171215200003_pvol.ref.h5

echo Making... REF_CASRA_H5_PVOL
#see ./utils/polar_merger.py for hardcoded entries
[ -d tmp ] || mkdir tmp #added to .gitignore
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300dBuZ.vol.gz   -o tmp/CASRA_2017121520000300dBuZ.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300dBZ.vol.gz    -o tmp/CASRA_2017121520000300dBZ.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300PhiDP.vol.gz  -o tmp/CASRA_2017121520000300PhiDP.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300RhoHV.vol.gz  -o tmp/CASRA_2017121520000300RhoHV.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300SQI.vol.gz    -o tmp/CASRA_2017121520000300SQI.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300uPhiDP.vol.gz -o tmp/CASRA_2017121520000300uPhiDP.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300V.vol.gz      -o tmp/CASRA_2017121520000300V.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300W.vol.gz      -o tmp/CASRA_2017121520000300W.vol.h5.tmp
${base_dir}/src/rb5_2_odim -i org/CASRA_2017121520000300ZDR.vol.gz    -o tmp/CASRA_2017121520000300ZDR.vol.h5.tmp
#${base_dir}/utils/polar_merger.py #makes ref/CASRA_20171215200003_pvol.ref.h5 (old hardcoded)
${base_dir}/utils/polar_merger.py \
-i \
tmp/CASRA_2017121520000300dBuZ.vol.h5.tmp,\
tmp/CASRA_2017121520000300dBZ.vol.h5.tmp,\
tmp/CASRA_2017121520000300PhiDP.vol.h5.tmp,\
tmp/CASRA_2017121520000300RhoHV.vol.h5.tmp,\
tmp/CASRA_2017121520000300SQI.vol.h5.tmp,\
tmp/CASRA_2017121520000300uPhiDP.vol.h5.tmp,\
tmp/CASRA_2017121520000300V.vol.h5.tmp,\
tmp/CASRA_2017121520000300W.vol.h5.tmp,\
tmp/CASRA_2017121520000300ZDR.vol.h5.tmp \
-o \
ref/CASRA_20171215200003_pvol.ref.h5

#rm tmp/CASRA_2017121520000300*.vol.h5.tmp
