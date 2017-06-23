#!usr/bin/env python

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

from tool import inps

@pytest.mark.py3
def test_inps():    
    
    resource_path = os.path.join(os.path.dirname(__file__), "data/")
    bam_file = resource_path + "inps.Mouse.GRCm38.bam"
    peak_bed = bam_file.replace('.bam', '.bed')
   
    inps_obj = inps.inps()      
    inps_obj.run ([bam_file, peak_bed],{})
    
    
    
