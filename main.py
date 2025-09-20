import discord
from discord.ext import commands
import requests
import chess
import chess.svg
import io
import cairosvg
from PIL import Image

# Configuration
TOKEN = 'TON_TOKEN_DISCORD_ICI'  # Remplace par ton token
API_BASE = 'https://api.chess.com/pub/'

# Styles CSS pour "ultra graphique" : gradients, ombres, couleurs vives
CUSTOM_STYLE = """
.board {
    fill: url(#woodGradient);
    stroke: #333;
    stroke-width: 2;
}
.light { fill: #f0d9b5; }
.dark { fill: #b58863; }
.piece { filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5)); }
#woodGradient {
    stop-color1: #d2a679;
    stop-color2: #8b5e3c;
}
"""

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

# Stockage des parties en cours (clé: channel_id)
games = {}

@bot.event
async def on_ready():
    print(f'Bot connecté : {bot.user}')

# Fonction pour appeler l'API Chess.com
async def api_call(ctx, endpoint):
    try:
        response = requests.get(API_BASE + endpoint)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        await ctx.send(f"Erreur API : {e}")
        return None

# Commandes pour l'API Chess.com
@bot.command()
async def player(ctx, username: str):
    data = await api_call(ctx, f'player/{username}')
    if data:
        embed = discord.Embed(title=f"Profil de {username}", color=0x00ff00)
        embed.add_field(name="Nom", value=data.get('name', 'N/A'), inline=True)
        embed.add_field(name="Statut", value=data.get('status', 'N/A'), inline=True)
        embed.add_field(name="Followers", value=data.get('followers', 'N/A'), inline=True)
        await ctx.send(embed=embed)

@bot.command()
async def stats(ctx, username: str):
    data = await api_call(ctx, f'player/{username}/stats')
    if data:
        embed = discord.Embed(title=f"Stats de {username}", color=0x00ff00)
        for cat, stats in data.items():
            if isinstance(stats, dict) and 'last' in stats:
                embed.add_field(name=cat.capitalize(), value=f"Rating: {stats['last']['rating']}", inline=False)
        await ctx.send(embed=embed)

@bot.command()
async def games(ctx, username: str):
    data = await api_call(ctx, f'player/{username}/games/archives')
    if data and 'archives' in data:
        recent = data['archives'][-1] if data['archives'] else 'Aucune'
        await ctx.send(f"Archives de parties pour {username}: {recent}")
    # Pour télécharger PGN : utiliser /player/{username}/games/{yyyy}/{mm}

@bot.command()
async def clubs(ctx, username: str):
    data = await api_call(ctx, f'player/{username}/clubs')
    if data and 'clubs' in data:
        clubs_list = '\n'.join([club['@id'].split('/')[-1] for club in data['clubs']])
        await ctx.send(f"Clubs de {username}:\n{clubs_list}")

@bot.command()
async def tournaments(ctx, username: str):
    data = await api_call(ctx, f'player/{username}/tournaments')
    if data and 'tournaments' in data:
        tourn_list = '\n'.join([tourn['@id'].split('/')[-1] for tourn in data['tournaments']])
        await ctx.send(f"Tournois de {username}:\n{tourn_list}")

@bot.command()
async def club(ctx, club_id: str):
    data = await api_call(ctx, f'club/{club_id}')
    if data:
        embed = discord.Embed(title=f"Club: {data['name']}", color=0x00ff00)
        embed.add_field(name="Membres", value=data.get('members_count', 'N/A'), inline=True)
        await ctx.send(embed=embed)

@bot.command()
async def club_members(ctx, club_id: str):
    data = await api_call(ctx, f'club/{club_id}/members')
    if data and 'all_time' in data:
        members = '\n'.join([m['username'] for m in data['all_time'][:5]])  # Limite à 5
        await ctx.send(f"Membres du club {club_id}:\n{members}...")

@bot.command()
async def tournament(ctx, tournament_id: str):
    data = await api_call(ctx, f'tournament/{tournament_id}')
    if data:
        embed = discord.Embed(title=f"Tournoi: {data['name']}", color=0x00ff00)
        embed.add_field(name="Statut", value=data.get('status', 'N/A'), inline=True)
        await ctx.send(embed=embed)

