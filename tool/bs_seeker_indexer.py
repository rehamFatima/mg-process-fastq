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
import os
import tarfile

try:
    if hasattr(sys, '_run_from_cmdl') is True:
        raise ImportError
    from pycompss.api.parameter import FILE_IN, FILE_OUT, IN
    from pycompss.api.task import task
    from pycompss.api.api import compss_wait_on
except ImportError:
    print("[Warning] Cannot import \"pycompss\" API packages.")
    print("          Using mock decorators.")

    from dummy_pycompss import FILE_IN, FILE_OUT, IN
    from dummy_pycompss import task
    from dummy_pycompss import compss_wait_on

from basic_modules.tool import Tool

# ------------------------------------------------------------------------------

class bssIndexerTool(Tool):
    """
    Script from BS-Seeker2 for building the index for alignment. In this case
    it uses Bowtie2.
    """

    def __init__(self):
        """
        Init function
        """
        print("BS-Seeker Indexer wrapper")
        Tool.__init__(self)

    @task(
        fasta_file=FILE_IN, aligner=IN, aligner_path=IN, bss_path=IN,
        idx_out=FILE_OUT)
    def bss_build_index(self, fasta_file, aligner, aligner_path, bss_path, idx_out):
        """
        Function to submit the FASTA file for the reference sequence and build
        the required index file used by the aligner.

        Parameters
        ----------
        fasta_file : str
            Location of the genome FASTA file
        aligner : str
            Aligner to use by BS-Seeker2. Currently only bowtie2 is available in
            this build
        aligner_path : str
            Location of the aligners binary file
        bss_path
            Location of the BS-Seeker2 libraries
        idx_out : str
            Location of the output compressed index file

        Returns
        -------
        bam_out : str
            Location of the output bam alignment file
        """

        ff_split = fasta_file.split("/")

        command_line = (
            "python " + bss_path + "/bs_seeker2-build.py"
            " -f " + fasta_file + ""
            " --aligner " + aligner + " --path " + aligner_path + ""
            " --db " + "/".join(ff_split[0:-1])
        ).format()

        print("BS - INDEX CMD:", command_line)
        args = shlex.split(command_line)
        process = subprocess.Popen(args)
        process.wait()

        # tar.gz the index
        print("BS - idx_out", idx_out, idx_out.replace('.tar.gz', ''))
        tar = tarfile.open(idx_out, "w:gz")
        tar.add(fasta_file + "_" + aligner)
        tar.close()

        return True


    def run(self, input_files, output_files, metadata=None):
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


        file_name = input_files[0]
        genome_dir_split = file_name.split("/")
        genome_dir = '/'.join(genome_dir_split[:-1])

        aligner = metadata['aligner']
        aligner_path = metadata['aligner_path']
        bss_path = metadata['bss_path']


        output_file = file_name + '_' + aligner + '.tar.gz'

        # input and output share most metadata
        output_metadata = {}

        # handle error
        results = self.bss_build_index(
            file_name, aligner, aligner_path, bss_path, output_file)
        results = compss_wait_on(results)

        if results is True:
            pass

        return ([output_file], [output_metadata])

# ------------------------------------------------------------------------------
