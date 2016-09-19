#!/usr/bin/python

"""
Copyright 2016 EMBL-European Bioinformatics Institute

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

import argparse, urllib2, gzip, shutil, shlex, subprocess, os.path

from functions import danpos

#from pycompss.api.task import task
#from pycompss.api.parameter import *


try :
    import pysam
except ImportError :
    print "[Error] Cannot import \"pysam\" package. Have you installed it?"
    exit(-1)


class process_rnaseq:
    """
    Functions for downloading and processing Mnase-seq FastQ files. Files are
    downloaded from the European Nucleotide Archive (ENA), then aligned,
    filtered and analysed for peak calling
    """
    
    def __init__ (self):
        """
        Initialise the module
        """
        self.ready = ""
    
    
    def getGenomeFile(self, data_dir, species, assembly):
        """
        Function for downloading and extracting the DNA files from the ensembl FTP
        """
        
        file_name = data_dir + '/' + species + '_' + assembly + '/' + species + '.' + assembly + '.dna.toplevel.fa.gz'
        
        if os.path.isfile(file_name) == False:
            cdna_file = urllib2.urlopen(
            'ftp://ftp.ensembl.org/pub/current_fasta/' + species.lower() + '/dna/' + species[0].upper() + species[1:] + '.' + assembly + '.dna.toplevel.fa.gz')
            
            CHUNK = 16 * 1024
                    
            with open(file_name, 'wb') as fp:
                while True:
                    chunk = cdna_file.read(CHUNK)
                    if not chunk: break
                    fp.write(chunk)
            
            self.bwa_index_genome(file_name)
        
        return file_name
    
    
    def getFastqFiles(self, ena_err_id, data_dir):
        """
        Function for downloading and extracting the FastQ files from the ENA
        """
        
        f_index = urllib2.urlopen(
        'http://www.ebi.ac.uk/ena/data/warehouse/filereport?accession=' + str(ena_err_id) + '&result=read_run&fields=study_accession,run_accession,tax_id,scientific_name,instrument_model,library_layout,fastq_ftp&download=txt')
        data = f_index.read()
        rows = data.split("\n")
        row_count = 0
        files = []
        gzfiles  = []
        for row in rows:
            if row_count == 0:
                row_count += 1
                continue
            
            row = row.rstrip()
            row = row.split("\t")
            
            if len(row) < 6:
                continue
            
            project = row[0]
            srr_id = row[1]
            fastq_files = row[6].split(';')
            row_count += 1
            
            for fastq_file in fastq_files:
                file_name = fastq_file.split("/")
                print data_dir + '/' + project + "/" + file_name[-1]
                
                req = urllib2.urlopen("ftp://" + fastq_file)
                CHUNK = 16 * 1024
                
                files.append(data_dir + '/' + project + "/" + file_name[-1].replace('.fastq.gz', '.fastq'))
                gzfiles.append(data_dir + '/' + project + "/" + file_name[-1])
                
                with open(data_dir + '/' + project + "/" + file_name[-1], 'wb') as fp:
                    while True:
                        chunk = req.read(CHUNK)
                        if not chunk: break
                        fp.write(chunk)
        
        for gzf in gzfiles:
            with gzip.open(gzf, 'rb') as f_in, open(gzf.replace('.fastq.gz', '.fastq'), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.remove(gzf)
        
        return files
    
    
    def bwa_index_genome(self, genome_file):
        """
        Create an index of the 
        """
        command_line = 'bwa index ' + genome_file
        
        args = shlex.split(command_line)
        p = subprocess.Popen(args)
        p.wait()
        
        
    def bwa_align_reads(self, genome_file, data_dir, run_id):
        """
        Map the reads to the genome
        """
        
        reads_file = data_dir + '/' + run_id + '.fq'
        intermediate_file = data_dir + '/' + run_id + '.sai'
        intermediate_sam_file = data_dir + '/' + run_id + '.sam'
        output_bam_file = data_dir + '/' + run_id + '.bam'
        
        command_lines = [
            'bwa aln -q 5 -f ' + intermediate_file + ' ' + genome_file + ' ' + reads_file,
            'bwa samse -f ' + intermediate_sam_file  + ' ' + genome_file + ' ' + intermediate_file + ' ' + reads_file,
            'samtools view -b -o ' + output_bam_file + ' ' + intermediate_sam_file
        ]
        
        for command_line in command_lines:
            args = shlex.split(command_line)
            p = subprocess.Popen(args)
            p.wait()
     
    
    def merge_bam(self, data_dir, final_id, run_ids=[]):
        """
        Merge together all the bams in a directory and sort to create the final
        bam ready to be filtered
        
        If run_ids is blank then the function looks for all bam files in the
        data_dir
        """
        out_bam_file = data_dir + '/' + project_id + '/' + final_id + '.bam'
        
        if len(run_ids) == 0:
            bam_files = [f for f in listdir(data_dir + '/' + project_id) if f.endswith(("sai"))]
        else:
            bam_files = [f + ".bam" for f in run_ids]
        
        bam_sort_files = []
        bam_merge_files = []
        for bam in bam_files:
            bam_sort_files.append(bam)
            bam_merge_files.append(["-o", bam + ".sorted.bam", "-T", bam + ".bam_sort", bam])
        
        map(pysam.sort, bam_sort_files)
        
        pysam.merge(out_bam_file, bam_merge_files)
    
        pysam.sort("-o", out_bam_file + '.sorted.bam', "-T", out_bam_file + ".bam_sort", out_bam_file)
    
        pysam.index(out_bam_file)
    
    
    def danpos2_peak_calling(self, data_dir, run_ids = [], paired = 0, wild_type_id = None):
        """
        Runs dpos script in DANPOS2. The call has been extracted from the
        danpos.py script so that it can get run as part of the pipeline
        
        Need to handle
        """
        bam_file = data_dir + run_id + '.bam'
        bam_file = ','.join([data_dir + run_id for run_id in run_ids])
        #bam_bgd_file = data_dir + bgd_id + '.bam'
        
        danpos(tpath=bam_file,paired=paired,opath='result',save=0,tbg=None,fdr=1,\
            call_region=0,\
            call_peak=0,\
            call_position=1,width=40,distance=100,edge=0,fill_gap=0,ratio=0.9,\
            ref_position=None,\
            height=5,pheight=0,logp=0,\
            nor='F',nonzero=0,amount=None,step=10,smooth_width=20,lmd=300,\
            cut=0,fs=None,mifrsz=50,mafrsz=300,extend=80,\
            exclude_low_percent=0,exclude_high_percent=0,region_file=None,\
            both=True,\
            wgfmt='fixed',\
            fill_value=1,\
            test='P',\
            pcfer=0)
    
    #@task()
    def main(self, data_dir, expt, genome_fa):
        """
        Main loop
        """
        # Optain the FastQ files
        run_ids = []
        run_fastq_files = []
        
        run_ids = []
        run_fastq_files = {}
        for run_id in expt["run_ids"]:
            run_ids.append(run_id)
            in_files = self.getFastqFiles(run_id, data_dir)
            run_fastq_files[run_id] = in_files
        
        # Obtain background FastQ files
        bgd_ids = []
        bgd_fastq_files = []
        for bgd_id in expt["bgd_ids"]:
            bgd_ids.append(run_id)
            in_files = self.getFastqFiles(bgd_id, data_dir)
            bgd_fastq_files[run_id] = in_files
        
        # Run BWA
        paired = 0
        for run_id in expt["run_ids"]:
            if len(run_fastq_files[run_id]) > 1:
                paired = 1
                for i in range(1,len(run_fastq_files[run_id])+1):
                    self.bwa_align_reads(genome_fa, data_dir, expt["project_id"], run_id + "_" + str(i))
            else:
                self.bwa_align_reads(genome_fa, data_dir, expt["project_id"], run_id)
        
        for bgd_id in expt["bgd_ids"]:
            if len(run_fastq_files[run_id]) > 1:
                paired = 1
                for i in range(1,len(run_fastq_files[run_id])+1):
                    self.bwa_align_reads(genome_fa, data_dir, expt["project_id"], bgd_id + "_" + str(i))
            else:
                self.bwa_align_reads(genome_fa, data_dir, expt["project_id"], bgd_id)
        
        #final_run_id = expt["project_id"] + "_" + expt["group_name"] + "_run"
        #final_bgd_id = expt["project_id"] + "_" + expt["group_name"] + "_bgd"
        
        # Merge Bam files
        #self.merge_bam(data_dir, expt["project_id"], final_run_id, expt["run_ids"])
        #self.merge_bam(data_dir, expt["project_id"], final_bgd_id, expt["bgd_ids"])
        
        # DANPOS to call peaks
        if len(expt["bgd_ids"]) == 1:
            self.danpos2_peak_calling(data_dir, expt["project_id"], expt["run_ids"], paired, expt["bgd_ids"][0])
        else:        
            self.danpos2_peak_calling(data_dir, expt["project_id"], expt["run_ids"], paired, None)
    
if __name__ == "__main__":
    import sys
    import os
    
    # Set up the command line parameters
    parser = argparse.ArgumentParser(description="Mnase-seq peak calling")
    parser.add_argument("--species", help="Species (Homo_sapiens)")
    parser.add_argument("--assembly", help="Assembly (GRCm38)")
    parser.add_argument("--project_id", help="Project ID of the dataset (PRJDA47577)")
    parser.add_argument("--run_ids", help="File with list of the experiment run IDs of the dataset")
    parser.add_argument("--data_dir", help="Data directory; location to download ERR FASTQ files and save results")

    # Get the matching parameters from the command line
    args = parser.parse_args()
    
    project     = args.project_id
    run_id_file = args.run_ids
    species     = args.species
    assembly    = args.assembly
    data_dir    = args.data_dir
    
    prs = process_rnaseq()
    
    try:
        os.makedirs(data_dir)
    except:
        pass

    try:
        os.makedirs(data_dir + '/' + project)
    except:
        pass
    
    try:
        os.makedirs(data_dir + '/' + species + "_" + assembly)
    except:
        pass
    
    # Get the assembly
    genome_fa = prs.getGenomeFile(data_dir, species, assembly)
    
    # Run main loop
    with open(run_id_file) as data_file:    
        job_id_sets = json.load(data_file)
    
    for expt in job_id_sets["expts"]:
        prs.main(data_dir, expt, genome_fa)
    
    
