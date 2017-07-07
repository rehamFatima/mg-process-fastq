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

try:
    from pycompss.api.parameter import FILE_IN, FILE_OUT
    from pycompss.api.task import task
    from pycompss.api.api import compss_wait_on
except ImportError:
    print ("[Warning] Cannot import \"pycompss\" API packages.")
    print ("          Using mock decorators.")

    from dummy_pycompss import FILE_IN, FILE_OUT
    from dummy_pycompss import task
    from dummy_pycompss import compss_wait_on

from basic_modules.tool import Tool

from tool.common import common

# ------------------------------------------------------------------------------

class bowtieIndexerTool(Tool):
    """
    Tool for running indexers over a genome FASTA file
    """

    def __init__(self):
        """
        Init function
        """
        print("Bowtie2 Indexer")
        Tool.__init__(self)

    @task(file_loc=FILE_IN, idx_loc=FILE_OUT)
    @staticmethod
    def bowtie2_indexer(file_loc, bt_file1, bt_file2, bt_file3, # pylint: disable=unused-argument,too-many-arguments
                        bt_file4, bt_filer1, bt_filer2): # pylint: disable=unused-argument
        """
        Bowtie2 Indexer

        Parameters
        ----------
        file_loc : str
            Location of the genome assembly FASTA file
        idx_loc : str
            Location of the output index file
        """
        common_handle = common()
        common_handle.bowtie_index_genome(file_loc)
        return True

    def run(self, input_files, output_files, metadata=None):
        """
        Tool for generating assembly aligner index files for use with the
        Bowtie 2 aligner

        Parameters
        ----------
        input_files : list
            List with a single str element with the location of the genome
            assembly FASTA file
        metadata : list

        Returns
        -------
        array : list
            First element is a list of the index files. Second element is a
            list of the matching metadata
        """

        file_name = input_files[0].split('/')
        file_name[-1] = file_name[-1].replace('.fasta', '')
        file_name[-1].replace('.fa', '')

        # input and output share most metadata
        output_metadata = dict(
            data_type=metadata[0]["data_type"],
            file_type=metadata[0]["file_type"],
            meta_data=metadata[0]["meta_data"])

        results = self.bowtie2_indexer(
            input_files[0],
            output_files[0],
            output_files[1],
            output_files[2],
            output_files[3],
            output_files[4],
            output_files[5]
        )

        results = compss_wait_on(results)

        # handle error
        #if not self.bowtie2_indexer(input_files[0], output_file):
        #    output_metadata.set_exception(
        #        Exception(
        #            "bowtie2_indexer: Could not process files {}, {}.".format(*input_files)))
        #    output_file = None
        return (output_files, output_metadata)

# ------------------------------------------------------------------------------
