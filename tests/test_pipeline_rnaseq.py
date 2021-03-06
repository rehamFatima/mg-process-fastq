"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.

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

import os.path
import pytest # pylint: disable=unused-import

from process_rnaseq import process_rnaseq
from basic_modules.metadata import Metadata

@pytest.mark.rnaseq
@pytest.mark.pipeline
def test_rnaseq_pipeline():
    """
    Test case to ensure that the RNA-seq pipeline code works.

    Running the pipeline with the test data from the command line:

    .. code-block:: none

       runcompss                                                         \\
          --lang=python                                                  \\
          --library_path=${HOME}/bin                                     \\
          --pythonpath=/<pyenv_virtenv_dir>/lib/python2.7/site-packages/ \\
          --log_level=debug                                              \\
          process_rnaseq.py                                              \\
             --taxon_id 9606                                             \\
             --genome /<dataset_dir>/Human.GRCh38.fasta                  \\
             --assembly GRCh38                                           \\
             --file /<dataset_dir>/ERR030872_1.fastq                     \\
             --file2 /<dataset_dir>/ERR030872_2.fastq

    """
    resource_path = os.path.join(os.path.dirname(__file__), "data/")

    files = {
        'cdna': resource_path + 'kallisto.Human.GRCh38.fasta',
        'fastq1': resource_path + 'kallisto.Human.ERR030872_1.fastq',
        'fastq2': resource_path + 'kallisto.Human.ERR030872_2.fastq'
    }

    metadata = {
        "cdna": Metadata(
            "Assembly", "fasta", files['cdna'], None,
            {'assembly' : 'GCA_000001405.22'}),
        "fastq1": Metadata(
            "data_rna_seq", "fastq", files['fastq1'], None,
            {'assembly' : 'GCA_000001405.22'}
        ),
        "fastq2": Metadata(
            "data_rna_seq", "fastq", files['fastq2'], None,
            {'assembly' : 'GCA_000001405.22'}
        ),
    }

    files_out = {
        "index": 'tests/data/kallisto.idx',
        "abundance_h5_file": 'tests/data/kallisto.abundance.h5',
        "abundance_tsv_file": 'tests/data/kallisto.abundance.tsv',
        "run_info_file": 'tests/data/kallisto.run_info.json'
    }

    rs_handle = process_rnaseq()
    rs_files, rs_meta = rs_handle.run(files, metadata, files_out)

    # Checks that the returned files matches the expected set of results
    assert len(rs_files) == 4

    # Add tests for all files created
    for f_out in rs_files:
        print("RNA SEQ RESULTS FILE:", f_out)
        assert rs_files[f_out] == files_out[f_out]
        assert os.path.isfile(rs_files[f_out]) is True
        assert os.path.getsize(rs_files[f_out]) > 0
