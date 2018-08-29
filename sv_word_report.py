#!/usr/bin/env python3
import os
import sys
import argparse
import logging
import time

from docxtpl import DocxTemplate, RichText, InlineImage
from docx.shared import Mm
from datetime import datetime

def read_table(_file_name, comment='#'):
    """
    :_file_name: file name
    :returns: list

    """
    with open(_file_name, 'r') as f:
        for line in f:
            if comment and line.startswith(comment):
                continue
            yield line.split('\t')


class Report(object):

    """生成报告"""

    def __init__(self, proj_id, sample_id, customer_institute, bioinfo_engineer, supervisor, proj_path, template_file, output_path):
        """初始化结果

        :proj_id: TODO
        :proj_name: TODO
        :proj_path: TODO

        """
        self._proj_id = proj_id
        self._sample_id = sample_id
        self._customer_institute = customer_institute
        self._bioinfo_engineer = bioinfo_engineer
        self._supervisor = supervisor
        self._proj_path = proj_path
        self._template_file = template_file
        self._output_path = output_path
        self.tpl = DocxTemplate(self._template_file)


    def format_cover_table_string(self, string):
        return "{}".format(string)

    def get_proj_info(self):
        """获取项目信息
        :returns: TODO

        """
        proj_info = {
            'customer_institute': self.format_cover_table_string(self._customer_institute),
            'proj_id': self.format_cover_table_string(self._proj_id),
            'sample_id': self._sample_id,
            'report_date': self.format_cover_table_string(datetime.now().strftime("%Y-%m-%d")),
            'bioinfo_engineer': self.format_cover_table_string(self._bioinfo_engineer),
            'supervisor': self.format_cover_table_string(self._supervisor)
        }
        return proj_info


    '''
    def get_img(self, file_name, width=110.1, flag=True):
        """TODO: Docstring for proc_img.

        :file_name: TODO
        :returns: TODO

        """
        if 0:
            return InlineImage(self.tpl, file_name, width=Mm(width))
        return file_name
    '''

    def N50(self, file_name):
        with open(file_name, 'r') as io:
            for line in io:
                line = line.strip()
                fields = line.split("\t")
                if fields[0] == "N50":
                    return fields[1]
        return 0

    def basic_reads_stats(self, file_name):
        stats_list = []
        with open(file_name, 'r') as io:
            for line in io:
                line = line.strip()
                if line == '':
                    continue
                if not line[0] == "#":
                    fields = line.split("\t")
                    stats_list.append(fields[1])
        stats_row_name = ["file_num", "num_of_reads", "num_bases",
                "average_length", "max_length"]
        stats_dict = dict(i for i in zip(stats_row_name, stats_list))
        return stats_dict

    def get_first_match(self, end_with):
        file_list = [i for i in os.listdir(self._proj_path) if i.endswith(end_with)]
        num_of_matchs = len(file_list)
        if num_of_matchs > 1:
            raise RuntimeError("Only one {} file is supported now".format(end_with))
        elif num_of_matchs < 1:
            raise RuntimeError("Cannot find {} file in proj_path".format(end_with))
        else:
            first = os.path.join(self._proj_path, file_list[0])
        return first


    def fastq_qc(self):
        read_distribute = self.get_first_match("reads.distribute.xls")

        read_stats = self.get_first_match("reads.stat.xls")

        fastq_qc = {}
        if self.N50(read_distribute):
            fastq_qc["N50"] = self.N50(read_distribute)
        else:
            raise RuntimeError("Cannot find N50 in read_distribute file")
        fastq_qc.update(self.basic_reads_stats(read_stats))
        # depth = num_bases/3000000000
        fastq_qc['depth'] = "{:4.2f}".format(int(fastq_qc['num_bases'].replace(',',''))/3000000000)

        # length distribut
        read_length_distribute = self.get_first_match("Reads_length_histogram.png")

        self.tpl.replace_pic('sample_id.Reads_length_histogram.png', read_length_distribute)
        # fastq_qc['length_histogram'] = self.get_img(read_length_distribute)

        return fastq_qc

    def basic_bam_stats(self):
        bam_stat_file = self.get_first_match("bam.bc")
        stats_row_name = ["raw_total_sequences", "reads_mapped", "total_length",
                "bases_mapped", "error_rate"]
        stats_list = []
        with open(bam_stat_file,"r") as io:
            bam_stat_dict = {}
            for line in io:
                line = line.strip()
                if line[0:2] == "SN":
                    fields = line.split("\t")
                    key = fields[1].strip(":").replace(" ","_")
                    value = fields[2]
                    if key == "error_rate":
                        value = "{0:.2f}%".format(10*float(value[0:6]))
                    if not key == "error_rate":
                        value = "{:,}".format(int(value))
                    if key in stats_row_name:
                        stats_list.append(value)
                    if len(stats_list) == len(stats_row_name):
                        break
            bam_stat_dict = dict(i for i in zip(stats_row_name, stats_list))
            bam_stat_dict["reads_map_rate"] = "{0:.2f}%".format(100*float(bam_stat_dict["reads_mapped"].replace(',',''))/float(bam_stat_dict["raw_total_sequences"].replace(',','')))
            bam_stat_dict["bases_map_rate"] = "{0:.2f}%".format(100*float(bam_stat_dict["bases_mapped"].replace(',',''))/float(bam_stat_dict["total_length"].replace(',','')))
        return bam_stat_dict

    def sv_num(self):
        read_svnum = self.get_first_match("re4.svnum")
        with open(read_svnum, "r") as io:
            sv_num_dict = {}
            for line in io:
                line = line.strip()
                if not line[0] == "#":
                    fields = line.split("\t")
                    sv_num_dict[fields[0]] = "{:,}".format(int(fields[1]))
        total_sv_num = sum([int(sv_num_dict[k].replace(',','')) for k in sv_num_dict])
        sv_num_dict["Total"] = "{:,}".format(total_sv_num)

        # sv_num bar
        sv_num_barplot = self.get_first_match("re4.svnum.png")
        self.tpl.replace_pic('sample_id.re4.svnum.png', sv_num_barplot)
        return sv_num_dict

    def sv_len(self):
        sv_len_densityplot = self.get_first_match("re4.svlen.png")
        self.tpl.replace_pic('sample_id.re4.svlen.png', sv_len_densityplot)


    def create_report(self):
        """生成报告
        """

        # sv len pic
        self.sv_len()

        content = {
            'proj_info': self.get_proj_info(),
            'fastq_qc': self.fastq_qc(),
            'bam_stat':self.basic_bam_stats(),
            'sv_num': self.sv_num()
        }

        self.tpl.render(content)
        output_file = '{proj_id}_{sample_id}_sv_report_{date}.docx'.format(
            proj_id=self._proj_id,sample_id=self._sample_id,
            date=time.strftime('%Y-%m-%d', time.localtime(time.time())))
        self.tpl.save(os.path.join(self._output_path, output_file))

