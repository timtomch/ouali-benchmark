#!/usr/bin/env python
# coding: utf-8

# Ce script sert à convertir les rapports Ouali vers le format utilisé par RERO pour chargement des alignements dans leur
# base de données. Seuls les alignements MANUELS sont exportés.
# Le script est appelé avec un seul paramètre: un fichier de config contenant les chemins des fichiers à utiliser pour
# l'export et le recoupement avec les identifiants RERO:
# python ouali-benchmark.py fichier/de/config.yaml


import pandas as pd
import yaml
import sys
import re

config_file = str(sys.argv[1])

# Chargement des valeurs du fichier de config
config = yaml.safe_load(open(config_file))

ouali_files = config['Alignements Ouali']
rero_concord_file = config['Concordance RERO']
output_folder = config['Dossier Export']
output_file = config['Fichier Export']

# Si aucun nom de fichier export n'est spécifié, on passe en mode export séparé et un fichier d'export distinct sera généré
# pour chaque rapport Ouali.
if output_file is None:
    sep_export = True
else:    
    outfile = output_folder + '/' + output_file
    sep_export = False

rero_concord = pd.read_csv(rero_concord_file, dtype = str)
rero_concord['id_rero_join'] = rero_concord['id_rero'].fillna(rero_concord['id_rero_a'])
rero_concord['id_rero_join'] = rero_concord.id_rero_join.str.extract('(\d+)')

for infile in ouali_files:
    ouali_data = pd.read_csv(infile, sep='\t', dtype = str)
    ouali_align = ouali_data.query('`décision d\'alignement` == "manuel"').copy()
    print('Alignements manuels dans le fichier ' + infile + ' : ' + str(len(ouali_align)))
    output_data = pd.merge(ouali_align, rero_concord, left_on='id source', right_on='id', how='inner')
    output_data['id rnv']=output_data['id source']
    output_data['id rero']=output_data['id_rero_join']
    output_data['id idref']=output_data['id cible']
    output_data['type']= ''
    print('   dont alignements avec concordance RERO : ' + str(len(output_data)))
    if len(output_data) > 0:
        if sep_export:
            outfile = output_folder + '/' + re.search("\/(.*)\.tsv",infile).group(1) + '_export-RERO.tsv'
            output_data.to_csv(outfile,columns=['id rero','id idref', 'type'],encoding="UTF-8",sep='\t',index=False)
        else:
            output_data.to_csv(outfile,columns=['id rero','id idref', 'type'],encoding="UTF-8",sep='\t',index=False, mode='a')
        print('Sauvergardés dans ' + outfile)