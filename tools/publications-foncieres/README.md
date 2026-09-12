# Publications foncières — Corsier (1246)

Petit outil personnel pour suivre les publications foncières genevoises
concernant la commune de Corsier.

## Ce que cet outil fait, et ne fait pas

Le site publications-foncieres.app.ge.ch est protégé par un captcha. Cet outil
**ne le contourne pas**. C'est toi qui ouvres le site, passes le captcha et
lances la recherche, comme n'importe quel visiteur. Le script se contente de
recopier les résultats déjà affichés à l'écran dans un CSV, et de te dire ce
qui est nouveau depuis la dernière fois.

Autrement dit: l'humain fait la consultation, la machine fait la recopie.

Rappel utile: ces publications contiennent des noms et des montants. L'usage
prévu ici est personnel. Rediffuser ces données, les recouper ou les exploiter
commercialement relève de la protection des données et n'est pas le même sujet.

## Utilisation

Une seule commande, sur ta propre machine:

```bash
cd tools/publications-foncieres
./start.sh
```

Au premier lancement le script installe ce qu'il faut et cherche un navigateur
déjà présent (Chrome, Chromium ou Edge) avant d'en télécharger un. Ensuite il
se contente de lancer la capture.

Pour forcer un navigateur précis: `export PF_CHROMIUM="/chemin/vers/chrome"`.

Un navigateur s'ouvre. Tu passes le captcha, tu lances ta recherche pour
Corsier, tu laisses les résultats affichés, tu reviens dans le terminal et tu
appuies sur Entrée.

Si les résultats tiennent sur plusieurs pages, le script te demande après
chaque capture si tu veux en faire une autre: réponds `o`, tourne la page dans
le navigateur, et recommence. Les doublons entre pages sont éliminés.

Le script écrit alors dans `data/captures/` :

- `AAAAMMJJ-HHMMSS.html` — la page brute, archivée telle quelle
- `AAAAMMJJ-HHMMSS.csv` — les lignes concernant Corsier
- `AAAAMMJJ-HHMMSS-nouveautes.csv` — uniquement ce qui n'était pas là avant

Le site est mis à jour le vendredi en principe, donc une passe par semaine
suffit. Le profil du navigateur est conservé dans `data/browser-profile/`, ce
qui évite parfois de refaire le captcha à chaque fois.

### Options utiles

Tout argument passé à `start.sh` est transmis au script:

```bash
./start.sh --no-filter                       # voir toutes les lignes lues
./start.sh --filter 'corsier|anieres'        # élargir à une autre commune
./start.sh --from-html data/captures/20260912-140000.html   # relire une archive
./start.sh --list                            # lister les captures passées
```

Le filtre par défaut est le mot « corsier » seul. Le code postal 1246 n'est
volontairement pas dans le filtre: il apparaît aussi comme numéro de parcelle
dans d'autres communes, ce qui ramènerait des voisins par erreur.

## À lancer sur ta machine

Ce script ouvre une fenêtre de navigateur que tu dois voir et utiliser. Il n'a
donc de sens que sur ton propre ordinateur, pas dans une session distante.

## État actuel et étape suivante

La lecture de la page est **générique**: le script cherche d'abord un tableau,
sinon des blocs répétés, sinon des lignes de texte. Elle a été testée sur des
pages factices reproduisant ces cas, y compris le passage complet par le
navigateur, la pagination et la détection des nouveautés. Elle n'a pas été
testée sur le vrai site, qui n'était pas accessible au moment de l'écriture.

Concrètement: la première capture réelle marchera probablement, mais les
colonnes seront peut-être mal découpées. Envoie le fichier `.html` archivé de
ta première capture et le découpage pourra être écrit précisément — date,
commune, parcelle, nature, montant dans leurs propres colonnes.

## Sources officielles

- [Consulter les publications foncières](https://www.ge.ch/consulter-registre-foncier/consulter-publications-foncieres)
- [Feuille d'avis officielle (FAO)](https://www.ge.ch/feuille-avis-officielle-fao), qui publie les mêmes transactions en PDF
- [Accès en ligne Intercapi / Terravis](https://www.ge.ch/consulter-registre-foncier/demander-acces-ligne-intercapi-portail-terravis), pour un accès conventionné