@bot.command()
async def team_match(ctx, match_id: str):
    data = await api_call(ctx, f'team-match/{match_id}')
    if data:
        await ctx.send(f"Match: {data['name']} - Équipes: {', '.join([team['@id'].split('/')[-1] for team in data['teams']])}")

@bot.command()
async def country(ctx, iso_code: str):
    data = await api_call(ctx, f'country/{iso_code.upper()}')
    if data:
        await ctx.send(f"Pays {iso_code}: {data['name']}")

@bot.command()
async def country_players(ctx, iso_code: str):
    data = await api_call(ctx, f'country/{iso_code.upper()}/players')
    if data and 'players' in data:
        players = '\n'.join(data['players'][:5])
        await ctx.send(f"Joueurs de {iso_code}:\n{players}...")

@bot.command()
async def daily_puzzle(ctx):
    data = await api_call(ctx, 'puzzle')
    if data:
        await ctx.send(f"Puzzle quotidien: {data['title']} - {data['url']}")

# Commandes pour jouer aux échecs
@bot.command()
async def startchess(ctx, opponent: discord.Member):
    if ctx.channel.id in games:
        await ctx.send("Une partie est déjà en cours dans ce channel.")
        return
    games[ctx.channel.id] = {
        'board': chess.Board(),
        'white': ctx.author,
        'black': opponent,
        'turn': chess.WHITE
    }
    await ctx.send(f"Partie démarrée : {ctx.author.mention} (Blancs) vs {opponent.mention} (Noirs).")
    await send_board(ctx)

@bot.command()
async def move(ctx, move_str: str):
    if ctx.channel.id not in games:
        await ctx.send("Aucune partie en cours.")
        return
    game = games[ctx.channel.id]
    if (game['turn'] == chess.WHITE and ctx.author != game['white']) or (game['turn'] == chess.BLACK and ctx.author != game['black']):
        await ctx.send("Ce n'est pas ton tour !")
        return
    try:
        move = game['board'].parse_san(move_str)
        game['board'].push(move)
        game['turn'] = not game['turn']
        await send_board(ctx)
        if game['board'].is_checkmate():
            winner = game['white'] if game['turn'] == chess.BLACK else game['black']
            await ctx.send(f"Échec et mat ! {winner.mention} gagne.")
            del games[ctx.channel.id]
        elif game['board'].is_stalemate():
            await ctx.send("Pat ! Match nul.")
            del games[ctx.channel.id]
    except ValueError:
        await ctx.send("Move invalide. Exemple : e2e4 ou Nf3.")

@bot.command()
async def resign(ctx):
    if ctx.channel.id in games:
        del games[ctx.channel.id]
        await ctx.send(f"{ctx.author.mention} abandonne la partie.")

@bot.command()
async def board(ctx):
    if ctx.channel.id in games:
        await send_board(ctx)
    else:
        await ctx.send("Aucune partie en cours.")

# Fonction pour envoyer le plateau graphique
async def send_board(ctx):
    game = games[ctx.channel.id]
    lastmove = game['board'].peek() if game['board'].move_stack else None
    check = game['board'].king(game['turn']) if game['board'].is_check() else None

    svg_data = chess.svg.board(
        board=game['board'],
        lastmove=lastmove,
        check=check,
        size=400,
        style=CUSTOM_STYLE,
        borders=True,
        coordinates=True
    )

    # Convertir SVG en PNG
    png_output = io.BytesIO()
    cairosvg.svg2png(bytestring=svg_data.encode(), write_to=png_output, scale=2)  # Scale pour haute qualité
    png_output.seek(0)

    # Améliorer avec Pillow (optionnel : ajouter effets)
    img = Image.open(png_output)
    # Exemple : ajouter un filtre (mais garder simple)
    img = img.convert("RGBA")

    file_output = io.BytesIO()
    img.save(file_output, format='PNG')
    file_output.seek(0)

    file = discord.File(file_output, filename="board.png")
    await ctx.send(file=file)

bot.run(TOKEN)
