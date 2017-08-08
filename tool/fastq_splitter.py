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

import sys
import re
import tarfile

try:
    if hasattr(sys, '_run_from_cmdl') is True:
        raise ImportError
    from pycompss.api.parameter import FILE_IN, FILE_OUT, IN, OUT
    from pycompss.api.task import task
    from pycompss.api.api import compss_wait_on
except ImportError:
    print("[Warning] Cannot import \"pycompss\" API packages.")
    print("          Using mock decorators.")

    from dummy_pycompss import FILE_IN, FILE_OUT, IN, OUT
    from dummy_pycompss import task
    from dummy_pycompss import compss_wait_on

#from basic_modules.metadata import Metadata
from basic_modules.tool import Tool

from fastqreader import fastqreader

# ------------------------------------------------------------------------------

class fastq_splitter(Tool):
    """
    Script for splitting up FASTQ files into manageable chunks
    """

    def __init__(self):
        """
        Init function
        """
        print("FASTQ Splitter")
        Tool.__init__(self)

    @task(
        in_file1=FILE_IN, tag=IN,
        out_file=FILE_OUT, files_out=OUT,
        returns=list
    )
    def single_splitter(self, in_file1, out_file, tag='tmp'):
        """
        Function to divide the FastQ files into separate sub files of 1000000
        sequences so that the aligner can run in parallel.

        Parameters
        ----------
        in_file1 : str
            Location of first FASTQ file
        tag : str
            DEFAULT = tmp
            Tag used to identify the files. Useful if this is getting run
            manually on a single machine multiple times to prevent collisions of
            file names


        Returns
        -------
        Returns: Returns a list of the files that have been generated.
                 Each sub list containing the two paired end files for that
                 subset.
        paired_files : list
            List of lists of pair end files. Each sub list containing the two
            paired end files for that subset.
        """

        fqr = fastqreader()
        fqr.openFastQ(in_file1)
        fqr.createOutputFiles(tag)

        record1 = fqr.next(1)

        count_r3 = 0

        file_loc_1 = fqr.fastq1.split("/")
        file_loc_1[-1] = file_loc_1[-1].replace(
            ".fastq",
            "." + str(fqr.output_tag) + "_" + str(fqr.output_file_count) + ".fastq")
        file_loc_1.insert(-1, tag)

        files_out = [["/".join(file_loc_1)]]

        while fqr.eof(1) is False:
            fqr.writeOutput(record1, 1)
            record1 = fqr.next(1)
            count_r3 += 1

            if count_r3 % 1000000 == 0:
                fqr.incrementOutputFiles()
                file_loc_1 = fqr.fastq1.split("/")
                new_suffix = "." + str(fqr.output_tag) + "_" + str(fqr.output_file_count) + ".fastq"
                file_loc_1[-1] = re.sub('.fastq$', new_suffix, file_loc_1[-1])
                #file_loc_1[-1] = file_loc_1[-1].replace(
                #    ".fastq",
                #    "." + str(fqr.output_tag) + "_" + str(fqr.output_file_count) + ".fastq")
                file_loc_1.insert(-1, "tmp")

                #files_out.append(["/".join(file_loc_1)])
                files_out.append([file_loc_1[-1]])

        fqr.closeFastQ()
        fqr.closeOutputFiles()

        tar = tarfile.open(out_file, "w:gz")
        tar.add("/".join(file_loc_1[:-1]), arcname='tmp')
        tar.close()

        return files_out

    @task(
        in_file1=FILE_IN, in_file2=FILE_IN, tag=IN,
        out_file=FILE_OUT, files_out=OUT,
        returns=list
    )
    def paired_splitter(self, in_file1, in_file2, out_file, tag='tmp'):
        """
        Function to divide the FastQ files into separte sub files of 1000000
        sequences so that the aligner can run in parallel.

        Parameters
        ----------
        in_file1 : str
            Location of first paired end FASTQ file
        in_file2 : str
            Location of second paired end FASTQ file
        tag : str
            DEFAULT = tmp
            Tag used to identify the files. Useful if this is getting run
            manually on a single machine multiple times to prevent collisions of
            file names


        Returns
        -------
        Returns: Returns a list of lists of the files that have been generated.
                 Each sub list containing the two paired end files for that
                 subset.
        paired_files : list
            List of lists of pair end files. Each sub list containing the two
            paired end files for that subset.
        """

        fqr = fastqreader()
        fqr.openFastQ(in_file1, in_file2)
        fqr.createOutputFiles(tag)

        record1 = fqr.next(1)
        record2 = fqr.next(2)

        count_r1 = 0
        count_r2 = 0
        count_r3 = 0

        file_loc_1 = fqr.fastq1.split("/")
        new_suffix = "." + str(fqr.output_tag) + "_" + str(fqr.output_file_count) + ".fastq"
        file_loc_1[-1] = re.sub('.fastq$', new_suffix, file_loc_1[-1])
        file_loc_1.insert(-1, tag)

        file_loc_2 = fqr.fastq2.split("/")
        new_suffix = "." + str(fqr.output_tag) + "_" + str(fqr.output_file_count) + ".fastq"
        file_loc_2[-1] = re.sub('.fastq$', new_suffix, file_loc_2[-1])

        file_loc_2.insert(-1, tag)
        files_out = [[file_loc_1[-1], file_loc_2[-1]]]

        while fqr.eof(1) is False and fqr.eof(2) is False:
            r1_id = record1["id"].split(" ")
            r2_id = record2["id"].split(" ")

            if r1_id[0] == r2_id[0]:
                fqr.writeOutput(record1, 1)
                fqr.writeOutput(record2, 2)

                record1 = fqr.next(1)
                record2 = fqr.next(2)

                count_r1 += 1
                count_r2 += 1
                count_r3 += 1
            elif r1_id[0] < r2_id[0]:
                record1 = fqr.next(1)
                count_r1 += 1
            else:
                record2 = fqr.next(2)
                count_r2 += 1

            if count_r3 % 1000000 == 0:
                fqr.incrementOutputFiles()
                file_loc_1 = fqr.fastq1.split("/")
                file_loc_1[-1] = file_loc_1[-1].replace(
                    ".fastq",
                    "." + str(fqr.output_tag) + "_" + str(fqr.output_file_count) + ".fastq")
                file_loc_1.insert(-1, "tmp")

                file_loc_2 = fqr.fastq2.split("/")
                file_loc_2[-1] = file_loc_2[-1].replace(
                    ".fastq",
                    "." + str(fqr.output_tag) + "_" + str(fqr.output_file_count) + ".fastq")
                file_loc_2.insert(-1, "tmp")

                files_out.append([file_loc_1[-1], file_loc_2[-1]])

        fqr.closeFastQ()
        fqr.closeOutputFiles()

        tar = tarfile.open(out_file, "w:gz")
        tar.add("/".join(file_loc_1[:-1]), arcname='tmp')
        tar.close()

        return files_out

    def run(self, input_files, output_files, metadata=None):
        """
        The main function to run the splitting of FASTQ files (single or paired)
        so that they can aligned in a distributed manner

        Parameters
        ----------
        input_files : list
            List of input fastq file locations
        output_files : list
        metadata : dict


        Returns
        -------
        output_file : str
            Location of compressed (.tar.gz) of the split FASTQ files
        output_names : list
            List of file names in the compressed file

        """

        if len(input_files) == 2:
            results = output_files = self.paired_splitter(
                input_files[0], input_files[1],
                input_files[0] + ".tar.gz"
            )
        else:
            results = output_files = self.single_splitter(
                input_files[0],
                input_files[0] + ".tar.gz",
            )

        results = compss_wait_on(results)

        print("WGBS - FASTQ SPLITTER:", results)

        return (
            input_files[0] + ".tar.gz",
            results
        )
