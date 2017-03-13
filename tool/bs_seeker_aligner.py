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

try:
    from pycompss.api.parameter import FILE_IN, FILE_OUT
    from pycompss.api.task import task
except ImportError :
    print "[Warning] Cannot import \"pycompss\" API packages."
    print "          Using mock decorators."
    
    from dummy_pycompss import *

from basic_modules.metadata import Metadata
from basic_modules.tool import Tool

from common import common

from bs_index.wg_build import *

# ------------------------------------------------------------------------------

class bssAlignerTool(Tool):
    """
    Script from BS-Seeker2 for building the index for alignment. In this case
    it uses Bowtie2.
    """
    
    def __init__(self):
        """
        Init function
        """
        print "BS-Seeker Aligner"

    @task(input_fastq1 = FILE_IN, input_fastq2 = FILE_IN, aligner = IN, aligner_path = IN, genome_fasta = FILE_IN, bam_out = FILE_INOUT)
    def bs_seeker_aligner(self, input_fastq1, input_fastq2, aligner, aligner_path, genome_fasta, bam_out):
        """
        Alignment of the paired ends to the reference genome
        Generates bam files for the alignments
        This is performed by running the external program rather than
        reimplementing the code from the main function to make it easier when
        it comes to updating the changes in BS-Seeker2

        Parameters
        ----------
        input_fastq1 : str
            Location of paired end FASTQ file 
        input_fastq2 : str
            Location of paired end FASTQ file 2
        aligner : str
            Aligner to use
        aligner_path : str
            Location of the aligner
        genome_fasta : str
            Location of the genome FASTA file
        bam_out : str
            Location of the aligned bam file

        Returns
        -------
        bam_out : file
            Location of the BAM file generated during the alignment.
        """
        import subprocess
        
        g_dir = genome_fasta.split("/")
        g_dir = "/".join(g_dir[0:-1])

        command_line = "python " + aligner_path + "/bs_seeker2-align.py --input_1 " + input_fastq1 + " --input_2 " + input_fastq2 + " --aligner " + aligner + " --path " + aligner_path + " --genome " + genome_fasta + " -d " + g_dir + " --bt2-p 4 -o " + bam_out
        
        args = shlex.split(command_line)
        p = subprocess.Popen(args)
        p.wait()

        return True


    def run(self, input_files, metadata):
        """
        Tool for indexing the genome assembly using BS-Seeker2. In this case it
        is using Bowtie2
        
        Parameters
        ----------
        input_files : list
            FASTQ file
        metadata : list
        
        Returns
        -------
        array : list
            Location of the filtered FASTQ file
        """
        
        genome_fasta = input_files[0]
        fasta_file_1 = input_files[1]
        fasta_file_2 = input_files[2]

        gd = file_name.split("/")
        genome_dir = '/' + '/'.join(gd[:-1])
        
        aligner      = metadata['aligner']
        aligner_path = metadata['aligner_path']


        output_file = file_name + '.filtered.bam'
        
        # input and output share most metadata
        output_metadata = dict(
            data_type=metadata[0]["data_type"],
            file_type=metadata[0]["file_type"],
            meta_data=metadata[0]["meta_data"])
        
        # handle error
        if not self.bss_build_index(file_name, aligner, aligner_path, genome_dir, output_file):
            output_metadata.set_exception(
                Exception(
                    "bs_seeker_filter: Could not process files {}, {}.".format(*input_files)))
            output_file = None
        return ([output_file], [output_metadata])

# ------------------------------------------------------------------------------