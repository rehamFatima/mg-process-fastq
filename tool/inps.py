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

import os

try :
    from pycompss.api.parameter import *
    from pycompss.api.task import task
except ImportError :
    print("[Warning] Cannot import \"pycompss\" API packages.")
    print("          Using mock decorators.")
    
    from dummy_pycompss import *

from basic_modules.metadata import Metadata
from basic_modules.tool import Tool

from common import common

# ------------------------------------------------------------------------------

class inps(Tool):
    """
    Tool for peak calling for MNase-seq data
    """
    
    def __init__(self):
        """
        Init function
        """
        print "iNPS Peak Caller"
    
    @task(bam_file = FILE_IN, peak_bed = FILE_OUT)
    def inps_peak_calling(self, bam_file, peak_bed):
        """
        Convert Bam to Bed then make Nucleosome peak calls. These are saved as
        bed files That can then get displayed on genome browsers.
        
        Parameters
        ----------
        bam_file : str
            Location of the aligned sequences in bam format
        
        Returns
        -------
        peak_bed : str
            Location of the collated bed file of nucleosome peak calls
        """
        
        with cd('../../lib/iNPS'):
            command_line_1 = 'bedtools bamtobed -i ' + bam_file
            command_line_2 = 'python iNPS_V1.2.2.py -i ' + bed_file + ' -o ' + peak_bed
            
            
            args = shlex.split(command_line_1)
            with open(bed_file, "w") as f_out:
                p = subprocess.Popen(args, stdout=f_out)
                p.wait()
            
            args = shlex.split(command_line_2)
            p = subprocess.Popen(args)
            p.wait()
        
        return peak_bed
    
    
    def run(self, input_files, metadata):
        """
        The main function to run MACS 2 for peak calling over a given BAM file
        and matching background BAM file.
        
        Parameters
        ----------
        input_files : list
            List of input bam file locations where 0 is the bam data file and 1
            is the matching background bam file
        metadata : dict
        
        
        Returns
        -------
        output_files : list
            List of locations for the output files.
        output_metadata : list
            List of matching metadata dict objects
        
        """
        
        bam_file = input_files[0]
        peak_bed = bam_file.replace('.bam', '.bed')
        
        # input and output share most metadata
        output_metadata = {}
        
        # handle error
        if not self.inps_peak_calling(bam_file, peak_bed):
            output_metadata.set_exception(
                Exception(
                    "inps_peak_calling: Could not process files {}, {}.".format(*input_files)))
            peak_bed = None
        return ([peak_bed], output_metadata)

# ------------------------------------------------------------------------------
