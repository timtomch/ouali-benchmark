#!/usr/bin/env python
# coding: utf-8

# Ce script sert à comparer les alignements (et non-alignements) automatiques calculés par Ouali aux données validées fournies
# par RERO où à celles de l'ABES.
# Il s'agit de la conversion du notebook "Ouali benchmark" sous forme de script pour pouvoir être utilisé sur plusieurs instances.
# Le script est appelé avec un seul paramètre: un fichier de config propre à chaque instance et contenant les chemins des fichiers
# à utiliser pour la comparaison:
# python ouali-benchmark.py fichier/de/config.yaml


import pandas as pd
import gc
import yaml
import sys

config_file = str(sys.argv[1])

# Chargement des valeurs du fichier de config
config = yaml.safe_load(open(config_file))

ouali_files = config['Alignements Auto Ouali']
ouali_undefined_files = config['Arbitrages Ouali']
ouali_fields = config['Colonnes Export Ouali']

rero_files = config['Alignements RERO']
rero_concord_file = config['Concordance RERO']
rero_fields = config['Colonnes Export RERO']

abes_files = config['Alignements ABES']
abes_noalign_file = config['Non-alignements ABES']
abes_fields = config['Colonnes Export ABES']

set_name = config['Instance']

output_folder = config['Dossier Export']

common_file = config['Alignements Communs']
common_noalign_file = config['Non-Alignements Communs']
divergences_file = config['Alignements Divergents']
div_noalign_file = config['Non-Alignements Divergents']
missed_file = config['Manquants']


# ### Préparation des données Ouali
# 
# Commençons par charger les données exportées depuis Ouali en les chargeant dans des dataframes.
# 
# Pour tous les chargements de données, on s'assure que Python traite toutes les valeurs comme texte, sinon il va convertir certaines colonnes contenant des identifiants en nombres, ce qui peut poser problème par la suite si on les compare aux mêmes données chargées comme texte ou si on essaie de faire une opération join sur ces colonnes. Pour cela, on spécifie le paramètre `dtype`.

ouali_data = pd.concat((pd.read_csv(f, sep='\t', encoding = "UTF-8", dtype = str) for f in ouali_files))
ouali_undefined_data = pd.concat((pd.read_csv(f, sep='\t', encoding = "UTF-8", dtype = str) for f in ouali_undefined_files))

# On renomme les colonnes des identifiants source et cible comme dans les fichiers RERO, cela simplifiera les opérations de comparaison
ouali_data['source'] = ouali_data['id source']
ouali_undefined_data['source'] = ouali_undefined_data['id source']
ouali_data['cible'] = ouali_data['id cible']

# .copy() est nécessaire pour éviter les erreurs SettingWithCopyWarning
ouali_align = ouali_data.query('`nombre de candidats` != "0" & `décision d\'alignement` == "auto"').copy()
ouali_no_align = ouali_data.query('`nombre de candidats` == "0" & `décision d\'alignement` == "auto"').copy()

print('Résultats du benchmark des alignements Ouali pour l\'instance ' + set_name)
print('----------------------------------------------------------------------------')
print('Alignements Ouali: ' + str(len(ouali_align)))
print('Non-alignements Ouali: ' + str(len(ouali_no_align)))
print('Alignements à arbitrer (pas de décision): ' + str(len(ouali_undefined_data)))


