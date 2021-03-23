'''
Copyright (C) 2021 The Crown (i.e. Her Majesty the Queen in Right of Canada)

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

Test suite for rb52odim

@file
@author Peter Rodriguez, Environment and Climate Change Cananda
@date 2021-02-24
'''
import unittest, os, sys
import _rave
import _rb52odim

from rb52odimTests import *


if __name__ == '__main__':
#  unittest.main()

  # do only this one test
  suite = unittest.TestSuite()
#  suite.addTest(rb52odimTest("testWrongInput"))
#  suite.addTest(rb52odimTest("testSingleRB5Azi"))
#  suite.addTest(rb52odimTest("testSingleRB5Vol"))
#  suite.addTest(rb52odimTest("testReadParameters"))
#  suite.addTest(rb52odimTest("testCombineRB5Files"))
#  suite.addTest(rb52odimTest("testCombineRB5FromTarball"))
#  suite.addTest(rb52odimTest("testCompileScanParameters"))
#  suite.addTest(rb52odimTest("testCompileVolumeFromVolumes"))
#  suite.addTest(rb52odimTest("testMergeOdimScans2Pvol"))
#  suite.addTest(rb52odimTest("testCompileVolumeFromVolumes_vs_CombineRB5FilesReturnRIO"))

  # do all
  suite = unittest.TestLoader().loadTestsFromTestCase(rb52odimTest)

  #verbosity control added >=2.7
  #".", "E" or "F" for "ok", "error" and "fail" written by self.AssertXXX method if verbose>=1
  result = unittest.TextTestRunner(verbosity=3).run(suite)
  #print('result : %s' % result)

  #return an exit code
  exit_code=int(not result.wasSuccessful())
  #print('Exit code : %d' % exit_code)
  sys.exit(exit_code)
