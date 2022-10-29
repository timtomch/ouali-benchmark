#!/usr/bin/env python
# coding: utf-8

# Ce script sert à compter le nombre d'alignements manuels, automatiques et externes dans les rapports CSV produits par Ouali.
# Il est utile pour générer rapidement un rapport sur les alignements.
# Le script est appelé avec un seul paramètre: un fichier de config avec la liste des rapports à traiter:
# python ouali-stats.py fichier/de/config.yaml


import pandas as pd
import yaml
import sys
import re
from tabulate import tabulate

config_file = str(sys.argv[1])

# Chargement des valeurs du fichier de config
config = yaml.safe_load(open(config_file))

ouali_established_files = config['Alignements effectués']
ouali_undefined_files = config['Alignements à traiter']


counts = {}

for infile in ouali_established_files:
    instance_name = re.search(r'(\w+-\w+)',infile).group()
    ouali_data = pd.read_csv(infile, sep='\t', dtype = str)
    ouali_align = ouali_data.query('`nombre de candidats` != "0"').copy()
    ouali_counts = ouali_align['décision d\'alignement'].value_counts(sort=False)
    ouali_notalign = ouali_data.query('`nombre de candidats` == "0"').copy()
    ouali_notcounts = ouali_notalign['décision d\'alignement'].value_counts(sort=False)
    counts.update({instance_name:{"Alignements":ouali_counts,"Non-concordances":ouali_notcounts}})

count_table = pd.DataFrame(counts)


for infile in ouali_undefined_files:
    instance_name = re.search(r'(\w+-\w+)',infile).group()
    ouali_data = pd.read_csv(infile, sep='\t', dtype = str).shape[0]
    count_table.at["à faire",instance_name] = ouali_data

print(tabulate(count_table.T,headers="keys"))