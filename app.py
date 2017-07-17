# -*- coding: utf-8 -*-
"""
Authored by: Fang Jiaan (fduodev@gmail.com)
"""
import re

from flask import Flask, jsonify, request
import codecs
from mcrcon import MCRcon
from flask_cors import CORS, cross_origin

help_map = {}
with codecs.open('./help.tsv', encoding='utf-8') as f:
    for line in f.readlines():
        c, v = line.split('\t')
        help_map[c.strip()] = v.strip()

app = Flask(__name__)
server = MCRcon()
cors = CORS(app, resources={r'/*': {'origins': '*'}})
cache = {}


@app.route('/commands')
def commands():
    if 'cmds' in cache:
        cmds = cache['cmds']
    else:
        cmds = []
        first_line = server.command('?').splitlines()[0]
        pages = int(re.findall(r'\(\d*/(\d*)\)', first_line)[0])
        for i in range(pages):
            page_commands = []
            tmp = server.command('? %s' % (i + 1)).splitlines()[1:]
            for line in tmp:
                if not line.startswith('/'):
                    continue
                command, desc = line.split(': ')
                page_commands.append(
                    {'command': command.strip(),
                     'description': help_map.get(command.strip().replace('minecraft:', ''), desc.strip())}
                )

            cmds.extend(page_commands)
            cache['cmds'] = cmds
    total = len(cmds)
    count = int(request.args.get('count', 20))
    if count >= 50:
        return jsonify({'message': u'每页条目数不得超过50'}), 400
    start = int(request.args.get('start', 0))
    page = start * count / total

    data = {
        'results': cmds[start:start + count],
        'total': total,
        'page': page,
        'start': start,
        'count': count
    }
    return jsonify(data)


@app.route('/users')
def users():
    users = [x.split(': ') for x in server.command('list').splitlines()[1:]]
    return jsonify(
        {
            'results': [{'world': world, 'name': name} for world, name in users],
            'total': len(users)
        }
    )


@app.route('/users/<string:username>', methods=['GET', 'PATCH'])
def user(username):
    if request.method.lower() == 'patch':
        if not request.json:
            return {'message': u'数据无效'}, 400

        if 'exp' in request.json:
            print(server.command('exp set %s %s' % (username, request.json['exp'])))

        if 'op' in request.json:
            if not isinstance(request.json['op'], bool):
                return jsonify({'message': '值非法: op'})
            server.command('op %s' % username) if request.json['op'] else server.command('deop %s' % username)

        if 'gamemode' in request.json:
            gamemode = request.json['gamemode']
            modes = ['survival', 'creative', 'adventure', 'spectator']
            if gamemode not in modes:
                return jsonify({'message': '无效的游戏模式, 可用的值: %s' % ', '.join(modes)})
            server.command('gamemode %s %s' % (gamemode, username))

    info = server.command('whois ' + username).splitlines()[1:]
    info = [line.split(': ') for line in info]
    data = dict((k.lower().replace(' - ', '').replace(' ', '_'), v) for k, v in info)

    to_clear_fields = ['fly_mode', 'god_mode', 'op', 'afk', 'jail', 'muted']
    for field in to_clear_fields:
        data[field] = True if 'true' in data[field] else False

    exp, level = data['exp'].split(' (')
    data['exp'] = int(exp.replace(',', ''))
    data['level'] = int(level.replace('Level ', '').replace(')', ''))
    data['health_current'] = int(data['health'].split('/')[0])
    data['health_full'] = int(data['health'].split('/')[0])
    del data['health']
    hunger = data['hunger'].split(' (')[0]
    data['hunger_current'] = int(hunger.split('/')[0])
    data['hunger_full'] = int(hunger.split('/')[0])
    del data['hunger']

    return jsonify(data)


@app.route('/users/<string:username>/do/burn', methods=['PATCH'])
def burn(username):
    secs = request.json.get('seconds') if request.json else None
    if not secs:
        return jsonify({'message': u'参数`seconds`是必填项'})
    ret = server.command('burn %s %s' % (username, secs))
    return jsonify({'message': ret})


@app.route('/users/<string:username>/do/feed', methods=['PATCH'])
def feed(username):
    ret = server.command('feed %s' % (username))
    return jsonify({'message': ret.strip()})


@app.route('/users/<string:username>/do/heal', methods=['PATCH'])
def heal(username):
    ret = server.command('heal %s' % (username))
    return jsonify({'message': ret.strip()})


@app.route('/users/<string:username>/toggle_fly', methods=['POST'])
def fly(username):
    ret = server.command('fly %s' % (username))
    return jsonify({'fly_mode': False if 'disabled' in ret.strip() else True})


@app.route('/users/<string:username>/toggle_god', methods=['POST'])
def god(username):
    ret = server.command('god %s' % (username))
    return jsonify({'god_mode': False if 'disabled' in ret.strip() else True})


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--bind', metavar='N', type=str,
                        help='bind')

    parser.add_argument('--rcon-host', metavar='N', type=str,
                        help='bind', required=True)

    parser.add_argument('--rcon-port', metavar='N', type=int,
                        help='bind', required=True)

    args = parser.parse_args()
    server.connect(args.rcon_host, args.rcon_port)
    server.login('minecraft')
    if args.bind:
        host, port = args.bind.split(':')
    else:
        host = 'localhost'
        port = 25585

    app.run(host=host, port=int(port), debug=True)
