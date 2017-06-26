#!usr/bin/python

"""
.. Copyright 2017 EMBL-European Bioinformatics Institute
 
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at 

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import pytest
import random
import os
import sys

#PACKAGE_PARENT = '..'
#SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
#sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from tool import bs_seeker_filter

def test_bs_seeker_filter():    
    
    resource_path = os.path.join(os.path.dirname(__file__), "data/")
    genomefa_file = resource_path + "bsSeeker.Mouse.GRCm38_1.fastq"
    
    bsi = bs_seeker_filter.filterReadsTool()
    bsi.run([genomefa_file],{"aligner":"bowtie", "aligner_path":"/usr/local/bin","bss_path":"/Users/reham/lib/BSseeker2"})
    

    
   