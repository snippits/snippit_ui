#!/usr/bin/env python3
# Copyright (c) 2017, Medicine Yeh

import os
import sys
import getopt
import glob
import json
import time
import textwrap
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from flask import Flask, request, send_from_directory, send_file
import flask_profiler

import myutils.processParser as processParser
import myutils.createMappingTable as createMappingTable
import myutils.createTreeMap as createTreeMap
import myutils.terminalColors as bcolors

from myutils.phaseProcessor import *

PHASE_CONTEXT_SWITCH = 1


BASE_PATH = os.path.dirname(os.path.realpath(__file__))
PARENTDIR = os.path.dirname(BASE_PATH)

STATIC_DIR = os.path.join(BASE_PATH, '..', 'public')
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5000
DEFAULT_INPUT_PATH = '/tmp/snippit'

# Set the project root directory as the static folder
app = Flask(__name__)

# Load settings
app.config.from_object('flask_config.DefaultConfig')
if (os.environ.get('SNIPPIT_UI_CONFIG')):
    app.config.from_envvar('SNIPPIT_UI_CONFIG')

# Necessary configuration to initialize flask-profiler:
app.config['flask_profiler'] = {
    'enabled': app.config['DEBUG'],
    'storage': {
        'engine': 'sqlite'
    },
    'basicAuth':{
        'enabled': True,
        'username': 'admin',
        'password': 'admin'
    },
    'ignore': [
    ]
}

def getSimilarityParams(request):
    requestValues = request.get_json(silent=True)
    simMat = processes['default_']['similarityMatrix']
    if requestValues['similarityThreshold']:
        simTh = float(requestValues['similarityThreshold']) / 100.0
    else:
        simTh = None

    return (simMat, simTh)

@app.route('/')
def root():
    path = os.path.join(STATIC_DIR, 'index.html')
    return send_file(path, cache_timeout=0)

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory(STATIC_DIR, path, cache_timeout=0)

@app.route('/phase/timeline', methods=['POST'])
def get_phase_timeline():
    info = processes['default_']['info']
    (simMat, simTh) = getSimilarityParams(request)

    # Get mapping table and remap the timeline to its new phase ID
    mappingTable = getPhaseMappingTable(simMat, simTh)
    timeline = [ [kv[0], mappingTable[kv[1]]] for kv in info['timeline'] ]
    # Get the context switch points
    breakPoints = [ [kv[0], None] for kv in info['events'] if kv[1] == PHASE_CONTEXT_SWITCH ]
    # Merge two timeline in sorted order
    timeline = sorted(timeline + breakPoints)
    response = app.response_class(
        response=json.dumps(timeline),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/phase/<int:phase_id>/treemap', methods=['POST'])
def get_phase_treemap(phase_id):
    info = processes['default_']['info']
    (simMat, simTh) = getSimilarityParams(request)

    merged_phases = getMergedPhases(info['phase'], simMat, simTh)
    codes = merged_phases[phase_id]['codes']
    treemap = createTreeMap.parse(codes)
    response = app.response_class(
        response=json.dumps(treemap),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/phase/<int:phase_id>/prof', methods=['POST'])
def get_phase_prof(phase_id):
    info = processes['default_']['info']
    (simMat, simTh) = getSimilarityParams(request)

    merged_phases = getMergedPhases(info['phase'], simMat, simTh)
    response = app.response_class(
        response=json.dumps(merged_phases[phase_id]['counters']),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/phase/<int:phase_id>/codes', methods=['POST'])
def get_phase_code(phase_id):
    info = processes['default_']['info']
    (simMat, simTh) = getSimilarityParams(request)

    merged_phases = getMergedPhases(info['phase'], simMat, simTh)
    response = app.response_class(
        response=json.dumps(merged_phases[phase_id]['codes']),
        status=200,
        mimetype='application/json'
    )
    return response

# In order to active flask-profiler, you have to pass flask
# app as an argument to flask-profiler.
# All the endpoints declared so far will be tracked by flask-profiler.
flask_profiler.init_app(app)

def get_descriptions():
    return textwrap.dedent('''\
    A webserver for snippits UI web interface.
    ''')

def get_sample_usage():
    return textwrap.dedent('''\
    Sample Usage:
            Ex: server.py /tmp/snippit
    ''')

def main(argv):
    ap = ArgumentParser('server.py',
            formatter_class=RawDescriptionHelpFormatter,
            description=get_descriptions(),
            epilog=get_sample_usage())
    ap.add_argument('input_path', metavar='PATH', type=str, nargs='?', default=DEFAULT_INPUT_PATH,
            help='The path to Snippits output. Defaults to {}'.format(DEFAULT_INPUT_PATH))
    ap.add_argument('--host', type=str, default=DEFAULT_HOST,
            help='The host ip address on which Snippit webserver serve. Defaults to {}'.format(DEFAULT_HOST))
    ap.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
            help='The port on which Snippit webserver will be hosted. Defaults to {}'.format(DEFAULT_PORT))
    args = ap.parse_args()

    input_path = os.path.abspath(args.input_path)
    proc_path = os.path.join(input_path, 'proc')
    if (os.path.exists(proc_path) == False):
        print('{} path \'{}\' not found!'.format(bcolors.WARNING_STR, proc_path))

    global processes
    processes = processParser.parseAllProcesses(proc_path)
    if (len(processes) == 0):
        print('{} no processes found under \'{}\'!'.format(bcolors.WARNING_STR, proc_path))

    print(' * Server running on: {}http://{}:{}/{}'.format(
            bcolors.OKBLUE, args.host, args.port, bcolors.ENDC
        ))
    if (app.config['DEBUG']):
        print(' * Profiling results on: {}http://{}:{}/flask-profiler/{}'.format(
            bcolors.OKBLUE, args.host, args.port, bcolors.ENDC
            ))
        auth = app.config['flask_profiler']['basicAuth']
        print('       username: {}    password: {}'.format(auth['username'], auth['password']))
        app.run(host=args.host, port=args.port, use_debugger=True, use_reloader=True)
    else:
        app.run(host=args.host, port=args.port)

if __name__ == '__main__':
    main(sys.argv[1:])
