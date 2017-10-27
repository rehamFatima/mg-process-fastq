#!/usr/bin/env python

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

import argparse

from basic_modules.workflow import Workflow
from utils import logger
from utils import remap

from tool.fastq_splitter import fastq_splitter
from tool.bs_seeker_aligner import bssAlignerTool
from tool.bs_seeker_filter import filterReadsTool
from tool.bs_seeker_indexer import bssIndexerTool
from tool.bs_seeker_methylation_caller import bssMethylationCallerTool

# ------------------------------------------------------------------------------

class process_wgbs(Workflow):
    """
    Functions for downloading and processing whole genome bisulfate sequencings
    (WGBS) files. Files are filtered, aligned and analysed for points of
    methylation
    """

    configuration = {}

    def __init__(self, configuration=None):
        """
        Initialise the tool with its configuration.


        Parameters
        ----------
        configuration : dict
            a dictionary containing parameters that define how the operation
            should be carried out, which are specific to each Tool.
        """
        logger.info("Processing WGBS")
        if configuration is None:
            configuration = {}
        self.configuration.update(configuration)

    def run(self, input_files, metadata, output_files):
        """
        This pipeline processes paired-end FASTQ files to identify
        methylated regions within the genome.

        Parameters
        ----------
        input_files : list
            List of strings for the locations of files. These should include:

            genome_fa : str
                Genome assembly in FASTA
            fastq1 : str
                FASTQ file for the first pair end file
            fastq2 : str
                FASTQ file for the second pair end file

        Returns
        -------
        wig_file : str
            Location of the wig file containing the methylation peak calls
        cgmap_file : str
            Location of the CGmap file generated by BS-Seeker2
        atcgmap_file : str
            Location of the ATCGmap file generated by BS-Seeker2
        """
        output_results_files = {}
        output_metadata = {}

        logger.info("PIPELINE - metadata:", metadata)

        try:
            if "bss_path" in self.configuration:
                metadata["bss_path"] = self.configuration["bss_path"]
            if "aligner_path" in self.configuration:
                metadata["aligner_path"] = self.configuration["aligner_path"]
            if "aligner" in self.configuration:
                metadata["aligner"] = self.configuration["aligner"]
        except KeyError:
            logger.fatal("WGBS: Keys not defined")
            return {}, {}

        # Filter the FASTQ reads to remove duplicates
        logger.info("WGBS - Filter")
        frt = filterReadsTool()
        fastq1f, filter1_meta = frt.run(
            {"fastq": input_files["fastq1"]},
            {
                "fastq": metadata["fastq1"],
                "bss_path": metadata["bss_path"]
            },
            {"fastq_filtered": output_files["fastq1_filtered"]}
        )

        try:
            output_results_files["fastq1_filtered"] = fastq1f["fastq_filtered"]
            output_metadata["fastq1_filtered"] = filter1_meta["fastq_filtered"]
            tool_name = output_metadata['fastq1_filtered'].meta_data['tool']
            output_metadata['fastq1_filtered'].meta_data['tool_description'] = tool_name
            output_metadata['fastq1_filtered'].meta_data['tool'] = "process_wgbs"
        except KeyError:
            logger.fatal("WGBS - FILTER: Error while filtering")
            return {}, {}

        logger.info("WGBS - BS-Seeker2 Index")
        # Build the matching WGBS genome index
        builder = bssIndexerTool()
        genome_idx, gidx_meta = builder.run(
            remap(input_files, "genome"),
            remap(metadata, "genome", "aligner", "aligner_path", "bss_path"),
            remap(output_files, "index")
        )
        output_results_files['index'] = genome_idx["index"]
        output_metadata['index'] = gidx_meta["index"]

        if "fastq2" in input_files:
            logger.info("WGBS - Filter background")
            fastq2f, filter2_meta = frt.run(
                {"fastq": input_files["fastq2"]},
                {
                    "fastq": metadata["fastq2"],
                    "bss_path": metadata["bss_path"]
                },
                {"fastq_filtered": output_files["fastq2_filtered"]}
            )

            try:
                output_results_files["fastq2_filtered"] = fastq2f["fastq_filtered"]
                output_metadata['fastq2_filtered'] = filter2_meta["fastq_filtered"]

                tool_name = output_metadata['fastq2_filtered'].meta_data['tool']
                output_metadata['fastq2_filtered'].meta_data['tool_description'] = tool_name
                output_metadata['fastq2_filtered'].meta_data['tool'] = "process_wgbs"
            except KeyError:
                logger.fatal("WGBS - FILTER (background): Error while filtering")
                return {}, {}


        logger.info("WGBS - BS-Seeker2 Aligner")
        # Handles the alignment of all of the split packets then merges them
        # back together.
        bss_aligner = bssAlignerTool()
        aligner_input_files = remap(input_files, "genome", "fastq1", "fastq2")
        aligner_input_files["index"] = genome_idx["index"]

        aligner_meta = remap(
            metadata, "genome", "fastq1", "fastq2", "aligner", "aligner_path", "bss_path")
        aligner_meta["index"] = output_metadata['index']
        bam, bam_meta = bss_aligner.run(
            aligner_input_files,
            aligner_meta,
            remap(output_files, "bam", "bai")
        )

        try:
            output_results_files["bam"] = bam["bam"]
            output_results_files["bai"] = bam["bai"]
            output_metadata["bam"] = bam_meta["bam"]
            output_metadata["bai"] = bam_meta["bai"]

            tool_name = output_metadata['bam'].meta_data['tool']
            output_metadata['bam'].meta_data['tool_description'] = tool_name
            output_metadata['bam'].meta_data['tool'] = "process_wgbs"

            tool_name = output_metadata['bai'].meta_data['tool']
            output_metadata['bai'].meta_data['tool_description'] = tool_name
            output_metadata['bai'].meta_data['tool'] = "process_wgbs"
        except KeyError:
            logger.fatal("WGBS - Aligner failed")
            return {}, {}

        # Methylation peak caller
        peak_caller_handle = bssMethylationCallerTool()
        mct_meta = remap(
            metadata, "genome", "fastq1", "fastq2",
            "aligner", "aligner_path", "bss_path")
        mct_meta["bam"] = output_metadata["bam"]
        mct_meta["bai"] = output_metadata["bai"]
        mct_meta["index"] = output_metadata["index"]
        peak_files, peak_meta = peak_caller_handle.run(
            remap(output_files, "bam", "bai", "index"),
            mct_meta,
            remap(output_files, "wig_file", "cgmap_file", "atcgmap_file")
        )
        # output_metadata['peak_calling'] = peak_meta

        try:
            output_results_files["wig_file"] = peak_files["wig_file"]
            output_results_files["cgmap_file"] = peak_files["cgmap_file"]
            output_results_files["atcgmap_file"] = peak_files["atcgmap_file"]
            output_metadata["wig_file"] = peak_meta["wig_file"]
            output_metadata["cgmap_file"] = peak_meta["cgmap_file"]
            output_metadata["atcgmap_file"] = peak_meta["atcgmap_file"]

            output_metadata['wig_file'].meta_data['tool_description'] = output_metadata['wig_file'].meta_data['tool']
            output_metadata['wig_file'].meta_data['tool'] = "process_wgbs"
            output_metadata['cgmap_file'].meta_data['tool_description'] = output_metadata['cgmap_file'].meta_data['tool']
            output_metadata['cgmap_file'].meta_data['tool'] = "process_wgbs"
            output_metadata['atcgmap_file'].meta_data['tool_description'] = output_metadata['atcgmap_file'].meta_data['tool']
            output_metadata['atcgmap_file'].meta_data['tool'] = "process_wgbs"
        except KeyError:
            logger.fatal("WGBS - Peak caller failed")
            return {}, {}

        return (output_results_files, output_metadata)

# ------------------------------------------------------------------------------

def main_json(config, in_metadata, out_metadata):
    """
    Alternative main function
    -------------

    This function launches the app using configuration written in
    two json files: config.json and input_metadata.json.
    """
    # 1. Instantiate and launch the App
    print("1. Instantiate and launch the App")
    from apps.jsonapp import JSONApp
    app = JSONApp()
    result = app.launch(process_wgbs,
                        config,
                        in_metadata,
                        out_metadata)

    # 2. The App has finished
    print("2. Execution finished; see " + out_metadata)
    print(result)

    return result

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys._run_from_cmdl = True

    # Set up the command line parameters
    PARSER = argparse.ArgumentParser(description="WGBS peak calling")
    PARSER.add_argument("--config", help="Configuration file")
    PARSER.add_argument("--in_metadata", help="Location of input metadata file")
    PARSER.add_argument("--out_metadata", help="Location of output metadata file")

    # Get the matching parameters from the command line
    ARGS = PARSER.parse_args()

    CONFIG = ARGS.config
    IN_METADATA = ARGS.in_metadata
    OUT_METADATA = ARGS.out_metadata

    RESULTS = main_json(CONFIG, IN_METADATA, OUT_METADATA)

    print(RESULTS)
