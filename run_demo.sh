proj_path=/export/sdb1/suyanan/project/BJXWZ-20171204001Y/03_M18A1522_wangjinfeng_daughter/M18A1522/stat
proj_id="BJXWZ-20171204001Y"
sample_id="M18A1522"
customer_institute="国家卫生计生委科学技术研究所"
output_path=/export/sdb1/suyanan/project/BJXWZ-20171204001Y/03_M18A1522_wangjinfeng_daughter

#default value
reporter="苏亚男、郑宇"
supervisor="李丕栋"

python3 /data/grandanalysis/grandwordreport/sv_word_report.py --proj_path ${proj_path} --proj_id ${proj_id} --sample_id ${sample_id} --customer_institute ${customer_institute} --output_path ${output_path}