# Avons-nous au moins un fichier RERO? Si non, on passe à la suite
if rero_files is not None:
    if rero_concord_file is not None:

        # ### Préparation des données RERO
        # 
        # Pour la comparaison avec RERO, commençons par charger ces données également dans des dataframes.

        rero_data = pd.concat((pd.read_csv(f, sep='\t', encoding = "ISO-8859-1", dtype = str) for f in rero_files))
        rero_data.columns =[column.replace(" ", "_") for column in rero_data.columns]
        # Vu qu'on peut charger plusieurs fichiers RERO à comparer, il est possible qu'il y ait des doublons entre eux. On les retire ici.
        rero_data.drop_duplicates(subset=['rero_id'],inplace=True)
        rero_concord = pd.read_csv(rero_concord_file, dtype = str)
        print("Nombre de concordances validées dans le fichier RERO: ",len(rero_data))


        # L'identifiant utilisé par RERO n'est pas le même que dans les exports Ouali. Il faut donc commencer par ajouter l'identifiant RNV aux exports RERO pour pouvoir comparer ces alignements à ceux exportés par Ouali.
        # 
        # *Note au sujet de l'affichage d'exemples:*
        # L'usage de la fonction `query` ne fonctionne pas très bien pour extraire quelques exemples de ces données, peut-être à cause des espaces. C'est pourquoi on utilise `loc` et `contains`. Enfn on spécifie `na=False` car ces colonnes contiennent des entrées `NaN` qu'il faut convertir en `False` pour pouvoir utiliser `loc`.

        # Il faut aligner les chiffres dans la colonne `rero_id` du dataframe `rero_data` avec soit ceux trouvés dans `id_rero` ou `id_rero_a` dans `rero_concord`. Pour toutes ces colonnes, il faut tout d'abord enlever les préfixes avant de pouvoir les utiliser comme point de comparaison.

        rero_data['id_rero_join'] = rero_data.rero_id.str.extract('(\d+)')
        rero_concord['id_rero_join'] = rero_concord['id_rero'].fillna(rero_concord['id_rero_a'])
        rero_concord['id_rero_join'] = rero_concord.id_rero_join.str.extract('(\d+)')

        # Maintenant que c'est fait, on peut fusionner les deux tables et ainsi obtenir notre fichier de comparaison. On renomme également les colonnes `id` et  `idref_id` en `source` et `cible` respectivement, qui sont les termes utilisés dans l'export Ouali pour pouvoir les comparer à ce dernier.

        rero_aligns = pd.merge(rero_data, rero_concord, on='id_rero_join', how="inner")
        rero_aligns['source'] = rero_aligns['id']
        rero_aligns['cible'] = rero_aligns['idref_id']
        print('Nombre de concordiances RERO-IdRef validées: ' + str(len(rero_aligns)))


        # Nous avons maintenant un fichier prêt à être utilisé pour la comparaison avec Ouali.

        # ### Comparaison des données Ouali avec RERO

        common_source_rero = pd.merge(rero_aligns, ouali_align, how="inner", on='source', suffixes=("_rero", "_ouali"), copy=True)
        print("Alignements Ouali présents dans fichier RERO: ", len(common_source_rero))

        outfile = output_folder + '/' + common_file + '-RERO-' + set_name + '.csv'
        common_target_rero = pd.merge(rero_aligns, ouali_align, how="inner", on=['source', 'cible'], suffixes=("_rero", "_ouali"), copy=True)
        common_target_rero.to_csv(outfile,columns=['source','cible'] + ouali_fields + rero_fields,encoding="UTF-8",index=False)
        print("Alignements Ouali validés par RERO: ", len(common_target_rero))
        print("Pourcentage validé: ", round(len(common_target_rero)/len(common_source_rero)*100,1), "%")
        print("Exportés dans ", outfile)


        # #### Différences entre Ouali et RERO

        outfile = output_folder + '/' + divergences_file + '-RERO-' + set_name + '.csv'
        divergences_rero = common_source_rero.loc[~(common_source_rero['cible_rero'] == common_source_rero['cible_ouali'])]
        divergences_rero.to_csv(outfile,columns=['source','cible_ouali','cible_rero'] + ouali_fields + rero_fields,encoding="UTF-8",index=False)
        print("Alignements Ouali qui diffèrent dans RERO: ", len(divergences_rero))
        print("Pourcentage non-validé: ", round(len(divergences_rero)/len(common_source_rero)*100,1), "%")
        print("Exportés dans ", outfile)


        outfile = output_folder + '/' + div_noalign_file + '-RERO-' + set_name + '.csv'
        div_nonalign_rero = pd.merge(rero_aligns, ouali_no_align, how="inner", on='source', suffixes=("_rero", "_ouali"), copy=True)
        div_nonalign_rero.to_csv(outfile,columns=['source','cible_ouali','cible_rero'] + ouali_fields + rero_fields,encoding="UTF-8",index=False)
        print("Non-alignements Ouali erronés: ", len(div_nonalign_rero))
        print("Exportés dans ", outfile)


        outfile = output_folder + '/' + missed_file + '-RERO-' + set_name + '.csv'
        missed_rero = pd.merge(rero_aligns, ouali_undefined_data, how="inner", on='source', suffixes=("_rero", "_ouali"), copy=True)
        missed_rero.to_csv(outfile,columns=['source','cible'] + rero_fields,encoding="UTF-8",index=False)
        print("Alignements manqués: ", len(missed_rero))
        print("Exportés dans ", outfile)


        # Pour finir, faisons un peu d'ordre en effacant de la mémoire les dataframes utilisés pour la comparaison avec RERO avant de passer aux données ABES.

        del rero_data, rero_concord, rero_aligns, common_source_rero, common_target_rero, divergences_rero, div_nonalign_rero, missed_rero
        gc.collect()

    else:
        print("ERREUR le benchmark avec RERO n'est possible qu'avec un fichier de concordance RERO-ATC!")


