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

from __future__ import print_function

import shlex
import subprocess
import sys

try:
    if hasattr(sys, '_run_from_cmdl') is True:
        raise ImportError
    from pycompss.api.parameter import FILE_IN, FILE_OUT
    from pycompss.api.task import task
    from pycompss.api.api import compss_wait_on
except ImportError:
    print("[Warning] Cannot import \"pycompss\" API packages.")
    print("          Using mock decorators.")

    from dummy_pycompss import FILE_IN, FILE_OUT
    from dummy_pycompss import task
    from dummy_pycompss import compss_wait_on

#from basic_modules.metadata import Metadata
from basic_modules.tool import Tool

# ------------------------------------------------------------------------------

class biobambam(Tool):
    """
    Tool to sort and filter bam files
    """

    def __init__(self, configuration=None):
        """
        Init function
        """
        print("BioBamBam2 Filter")
        Tool.__init__(self)

    @task(returns=int, bam_file_in=FILE_IN, bam_file_out=FILE_OUT,
          isModifier=False)
    def biobambam_filter_alignments(self, bam_file_in, bam_file_out):
        """
        Sorts and filters the bam file.

        It is important that all duplicate alignments have been removed. This
        can be run as an intermediate step, but should always be run as a check
        to ensure that the files are sorted and duplicates have been removed.

        Parameters
        ----------
        bam_file_in : str
            Location of the input bam file
        bam_file_out : str
            Location of the output bam file
        tmp_dir : str
            Tmp location for intermediate files during the sorting

        Returns
        -------
        bam_file_out : str
            Location of the output bam file
        """

        td_list = bam_file_in.split("/")
        tmp_dir = "/".join(td_list[0:-1])

        command_line = 'bamsormadup --tmpfile=' + tmp_dir
        print(command_line)
        args = shlex.split(command_line)
        with open(bam_file_in, "r") as f_in:
            with open(bam_file_out, "w") as f_out:
                process = subprocess.Popen(args, stdin=f_in, stdout=f_out)
                process.wait()

        return 0


    def run(self, input_files, output_files, metadata=None):
        """
        The main function to run BioBAMBAMfilter to remove duplicates and
        spurious reads from the FASTQ files before analysis.

        Parameters
        ----------
        input_files : list
            List of input bam file locations where 0 is the bam data file
        metadata : dict

        Returns
        -------
        output_files : list
            Filtered bam fie.
        output_metadata : list
            List of matching metadata dict objects
        """
        in_bam = input_files[0]
        out_filtered_bam = input_files[0].replace('.bam', '.filtered.bam')

        output_metadata = {}

        results = self.biobambam_filter_alignments(in_bam, out_filtered_bam)
        results = compss_wait_on(results)

        print(results)

        return ([out_filtered_bam], output_metadata)

# ------------------------------------------------------------------------------
