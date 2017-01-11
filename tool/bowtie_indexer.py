"""
.. Copyright 2016 EMBL-European Bioinformatics Institute
 
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

from pycompss.api.parameter import FILE_IN, FILE_OUT
from pycompss.api.task import task

from basic_modules.metadata import Metadata
from basic_modules.tool import Tool

from .. import common

# ------------------------------------------------------------------------------

class bowtieIndexerTool(Tool):
    """
    Tool for running indexers over a genome FASTA file
    """
    
    @task(file_loc=FILE_IN, idx_loc=FILE_OUT)
    def bowtie2_indexer(self, file_loc, idx_loc):
        """
        Bowtie2 Indexer
        """
        cf = common()
        output_file = cf.bowtie_index_genome(file_loc)
        return True
    
    def run(self, input_files, metadata):
         """
        Standard function to call a task
        """
        
        output_file = file_name[-1].replace('.fa', '')
        
        # input and output share most metadata
        output_metadata = dict(
            data_type=metadata[0]["data_type"],
            file_type=metadata[0]["file_type"],
            meta_data=metadata[0]["meta_data"])
        
        # handle error
        if not self.bowtie_indexer(input_files[0], output_file):
            output_metadata.set_exception(
                Exception(
                    "bowtie2_indexer: Could not process files {}, {}.".format(*input_files)))
output_file = None
        return ([output_file], [output_metadata])

# ------------------------------------------------------------------------------
