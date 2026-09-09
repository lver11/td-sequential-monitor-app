# 🏛️ CIO TD Monitor

## Version web déployable

Le dépôt contient une interface web autonome avec watchlist éditable, univers d'indices,
matières premières, devises, taux, données Yahoo Finance, résumé des signaux, alertes locales et
export CSV. Le point d'entrée local est `index.html` servi par `server.py`.

### Déploiement gratuit recommandé

Le dossier `functions/` permet de publier la même interface sur Cloudflare Pages. Crée un projet
Pages connecté à ce dépôt, choisis le dossier racine comme répertoire de publication et ne mets
aucune commande de build. Cloudflare servira `index.html` et la Function `/api/chart` sur le même
domaine, donc l'interface restera identique à la version locale.

Une version Streamlit est également disponible dans `streamlit_app.py`, mais son apparence diffère
de l'interface web locale.

Voir [DEPLOIEMENT.md](./DEPLOIEMENT.md) pour publier l'application.

Outil d'analyse de l'épuisement des tendances (TD Sequential) pour Luc Verville.
- **Setup (9)** : Phase de préparation.
- **Countdown (13)** : Signal de retournement.
