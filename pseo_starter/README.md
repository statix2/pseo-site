
# pSEO Starter (Google Sheet → Site statique → GitHub Pages)

**But :** créer un petit annuaire local entièrement statique, généré automatiquement depuis un Google Sheet, et le publier gratuitement sur GitHub Pages. Pas de serveur, pas de frais (0 €), optionnellement un nom de domaine plus tard.

## Étapes ultra simples

1. **Duplique** ce dossier dans un nouveau dépôt GitHub (bouton "Add file" → "Upload files" ou via Git).  
2. Ouvre `config.json` et remplace `base_url` par ton URL GitHub Pages (ex. `https://ton-user.github.io/ton-repo`).  
3. Crée un **Google Sheet** avec ces colonnes exactes : `name,address,city,lat,lon,hours,features,photo_url,website_url`.  
4. Dans Google Sheets : *Fichier → Partager → Lien : Lecteur* puis *Fichier → Publier sur le web → Valeurs séparées par des virgules (.csv)*, copie l'URL et colle-la dans `sheet_csv_url`.  
5. (Optionnel) Si tu as un tag Amazon Partenaires, remplace `REPLACE_WITH_YOUR_TAG-21` dans `config.json`. Sinon laisse vide pour ne pas afficher le bloc d’affiliation.  
6. Pousse (commit/push) sur la branche `main`. La première exécution de GitHub Actions va **construire** le site et le **déployer** automatiquement.  
7. Active **Pages** si besoin : *Settings → Pages → Build and deployment → Source = GitHub Actions*.  
8. Ton site sera disponible à l’adresse indiquée. Les mises à jour du Google Sheet seront prises en compte **chaque jour** (cron) et à chaque push.

## Lancer en local (optionnel)
- Avoir Python 3.11+ installé.  
- `python generator.py` → les fichiers statiques apparaissent dans `public/`.

## Données d’exemple
`data/points.csv` contient 4 lieux pour tests. Une fois ton Sheet en place, la génération utilisera le CSV **du Sheet** automatiquement.

## Important
- Utiliser des données réutilisables légalement (open data, relevés perso).  
- Ne pas copier de textes d’autres sites.  
- Ajouter une phrase "Ce site peut contenir des liens d’affiliation" (déjà en footer).  
- Pour de la pub (AdSense), il faudra un nom de domaine et respecter le RGPD (bandeau cookies).

Bon build !
