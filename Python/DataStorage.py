import json
import datetime
import time
import sqlite3
import logging
import prettytable

logger = logging.Logger('catch_all')


def get_wins(ctx, member, arg):
    try:
        conn = sqlite3.connect('boardgamebot.db')
        c = conn.cursor()
        response = None
        if member and arg:
            c.execute('SELECT g.name, discord_id, number_of_wins ' +
                      'FROM wins ' +
                      'INNER JOIN games g on wins.game_id = g.id ' +
                      'WHERE discord_id = ' + str(member.id) + ' AND g.name = ' + '\'' + arg + '\'' +
                      ' GROUP BY g.name, discord_id')
            response = prettify_data(ctx, c)
        elif member:
            c.execute('SELECT g.name, discord_id, number_of_wins ' +
                      'FROM wins ' +
                      'INNER JOIN games g on wins.game_id = g.id ' +
                      'WHERE discord_id = ' + str(member.id) +
                      ' GROUP BY g.name, discord_id')
            response = prettify_data(ctx, c)
        elif arg:
            c.execute('SELECT g.name, discord_id, number_of_wins ' +
                      'FROM wins ' +
                      'INNER JOIN games g on wins.game_id = g.id ' +
                      'WHERE g.name = ' + '\'' + arg + '\''
                      'GROUP BY g.name, discord_id')
            response = prettify_data(ctx, c)
        else:
            c.execute('SELECT g.name, discord_id, number_of_wins ' +
                     'FROM wins ' +
                     'INNER JOIN games g on wins.game_id = g.id ' +
                     'GROUP BY g.name, discord_id')
            response = prettify_data(ctx, c)

    except BaseException as e:
            logger.error(e, exc_info=True)
            response = 'Failed to retrieve wins'
    finally:
        conn.close()
        return response


def add_win_db(ctx, member, arg):
    try:
        member_id = str(member.id)
        conn = sqlite3.connect('boardgamebot.db')
        c = conn.cursor()
        c.execute('SELECT id FROM games WHERE name = \'' + arg + '\'')
        game_id = c.fetchone()
        if game_id:
                game_id = game_id[0]
                c.execute('SELECT id ' +
                          'FROM wins WHERE game_id = ' + str(game_id) +
                          ' AND discord_id = ' + member_id)
                wins_id = c.fetchone()
                if wins_id:
                    wins_id = wins_id[0]
                    c.execute('SELECT number_of_wins FROM wins ' +
                              'WHERE id = ' + str(wins_id))
                    old_number_of_wins = c.fetchone()[0]
                    c.execute('UPDATE wins SET number_of_wins = ? ' +
                              'WHERE id = ?',
                              (old_number_of_wins + 1, wins_id,))
                    conn.commit()
                    return 'Added a win to ' + member.name + ' for ' + arg
                else:
                    c.execute("""INSERT INTO wins
                              (discord_id, game_id, number_of_wins)
                              VALUES (?,?,?)""", (member_id, game_id, 1,))
                    conn.commit()
                return 'Added a win to ' + member.name + ' for ' + arg
        else:
            return 'No game with the name ' + arg + ' could be found. Please add it first using the !ag command.'
    except BaseException as e:
        logger.error(e, exc_info=True)
        return 'Failed to add a win to ' + member.name + ' for ' + arg
    finally:
        conn.close()


def add_game_db(ctx, name):
    try:
        conn = sqlite3.connect('boardgamebot.db')
        c = conn.cursor()
        c.execute('INSERT INTO games (name) VALUES (?)', (name,))
        conn.commit()
        return 'Added the game ' + name
    except sqlite3.IntegrityError as e:
        logger.error(e, exc_info=True)
        return name + ' has already been added.'
    except BaseException as e:
        logger.error(e, exc_info=True)
        return 'Failed to add game ' + name
    finally:
        conn.close()


def getStartTime():
    jsonFile = open("data\\playtime.json", "r+")
    data = json.load(jsonFile)
    return data["start time"]


def setStartTime():
    start_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    with open("data\\playtime.json", "r+") as json_file:
        json_decoded = json.load(json_file)
    json_decoded["start time"] = start_time
    with open("data\\playtime.json", "r+") as json_file:
        json.dump(json_decoded, json_file)


def getEndTime():
    jsonFile = open("data\\playtime.json", "r+")
    data = json.load(jsonFile)
    string_date = data["start time"]
    formatted_datetime_object = datetime.datetime.strptime(
        string_date, '%Y-%m-%dT%H:%M:%S.%f')
    elapsed_time = datetime.datetime.now() - formatted_datetime_object
    return str(elapsed_time)


def prettify_data(ctx, cursor):
    rows = cursor
    if rows is None:
        return 'No wins found'
    else:
        pretty_table = prettytable.PrettyTable()
        pretty_table.field_names = ['Game', 'Player', 'Wins']

        for row in rows:
            pretty_table.add_row([row[0], ctx.guild.get_member(int(row[1])).display_name, row[2]])

        return pretty_table.get_string()

