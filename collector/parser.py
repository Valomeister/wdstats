import hashlib
from datetime import datetime

from core.logging_config import setup_logging


logger = setup_logging('collector')

RESULT_CODES = {'defeat': -1, 'draw': 0, 'victory': 1}


def parse_showdown_match(item, request_tag):
    game_time = item['battleTime']
    battle = item['battle']

    if item['event']['mode'] == 'soloShowdown':
        teams = [[p] for p in battle['players']]
    else:
        teams = battle['teams']

    cur_game = {
        'match_time': item['battleTime'],
        'game_dt': datetime.strptime(game_time, "%Y%m%dT%H%M%S.%fZ"),
        'game_mode': item['event']['mode'],
        'game_map': item['event']['map'],
        'game_type': battle['type'],
        'star_player': None,
        'result': 0, # doesnt make sense for showdown
        'players': []
    }

    non_nullable_fields = ['match_time', 'game_dt', 'game_mode', 'game_map', 'game_type', 'result']
    missing = [
        key for key in non_nullable_fields
        if cur_game[key] is None
    ]

    if missing:
        raise ValueError(f"Missing fields: {missing}")

    for t, team in enumerate(teams):
        for player in team:
            trophy_change = battle.get('trophyChange', 0) if player['tag'] == request_tag else None
            cur_game['players'].append(
                {
                    'team': t + 1,
                    'player_tag': player['tag'],
                    'player_nickname': player['name'],
                    'brawler': player['brawler']['name'],
                    'trophies': player['brawler']['trophies'],
                    'trophy_change': trophy_change
                }
            )

    cur_game['unique_hash'] = generate_match_hash(
        cur_game['game_dt'],
        [p['player_tag'] for p in cur_game['players']]
    )

    return cur_game


def parse_trio_match(item, request_tag):
    game_time = item['battleTime']
    battle = item['battle']
    teams = battle['teams']
    teams_tags = [[player['tag'] for player in team] for t, team in enumerate(teams)]
    current_team_idx = 0 if request_tag in teams_tags[0] else 1
    star_player_obj = battle.get('starPlayer', None)
    if star_player_obj is None:
        star_player = None
    else:
        star_player = star_player_obj.get('tag')

    cur_game = {
        'match_time': item['battleTime'],
        'game_dt': datetime.strptime(game_time, "%Y%m%dT%H%M%S.%fZ"),
        'game_mode': item['event']['mode'],
        'game_map': item['event']['map'],
        'game_type': battle['type'],
        'star_player': star_player,
        'result': RESULT_CODES[battle['result']],
        'players': []
    }

    non_nullable_fields = ['match_time', 'game_dt', 'game_mode', 'game_map', 'game_type', 'result']
    missing = [
        key for key in non_nullable_fields
        if cur_game[key] is None
    ]

    if missing:
        raise ValueError(f"Missing fields: {missing}")

    for t, team in enumerate(teams):
        for player in team:
            trophy_change = battle.get('trophyChange', 0) if player['tag'] == request_tag else None
            cur_game['players'].append(
                {
                    'team': 1 if t == current_team_idx else -1,
                    'player_tag': player['tag'],
                    'player_nickname': player['name'],
                    'brawler': player['brawler']['name'],
                    'trophies': player['brawler']['trophies'],
                    'trophy_change': trophy_change
                }
            )

    cur_game['unique_hash'] = generate_match_hash(
        cur_game['game_dt'],
        [p['player_tag'] for p in cur_game['players']]
    )

    return cur_game


def parse_battlelog(raw_json, request_tag):
    parsed = []
    unparsable = []
    friendly_counter = 0
    for item in raw_json['items']:
        try:
            if item['battle']['type'] == 'friendly':
                friendly_counter += 1
                continue

            if item['event']['mode'] in ['soloShowdown', 'duoShowdown', 'trioShowdown']:
                parsed_match = parse_showdown_match(item, request_tag)
            else:
                parsed_match = parse_trio_match(item, request_tag)

            parsed.append(parsed_match)
        except Exception as e:
            logger.exception(
                f"Could not parse match {item.get('battleTime')}: {e}"
            )
            unparsable.append(item)

    if unparsable:
        logger.warning(f'Could not parse {len(unparsable)} matches for player {request_tag}')
    if friendly_counter:
        logger.info(f'skipped {friendly_counter} friendly matches for player {request_tag}')

    return parsed

async def get_raw_from_api(api_client, request_tag):
    return await api_client.get_matches(request_tag)

def generate_match_hash(match_time, player_tags):
    data = (
        f"{match_time.isoformat()}:"
        f"{','.join(sorted(player_tags))}"
    )

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()
