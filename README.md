# PlanningDKIT

Petit outil en ligne de commande qui construit un planning hebdomadaire
personnalisé à partir du site des horaires du DKIT
(https://timetables.dkit.ie/studentset.php), sans passer par l'interface web.

## Comment ça marche

Le site publie la liste complète des "Student Group(s) to view" dans un
fichier JavaScript (`js/filter.min.js`) chargé par le navigateur. L'outil
télécharge et lit ce fichier pour connaître tous les groupes disponibles,
puis reproduit l'appel réseau fait par le bouton "View Timetable" (via le
même proxy `process.php` que le site utilise) pour récupérer, groupe par
groupe, le planning au format "List Format", sur la semaine en cours, du
lundi au vendredi, 09:00-18:00.

Pour chaque ligne `Cours | Groupe` que vous saisissez, l'outil :
1. retrouve le groupe correspondant dans le catalogue (recherche exacte,
   puis approximative avec confirmation si ambigu) ;
2. télécharge (et met en cache) le planning complet de ce groupe ;
3. y retrouve la ou les séances du cours demandé ;
4. les ajoute au planning final, regroupées par jour et triées par heure.

## Installation

```powershell
pip install -r requirements.txt
```

## Utilisation

```powershell
python main.py
```

Puis entrez vos cours, un par ligne :

```
Universal Design Project | Level 8:BSc (Hons) in Computing in Games Development Year 3 - Sem 1
Static Web Development | Level 8:BSc (Hons) in Computing in Games Development Year 1 Group 1a - Sem 1
Stop
```

Le planning final s'affiche dans le terminal et est enregistré dans
`planning.txt`.

## Structure

- `main.py` — point d'entrée, boucle interactive.
- `dkit_timetable/catalog.py` — récupère et parse la liste des groupes.
- `dkit_timetable/scraper.py` — récupère et parse le planning d'un groupe.
- `dkit_timetable/matching.py` — recherche approximative cours/groupe.
- `dkit_timetable/output.py` — construit le texte du planning final.