# Avons-nous au moins un fichier ABES? Si non, on passe à la suite
if abes_files is not None:
    
    # ### Préparation des données ABES

    abes_align = pd.concat((pd.read_csv(f, dtype = str) for f in abes_files))
    print("Nombre de concordances validées dans le fichier ABES: ",len(abes_align))
    
    if abes_noalign_file is not None:
        abes_noalign = pd.concat((pd.read_csv(f, dtype = str) for f in abes_noalign_file))
        print("Nombre de non-alignements validés dans le fichier ABES: ",len(abes_noalign))
        noalign_comp = True
    else:
        print("ALERTE: Aucun fichier de non-alignement fourni pour l'ABES - seules les concordances seront comparées.")
        noalign_comp = False


    # ### Comparaison des données Ouali avec l'ABES
    # 
    # Suivant le type de données fournies par l'ABES, il est nécessaire de préparer les données
    #
    
    if 'ID_EC' in abes_align:
        # Dans les "alignements sûrs" de l'ABES, l'identifiant RNV est au milieu de la chaîne de caractères présents dans la colonne `ID_EC`. Il faut donc extraire ces chiffres et les placer dans une nouvelle colonne `source` pour pouvoir les comparer à Ouali. On renomme également la colonne `IdRef` en `cible` pour faciliter la comparaison. On fait la même chose pour le fichier des non-alignements.
        abes_align['source']=abes_align['ID_EC'].str.extract(r'(\d{18})')
        abes_align['cible']=abes_align['IdRef']
    elif 'auth_id' in abes_align:
        # Dans les alignements expérimentaux, les colonnes sont celles fournies par Renouvaud. Dans ce cas, l'identifiant RNV est dans une colonne 'auth_id'
        abes_align['source']=abes_align['auth_id']
        abes_align['cible']=abes_align['IdRef_CANDIDAT']
        # De plus, dans ce type de fichier, il peut y avoir des doublons (dû à la méthode d'export SQL)
        abes_align.drop_duplicates(['source','cible'],keep= 'first',inplace=True)
    else:
        print("ERREUR format de fichier ABES non-reconnu!")
        sys.exit()

    if noalign_comp : abes_noalign['source']=abes_noalign['ID_EC'].str.extract(r'(\d{18})')

    common_source_abes = pd.merge(abes_align, ouali_align, how="inner", on='source', suffixes=("_abes", "_ouali"), copy=True)
    print("Alignements Ouali présents dans fichier ABES: ", len(common_source_abes))
    
    if noalign_comp : common_source_noalign_abes = pd.merge(abes_noalign, ouali_no_align, how="inner", on='source', suffixes=("_abes", "_ouali"), copy=True)


    outfile = output_folder + '/' + common_file + '-ABES-' + set_name + '.csv'
    common_target_abes = pd.merge(abes_align, ouali_align, how="inner", on=['source', 'cible'], suffixes=("_abes", "_ouali"), copy=True)
    
    try:
        common_target_abes.to_csv(outfile,columns=['source','cible'] + ouali_fields + abes_fields,encoding="UTF-8",index=False)
    except:
        print("ERREUR colonnes " + ouali_fields.join(',') + '; ' + abes_fields.join(',') + " non reconnues")
        sys.exit()
        
    print("Alignements Ouali validés par l'ABES: ", len(common_target_abes))
    print("Pourcentage validé: ", round(len(common_target_abes)/len(common_source_abes)*100,1), "%")
    print("Exportés dans ", outfile)

    if noalign_comp :

        outfile = output_folder + '/' + common_noalign_file + '-ABES-' + set_name + '.csv'
        common_source_noalign_abes.to_csv(outfile,columns=['source'],encoding="UTF-8",index=False)
        print("Non-alignements Ouali: ", len(ouali_no_align))
        print("Non-alignements Ouali communs avec l'ABES: ", len(common_source_noalign_abes))
        print("Pourcentage validé: ", round(len(common_source_noalign_abes)/len(ouali_no_align)*100,1), "%")
        print("Exportés dans ", outfile)


    # #### Différences entre Ouali et l'ABES

    outfile = output_folder + '/' + divergences_file + '-ABES-' + set_name + '.csv'
    # Alignements pour lesquels Ouali et l'ABES ont pris une décision différente (cible différente pour une même source)
    divergences_abes = common_source_abes.loc[~(common_source_abes['cible_abes'] == common_source_abes['cible_ouali'])]
    
    try:
        divergences_abes.to_csv(outfile,columns=['source','cible_ouali','cible_abes'] + ouali_fields + abes_fields,encoding="UTF-8",index=False)
    except:
        print("ERREUR colonnes " + ouali_fields.join(',') + '; ' + abes_fields.join(',') + " non reconnues")
        sys.exit()
        
    if noalign_comp :
        # Notices qu'Ouali a alignées, mais l'ABES a pris une décision de non-alignement
        divergences_NOT_abes = pd.merge(abes_noalign, ouali_align, how="inner", on=['source'], suffixes=("_abes", "_ouali"), copy=True)
        divergences_NOT_abes['cible_ouali'] = divergences_NOT_abes['cible']
        divergences_NOT_abes.insert(0,'cible_abes', "NaN")

        # On ajoute à ce même fichier les cas où l'ABES a pris une décision de non-alignement (mode 'a' - append)
        try:
            divergences_NOT_abes.to_csv(outfile,columns=['source','cible_ouali','cible_abes'] + ouali_fields + abes_fields ,encoding="UTF-8",index=False, mode='a')
        except:
            print("ERREUR colonnes " + ouali_fields.join(',') + '; ' + abes_fields.join(',') + " non reconnues")
            sys.exit()

    print("Alignements Ouali qui diffèrent dans l'ABES: ", len(divergences_abes))
    print("Pourcentage avec alignement différent: ", round(len(divergences_abes)/len(common_source_abes)*100,1), "%")
    if noalign_comp : print("Alignements Ouali qui sont non-alignés par l'ABES: ", len(divergences_NOT_abes))
    if noalign_comp : print("Pourcentage avec décision d'alignement différente: ", round(len(divergences_NOT_abes)/len(ouali_align)*100,1), "%")
    print("Exportés dans ", outfile)

    outfile = output_folder + '/' + div_noalign_file + '-ABES-' + set_name + '.csv'

    # Non-alignements Ouali pour lesquels l'ABES a trouvé un alignement
    div_nonalign_abes = pd.merge(abes_align, ouali_no_align, how="inner", on='source', suffixes=("_abes", "_ouali"), copy=True)
    
    try:
        div_nonalign_abes.to_csv(outfile,columns=['source','cible_ouali','cible_abes'] + ouali_fields + abes_fields ,encoding="UTF-8",index=False)
    except:
        print("ERREUR colonnes " + ouali_fields.join(',') + '; ' + abes_fields.join(',') + " non reconnues")
        sys.exit()
        
    print("Non-alignements Ouali erronés: ", len(div_nonalign_abes))
    print("Pourcentage de divergence: ", round(len(div_nonalign_abes)/len(ouali_no_align)*100,1), "%")

    print("Exportés dans ", outfile)

    outfile = output_folder + '/' + missed_file + '-ABES-' + set_name + '.csv'

    # Alignements manqués
    missed_abes = pd.merge(abes_align, ouali_undefined_data, how="inner", on='source', suffixes=("_abes", "_ouali"), copy=True)
    
    try:
        missed_abes.to_csv(outfile,columns=['source','cible'] + abes_fields,encoding="UTF-8",index=False)
    except:
        print("ERREUR colonnes " + abes_fields.join(',') + " non reconnues")
        sys.exit()

    if noalign_comp :
        # Non-alignements manqués
        missed_noalign_abes = pd.merge(abes_noalign, ouali_undefined_data, how="inner", on='source', suffixes=("_abes", "_ouali"), copy=True)
        missed_noalign_abes.insert(0,'cible', "NaN")
        
        try:
            missed_noalign_abes.to_csv(outfile,columns=['source','cible'] + abes_fields,encoding="UTF-8",index=False,mode='a')
        except:
            print("ERREUR colonnes " + abes_fields.join(',') + " non reconnues")
            sys.exit()
        
    print("Alignements manqués: ", len(missed_abes))
    if noalign_comp : print("Non-alignements manqués: ", len(missed_noalign_abes))
    print("Exportés dans ", outfile)