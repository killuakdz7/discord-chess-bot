# Discord Chess Bot

Un bot Discord intégrant l'API Chess.com et permettant de jouer aux échecs avec un plateau graphique.

## Installation
1. Clone ce repo : `git clone https://github.com/tonusername/discord-chess-bot.git`
2. Installe les dépendances : `pip install -r requirements.txt`
3. Ajoute ton token Discord dans `main.py` (variable TOKEN).
4. Lance : `python main.py`

## Commandes
- !player <username> : Profil d'un joueur.
- !stats <username> : Stats d'un joueur.
- !games <username> : Liste des parties récentes.
- !clubs <username> : Clubs d'un joueur.
- !tournaments <username> : Tournois d'un joueur.
- !club <club_id> : Profil d'un club.
- !club_members <club_id> : Membres d'un club.
- !tournament <tournament_id> : Infos sur un tournoi.
- !team_match <match_id> : Infos sur un match par équipe.
- !country <iso_code> : Profil d'un pays.
- !country_players <iso_code> : Joueurs d'un pays.
- !daily_puzzle : Puzzle quotidien.
- !startchess @opponent : Démarre une partie d'échecs.
- !move <move> (ex. e2e4) : Fait un move dans la partie en cours.
- !resign : Abandonne la partie.
- !board : Affiche le plateau actuel.

Note : Les IDs pour clubs/tournois/matchs sont des slugs (ex. "chess-com-francais" pour un club).
