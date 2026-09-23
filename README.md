# English version first, French version right after

# PlanningDKIT En

A litte tools in cmd who can create your own weekly schedule from here : https://timetables.dkit.ie/studentset.php
Whithout go to the timetables.

## Why ?
Cause i was tired to search throuth this labyrinthe of schedules.

## How it work

So it use the `js/filter.min.js` who were create by the website directly in your nav.
The tools just use them to see the differents groups and re-create the validation btn
"View Timetable" (by `process.php` from the website) to claim it, group after group,
the tools gonna create a list of the courses you enter previously, from Mon to Fri.

For every courses you want, you have to respect this parameter style on the cmd input :
Every line correspond to a `Course` and a `Group` so you have to enter in the line :
`Course | Groupe`

for exemple this case of input :

"Universal Design Project | Level 8: BSc (Hons) in Computing in Games Development Year 3 - Sem 1"

If your `Group` contain ": BSc", this will work as well too : ":BSc"

For every line, it will :
1. Find the good course, if you enter it wrong it will propose you different solutions;
2. Download the complete schedule of the week;
3. Finds the session(s) of the requested course;
4. adds them to the final schedule, grouped by day and sorted by time.

Stop will say it's the end of the input, time for the application to to the job

Also, the start of the output is in french, here is a quick traduction :

```md
Enter your courses, one per line in format :
    Name of the course | Name of the group
Enter stop alone in a line when you finished
```

## Installation

```powershell
pip install -r requirements.txt
```

## Use

```powershell
python main.py
```

And enter your courses, one per line :

```
Universal Design Project | Level 8:BSc (Hons) in Computing in Games Development Year 3 - Sem 1
Static Web Development | Level 8: BSc (Hons) in Computing in Games Development Year 1 Group 1a - Sem 1
Stop
```

final planning will be in `planning.txt`.

## Structure

- `main.py` - Start and the while input.
- `dkit_timetable/catalog.py` - Claim and parse the list of the groups.
- `dkit_timetable/scraper.py` - Claim and parse the schedule of one group.
- `dkit_timetable/matching.py` - Try to match what you wrote in the input.
- `dkit_timetable/output.py` - Create your own schedule.



# PlanningDKIT Fr

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

- `main.py` - point d'entrée, boucle interactive.
- `dkit_timetable/catalog.py` - récupère et parse la liste des groupes.
- `dkit_timetable/scraper.py` - récupère et parse le planning d'un groupe.
- `dkit_timetable/matching.py` - recherche approximative cours/groupe.
- `dkit_timetable/output.py` - construit le texte du planning final.
