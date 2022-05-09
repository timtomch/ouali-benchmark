# Benchmark des alignements Ouali

Le [réseau de bibliothèques Renouvaud](https://www.bcu-lausanne.ch/mandats/) regroupe 139 institutions dans le canton de Vaud, en Suisse. 
En 2021, la coordination du réseau Renouvaud a entamé un projet de migration de registres d’autorités locales vers le référentiel 
[IdRef](https://www.idref.fr/). 

L'outil Ouali a été développé par l'entrprise [Datuman](http://datuman.ch/) pour mener à bien ce projet. Ouali remplit deux missions:

* Alignement automatique des notices d’autorité provenant des registres locaux vers IdRef
* Aide à l’alignement manuel (arbitrage) lorsqu’un alignement automatique est impossible

Ce dossier GitHub contient des scripts utiles à comparer le résultat de l'alignement automatique d'Ouali aux alignements validés
fournis par RERO ainsi que ceux calculés par l'ABES. Au fur et à mesure des améliorations sur l'algorithme Ouali, ces scripts sont
utilisés pour mesurer s'il y a amélioration ou non.

## Utilisation

Le script à appeler est `ouali-benchmark.py`. Celui-ci prend pour seul argument un fichier de configuration YAML qui définit
le nom des fichiers à utiliser pour la comparaison de chaque instance Ouali. Les chemins vers ces fichiers doivent être relatifs
au script `ouali-benchmark.py`.

Exemple:

```
python ouali-benchmark.py config/nomsATC.yaml
```

Le résultat de l'analyse est affiché sur la ligne de commande lors de l'exécution du script. Ce dernier génère une série de fichiers
(dans un dossier spécifié en config) comportant les alignements communs et divergents entre Ouali et les sets comparés.