def get_args():
    parser = argparse.ArgumentParser(prog='基于python docxtpl，SV WORD版报告')
    parser.add_argument('--proj_path', help='项目路径，例如/data/huangjianjun/_work/test_pipline/work/Up_load')
    parser.add_argument('--proj_id', help='项目ID')
    parser.add_argument('--sample_id', help='样本编号')
    parser.add_argument('--customer_institute', help='客户单位，会出现在封面TITLE')
    parser.add_argument('--reporter', help='报告填写人，会出现在封面TITLE', default='苏亚男、郑宇')
    parser.add_argument('--supervisor', help='报告审核人，会出现在封面TITLE', default='梁帆')
    parser.add_argument('--output_path', help='结果目录，报告会存放在该目录下,文件名称： {proj_id}_sv_report_{date}.docx')
    #  parser.add_argument("--verbose", help="increase output verbosity",
                        #  action="store_false")
    if len(sys.argv) <= 1:
        parser.print_help()
        exit()
    return parser.parse_args()


def main():
    args = get_args()
    BASE_DIR = os.path.split(os.path.realpath(__file__))[0]
    template_file = os.path.join(BASE_DIR, 'template/sv_template.docx')
    report = Report(args.proj_id, args.sample_id, args.customer_institute, args.reporter, args.supervisor,
        args.proj_path, template_file, args.output_path)
    report.create_report()

if __name__ == '__main__':
    main()
