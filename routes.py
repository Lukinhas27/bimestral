from flask import Blueprint, request, redirect, url_for, render_template
from db import get_db_connection

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    conn = get_db_connection()
    teams = conn.execute('''
        SELECT teams.id, teams.name, GROUP_CONCAT(players.name, ', ') as player_names
        FROM teams
        LEFT JOIN player_team ON teams.id = player_team.team_id
        LEFT JOIN players ON player_team.player_id = players.id
        GROUP BY teams.id
    ''').fetchall()
    conn.close()
    return render_template('home.html', teams=teams)

@bp.route('/players')
def players():
    conn = get_db_connection()
    players = conn.execute('''
        SELECT players.id, players.name, COALESCE(GROUP_CONCAT(teams.name, ', '), '') AS team_names
        FROM players
        LEFT JOIN player_team ON players.id = player_team.player_id
        LEFT JOIN teams ON player_team.team_id = teams.id
        GROUP BY players.id;
    ''').fetchall()
    conn.close()
    return render_template('players.html', players=players)

@bp.route('/new_player', methods=('GET', 'POST'))
def new_player():
    conn = get_db_connection()
    error = None
    teams = conn.execute('SELECT * FROM teams').fetchall()

    if request.method == 'POST':
        name = request.form['name']
        selected_teams = request.form.getlist('teams')

        if not name:
            error = "O nome do jogador é obrigatório."
        elif not selected_teams:
            error = "Selecione pelo menos um time."

        if error is None:
            conn.execute('INSERT INTO players (name) VALUES (?)', (name,))
            player_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

            for team_id in selected_teams:
                conn.execute('INSERT INTO player_team (player_id, team_id) VALUES (?, ?)', (player_id, team_id))

            conn.commit()
            conn.close()
            return redirect(url_for('main.home'))

    conn.close()
    return render_template('new_player.html', teams=teams, error=error)

@bp.route('/edit_player/<int:id>', methods=('GET', 'POST'))
def edit_player(id):
    conn = get_db_connection()
    player = conn.execute('SELECT * FROM players WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        team_ids = request.form.getlist('teams')

        conn.execute('UPDATE players SET name = ? WHERE id = ?', 
                     (name, id))
        
        conn.execute('DELETE FROM player_team WHERE player_id = ?', 
                     (id,))
        
        # Adiciona novas associações
        for team_id in team_ids:
            conn.execute('INSERT INTO player_team (player_id, team_id) VALUES (?, ?)', 
                         (id, team_id))

        conn.commit()
        conn.close()
        return redirect(url_for('main.players'))

    teams = conn.execute('SELECT id, name FROM teams').fetchall()
    selected_teams = conn.execute('SELECT team_id FROM player_team WHERE player_id = ?', (id,)).fetchall()
    selected_teams = [team['team_id'] for team in selected_teams]
    conn.close()

    return render_template('edit_player.html', player=player, teams=teams, selected_teams=selected_teams)


@bp.route('/delete_player/<int:id>', methods=('POST',))
def delete_player(id):
    conn = get_db_connection()
    
    # Verificar se o jogador existe
    player = conn.execute('SELECT * FROM players WHERE id = ?', (id,)).fetchone()
    if player is None:
        conn.close()
        return redirect(url_for('main.players'))
    
    # Deletar associações e o jogador
    conn.execute('DELETE FROM player_team WHERE player_id = ?', (id,))
    conn.execute('DELETE FROM players WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('main.players'))

@bp.route('/teams')
def teams():
    conn = get_db_connection()
    teams = conn.execute('SELECT * FROM teams').fetchall()
    conn.close()
    return render_template('teams.html', teams=teams)

@bp.route('/new_team', methods=('GET', 'POST'))
def new_team():
    conn = get_db_connection()

    if request.method == 'POST':
        name = request.form['name']
        selected_player_ids = request.form.getlist('players')

        # Insere o novo time
        conn.execute('INSERT INTO teams (name) VALUES (?)', (name,))
        team_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Associa jogadores ao novo time
        for player_id in selected_player_ids:
            conn.execute('INSERT INTO player_team (player_id, team_id) VALUES (?, ?)', (player_id, team_id))

        conn.commit()
        conn.close()
        return redirect(url_for('main.home'))

    players = conn.execute('SELECT id, name FROM players').fetchall()
    conn.close()

    return render_template('new_team.html', players=players)


@bp.route('/edit_team/<int:id>', methods=('GET', 'POST'))
def edit_team(id):
    conn = get_db_connection()
    team = conn.execute('SELECT * FROM teams WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        selected_player_ids = request.form.getlist('players')

        # Atualiza o nome do time
        conn.execute('UPDATE teams SET name = ? WHERE id = ?', (name, id))
        
        # Remove todas as associações existentes
        conn.execute('DELETE FROM player_team WHERE team_id = ?', (id,))
        
        # Adiciona novas associações
        for player_id in selected_player_ids:
            conn.execute('INSERT INTO player_team (player_id, team_id) VALUES (?, ?)', (player_id, id))

        conn.commit()
        conn.close()
        return redirect(url_for('main.home'))

    players = conn.execute('SELECT id, name FROM players').fetchall()
    selected_players = conn.execute('SELECT player_id FROM player_team WHERE team_id = ?', (id,)).fetchall()
    selected_players = [player['player_id'] for player in selected_players]
    conn.close()

    return render_template('edit_team.html', team=team, players=players, selected_players=selected_players)

@bp.route('/delete_team/<int:id>', methods=('POST',))
def delete_team(id):
    conn = get_db_connection()
    
    # Verificar se o time existe
    team = conn.execute('SELECT * FROM teams WHERE id = ?', (id,)).fetchone()
    if team is None:
        conn.close()
        return redirect(url_for('main.teams'))
    
    # Deletar associações e o time
    conn.execute('DELETE FROM player_team WHERE team_id = ?', (id,))
    conn.execute('DELETE FROM teams WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('main.teams'))
