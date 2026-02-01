import sys
import runpy
import os
import argparse
from typing import Tuple, List
import retracesoftware.utils as utils
import retracesoftware.functional as functional
from retracesoftware.stackdifference import on_stack_difference
from pathlib import Path
from retracesoftware.proxy.record import RecordProxySystem
from retracesoftware.proxy.replay import ReplayProxySystem
import retracesoftware.stream as stream
from retracesoftware.proxy.startthread import thread_id
import datetime
import json
from shutil import copy2
import threading
import time
import gc
import hashlib

from retracesoftware.run import install, run_with_retrace, ImmutableTypes, thread_states
from retracesoftware.exceptions import RecordingNotFoundError, VersionMismatchError, ConfigurationError

def expand_recording_path(path):
    return datetime.datetime.now().strftime(path.format(pid = os.getpid()))

def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def dump_as_json(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

vscode_workspace = {
    "folders": [{ 'path': '.' }],
    "settings": {
        "python.defaultInterpreterPath": sys.executable,
    },
    "launch": {
        "version": "0.2.0",
        "configurations": [{
            "name": "replay",
            "type": "debugpy",
            "request": "launch",
            
            "python": sys.executable,
            "module": "retracesoftware",
            "args": [
                "--recording", "..",
                "--skip_weakref_callbacks",
                "--read_timeout", "1000"
            ],
            
            "cwd": "${workspaceFolder}/run",
            "console": "integratedTerminal",
            "justMyCode": False
        }]
    },
}

def scriptname(argv):
    return argv[1] if argv[0] == "-m" else argv[0]

def collector(multiplier):
    collect_gen = utils.CollectPred(multiplier = multiplier)

    return functional.lazy(functional.sequence(collect_gen, functional.when_not_none(gc.collect)))

def file_md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()

def checksum(path):
    return file_md5(path) if path.is_file() else {entry.name: checksum(entry) for entry in path.iterdir() if entry.name != '__pycache__'}

def retrace_extension_paths():
    names = ['retracesoftware_utils', '_retracesoftware_functional', 'retracesoftware_stream']
    return {name: Path(sys.modules[name].__file__) for name in names}

def retrace_module_paths():
    paths = retrace_extension_paths()
    paths['retracesoftware'] = Path(sys.modules['retracesoftware'].__file__).parent
    return paths

def checksums():
    return {name: checksum(path) for name, path in retrace_module_paths().items()}

def record(options, args):
    
    path = Path(expand_recording_path(options.recording))
    # ensure the path exists
    path.mkdir(parents=True, exist_ok=True) 

    from retracesoftware.install import edgecases
    edgecases.recording_path = path

    # write various recording files to directory
    dump_as_json(path / 'settings.json', {
        'argv': args,
        'executable': sys.executable,
        'magic_markers': options.magic_markers,
        'trace_inputs': options.trace_inputs,
        'trace_shutdown': options.trace_shutdown,
        'env': dict(os.environ),
        'python_version': sys.version,
        'md5_checksums': checksums(),
    })

    rundir = path / 'run'
    rundir.mkdir(exist_ok=True)

    script = Path(scriptname(args))
    if script.exists():
        copy2(script, rundir)

    # create a .venv directory in the recording path
    # venv_path = path / '.venv'
    # venv_path.mkdir(exist_ok=True)

    # create a pyvenv.cfg file in the .venv directory
    # with open(venv_path / 'pyvenv.cfg', 'w') as f:
    #     f.write(f'home = {sys.executable}\n')
    #     f.write('include-system-site-packages = false\n')
    #     f.write(f'version = {sys.version}\n')

    # bindir = venv_path / 'bin'
    # bindir.mkdir(exist_ok=True)

    # create a symlink to the python executable in the .venv directory
    # python_link = bindir / 'python'
    # if python_link.exists() or python_link.is_symlink():
    #     python_link.unlink()
    # python_link.symlink_to(sys.executable)

    dump_as_json(path / 'replay.code-workspace', vscode_workspace)

    with stream.writer(path = path / 'trace.bin',
                       thread = thread_id, 
                       verbose = options.verbose, 
                       stacktraces = options.stacktraces, 
                       magic_markers = options.magic_markers) as writer:

        # flusher = threading.Timer(5.0, periodic_task)
        # flusher.start()

        writer.exclude_from_stacktrace(record)
        writer.exclude_from_stacktrace(main)

        thread_state = utils.ThreadState(*thread_states)

        tracing_config = {}

        multiplier = 2
        gc.set_threshold(*map(lambda x: x * multiplier, gc.get_threshold()))

        system = RecordProxySystem(
            writer = writer,
            thread_state = thread_state,
            immutable_types = ImmutableTypes(), 
            tracing_config = tracing_config,
            maybe_collect = collector(multiplier = multiplier),
            traceargs = options.trace_inputs)

        # force a full collection
        install(system)

        gc.collect()
        gc.callbacks.append(system.on_gc_event)
    
        run_with_retrace(system, args, options.trace_shutdown)

        gc.callbacks.remove(system.on_gc_event)

def replay(args):
    path = Path(args.recording)

    if not path.exists():
        raise RecordingNotFoundError(f"Recording path: {path} does not exist")

    settings = load_json(path / "settings.json")

    if settings['md5_checksums'] != checksums():
        raise VersionMismatchError("Checksums for Retrace do not match, cannot run replay with different version of retrace to record")

    if settings['python_version'] != sys.version:
        raise VersionMismatchError("Python version does not match, cannot run replay with different version of Python to record")

    os.environ.update(settings['env'])

    if sys.executable != settings['executable']:
        raise ConfigurationError(f"Stopping replay as current python executable: {sys.executable} is not what was used for record: {settings['executable']}")

    thread_state = utils.ThreadState(*thread_states)

    # with stream.reader(path = path / 'trace.bin',
    #                    thread = thread_id, 
    #                    timeout_seconds = args.timeout,
    #                    verbose = args.verbose,
    #                    on_stack_difference = thread_state.wrap('disabled', on_stack_difference),
    #                    magic_markers = settings['magic_markers']) as reader:

    with stream.reader1(path = path / 'trace.bin',
                        read_timeout = args.read_timeout,
                        verbose = args.verbose,
                        magic_markers = settings['magic_markers']) as reader:

        tracing_config = {}

        system = ReplayProxySystem(
            reader = reader,
            thread_state = thread_state,
            immutable_types = ImmutableTypes(), 
            tracing_config = tracing_config,
            traceargs = settings['trace_inputs'],
            verbose = args.verbose,
            skip_weakref_callbacks = args.skip_weakref_callbacks)

        install(system)

        gc.collect()
        gc.disable()

        run_with_retrace(system, settings['argv'], settings['trace_shutdown'])

def main():
    parser = argparse.ArgumentParser(
        prog="python -m retracesoftware",
        description="Run a Python module with debugging, logging, etc."
    )

    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose output'
    )

    parser.add_argument(
        '--recording',   # or '-r'
        type = str,      # ensures it's a string (optional, but safe)
        default = '.',    # default value if not provided
        help = 'the directory to place the recording files'
    )

    if '--' in sys.argv:
        parser.add_argument(
            '--stacktraces', 
            action='store_true', 
            help='Capture stacktrace for every event'
        )

        parser.add_argument(
            '--magic_markers', 
            action='store_true', 
            help='Write magic markers to tracefile, used for debugging'
        )

        parser.add_argument(
            '--trace_shutdown',
            action='store_true', 
            help='Whether to trace system shutdown and cleanup hooks'
        )

        parser.add_argument(
            '--trace_inputs', 
            action='store_true', 
            help='Whether to write call parameters, used for debugging'
        )

        parser.add_argument('rest', nargs = argparse.REMAINDER, help='target application and arguments')

        args = parser.parse_args()

        record(args, args.rest[1:])
    else:

        parser.add_argument(
            '--skip_weakref_callbacks',
            action='store_true',
            help = 'whether to disable retrace in weakref callbacks on replay'
        )

        parser.add_argument(
            '--read_timeout',   # or '-r'
            type = int,      # ensures it's a string (optional, but safe)
            default = 1000,    # default value if not provided
            help = 'timeout in millseconds for incomplete read of element to timeout'
        )

        replay(parser.parse_args())

if __name__ == "__main__":
    main()