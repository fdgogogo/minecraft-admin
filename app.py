# -*- coding: utf-8 -*-
"""
Authored by: Fang Jiaan (fduodev@gmail.com)
"""
import re

from flask import Flask, jsonify
import codecs
from mcrcon import MCRcon

help_map = {}
with codecs.open('./help.tsv', encoding='utf-8') as f:
    for line in f.readlines():
        c, v = line.split('\t')
        help_map[c.strip()] = v.strip()

app = Flask(__name__)
server = MCRcon()


@app.route('/')
def commands():
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

    data = {
        'results': cmds
    }
    return jsonify(data)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--bind', metavar='N', type=str, nargs='+',
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
