from __future__ import print_function
from fnmatch import fnmatch
from random import shuffle
import inspect
import traceback
import argparse
import glob2
import os
import sys
import datetime
import platform
import imp
import colorama


class _g(object):
    '''
    Stores globals, e.g. _g.clargs
    '''
    script_run = None # The currently running script
    overall_run = None # The OverallRun object
    clargs = None # Command-line args
    verbosity = 2 # 2: normal, 1: minimal, 0: quiet
    multi = False # This gets set to True in go() if we're running more than 1 script.


class _Run(object):
    '''
    Describes each script run as well as the overall run which is a subclass of this.
    Holds the functions for logging successes, failures & errors.
    '''
    def __init__(self, script, plan):
        self.name = script['module']
        self.path = '{}/{}.py'.format(os.path.abspath(script['path']), script['module'])
        self.ran = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.underrun = False
        self.overrun = False
        self.failures = []
        self.stack_traces = []
        self.start_time = datetime.datetime.utcnow()
        self.end_time = None
        self.time_elapsed = None
        self.plan = plan
        if self.plan:
            self.plan_specified = True
        else:
            self.plan_specified = False

    def log_success(self, message=''):
        self.ran += 1
        self.passed += 1
        if not self.plan_specified:
            self.plan += 1

        if _g.verbosity == 0:
            return
        elif _g.verbosity == 1:
            sys.stdout.write('.')
            sys.stdout.flush()
        else:
            output = 'ok ' + str(self.ran)
            if message:
                output += ' - ' + str(message)
            print(colorama.Fore.RESET + output)
        _Newline.set(True)

    def log_failure(self, stack_frame, got=None, expected=None, message=''):
        self.ran += 1
        self.failed += 1
        if not self.plan_specified:
            self.plan += 1

        script_name = stack_frame[1]
        line_no = stack_frame[2]

        if _g.verbosity == 0:
            pass
        elif _g.verbosity == 1:
            sys.stdout.write('F')
            sys.stdout.flush()
        else:
            output = 'not ok ' + str(self.ran)
            if message:
                output += ' - ' + str(message)
            print(colorama.Fore.YELLOW + output)
            print(colorama.Fore.YELLOW + '#   Failure at line %s in %s.' % (line_no, script_name))

        if got and expected:
            self.failures.append({'script': script_name, 'line': int(line_no), 'got': got, 'expected': expected})
            if _g.verbosity == 2:
                print(colorama.Fore.YELLOW + '#        got:', got)
                print(colorama.Fore.YELLOW + '#   expected:', expected)
        elif got and not expected:
            self.failures.append({'script': script_name, 'line': int(line_no), 'got': got})
            if _g.verbosity == 2:
                print(colorama.Fore.YELLOW + '#   got:', got)
        else:
            self.failures.append({'script': script_name, 'line': int(line_no)})
        
        if _g.verbosity == 2:
            print()
            _Newline.set(False)

    def log_error(self):
        self.stack_traces.append(traceback.format_exc())
        self.errors += 1
        if _g.verbosity == 1:
            sys.stdout.write('E')
            sys.stdout.flush()
        if _g.verbosity == 2:
            print(colorama.Fore.MAGENTA + traceback.format_exc())
            _Newline.set(False)

    def collect(self):
        '''
        Fills in final details of a script run.
        '''
        self.end_time = datetime.datetime.utcnow()
        self.time_elapsed = self.end_time - self.start_time
        self.underrun = self.ran < self.plan
        self.overrun = self.ran > self.plan

    def summarize(self):
        '''
        Displays summary information when a script run is complete.
        '''
        if _g.verbosity < 2 and (self.failures or self.stack_traces):
            if _g.verbosity == 1: _Newline.make()
            _Newline.make()
            for failure in self.failures:
                self.print_failure(failure)
                _Newline.make()
            for stack_trace in self.stack_traces:
                print(colorama.Fore.MAGENTA + stack_trace)
            _Newline.set(False)

        if self.plan > 0: # i.e. The plan was set.
            if self.underrun or self.overrun:
                _Newline.make()
                print(colorama.Fore.MAGENTA + '# Looks like you ran {} test{}, but planned {}.'.format(self.ran, _s(self.ran), self.plan))
        if _g.verbosity > 0:
            _Newline.make()
        
        color = colorama.Fore.RESET
        if self.failed:
            color = colorama.Fore.YELLOW
        print(color + '# {} passed, {} failed.'.format(self.passed, self.failed))

        if self.errors > 0:
            print(colorama.Fore.MAGENTA + "# {} error{}".format(self.errors, _s(self.errors)))

        _Newline.set(True)
        _Newline.make()
        print(colorama.Fore.RESET + 'Time elapsed:', self.end_time - self.start_time)

        if _g.verbosity == 2 and _g.clargs.timestamp and _g.multi:
            _Newline.make()
            print(colorama.Fore.RESET + _timestamp(datetime.datetime.utcnow()))

    def print_failure(self, failure):
        print(colorama.Fore.YELLOW + 'Failure at line {} in {}.'.format(failure['line'], failure['script']))
        if 'got' in failure:
            print(colorama.Fore.YELLOW + '#      got:', failure['got'])
        if 'expected' in failure:
            print(colorama.Fore.YELLOW + '# expected:', failure['expected'])


class _OverallRun(_Run):
    '''
    Describes overall run. It's different enough from script runs to warrant its own class.
    '''

    def __init__(self):
        self.scripts = []
        self.script_runs = []
        self.complete_failures = []
        self.path = 'n/a'
        super(_OverallRun, self).__init__({'path': '', 'module': 'Overall'}, plan=0)

    def overview(self):
        '''
        Displays overview information at the start of overall run.
        '''
        print(colorama.Fore.RESET + _datetimestamp(self.start_time))
        if _g.multi or _g.clargs.parallel:
            if _g.multi:
                _Newline.make()
            if _g.clargs.parallel:
                print(colorama.Fore.RESET + 'Parallel run, {} instance{} of:'.format(_g.clargs.parallel, _s(_g.clargs.parallel)))
            for script in self.scripts:
                print(colorama.Fore.RESET + '{}/{}.py'.format(script['path'], script['module']))
            if _g.verbosity < 2:
                _Newline.make()

    def collect(self):
        '''
        Fills in final details of overall run.
        '''
        self.parallel = _g.clargs.parallel
        self.end_time = datetime.datetime.utcnow()
        self.time_elapsed = self.end_time - self.start_time

        for _g.script_run in self.script_runs:
            self.ran += _g.script_run.ran
            self.plan += _g.script_run.plan
            self.passed += _g.script_run.passed
            self.failed += _g.script_run.failed
            self.errors += _g.script_run.errors
            if _g.script_run.underrun:
                self.underrun = True
            if _g.script_run.overrun:
                self.overrun = True

            self.failures.extend(_g.script_run.failures)
            self.stack_traces.extend(_g.script_run.stack_traces)

    def summarize(self):
        '''
        Displays summary information after overall run is complete.
        '''
        if _g.verbosity == 1:
            _Newline.make()
            _Newline.make()
        if _g.verbosity < 2:
            for failure in self.failures:
                self.print_failure(failure)
                print()
            for stack_trace in self.stack_traces:
                print(colorama.Fore.MAGENTA + stack_trace)
            _Newline.set(False)
        else:
            _print_header('Overall')

        if self.failures:
            _Newline.make()
            print(colorama.Fore.RESET + 'Scripts with failures:')
            for run in self.script_runs:
                if run.failed:
                    print(colorama.Fore.YELLOW + '# {}.py'.format(run.path))

        if self.errors:
            _Newline.make()
            print(colorama.Fore.RESET + 'Scripts with errors:')
            for run in self.script_runs:
                if run.errors and (run.path not in self.complete_failures):
                    print(colorama.Fore.MAGENTA + '# {}'.format(run.path))

        if self.complete_failures:
            _Newline.make()
            print(colorama.Fore.RESET + 'Scripts that failed to run:')
            for complete_failure in self.complete_failures:
                print(colorama.Fore.MAGENTA + '# {}'.format(complete_failure))

        if self.underrun:
            _Newline.make()
            print(colorama.Fore.RESET + 'Underruns:')
            for run in self.script_runs:
                if run.underrun:
                    print(colorama.Fore.MAGENTA + '# {} ran {} test{}, but planned {}.'.format(run.path, run.ran, _s(run.ran), run.plan))

        if self.overrun:
            _Newline.make()
            print(colorama.Fore.RESET + 'Overruns:')
            for run in self.script_runs:
                if run.overrun:
                    print(colorama.Fore.MAGENTA + '# {} ran {} test{}, but planned {}.'.format(run.path, run.ran, _s(run.ran), run.plan))

        if self.plan > 0: # i.e. The plan was set.
            _Newline.make()
            if self.underrun or self.overrun:
                print(colorama.Fore.RESET + '# Looks like you ran {} test{}, but planned {}.'.format(self.ran, _s(self.ran), self.plan))
        
        color = colorama.Fore.RESET
        if self.failed:
            color = colorama.Fore.YELLOW
        print(color + '# {} passed, {} failed.'.format(self.passed, self.failed))

        if self.errors > 0:
            print(colorama.Fore.MAGENTA + "# {} error{}".format(self.errors, _s(self.errors)))

        _Newline.make()
        if _g.verbosity == 2:
            print(colorama.Fore.RESET + _datetimestamp(self.end_time))
        print(colorama.Fore.RESET + 'Time elapsed:', self.end_time - self.start_time)


'''
The test functions:

In all of them inspect.stack()[1] is the stack frame object for the test script.
inspect.stack()[0] is the current script--in this case cleartest.py.
'''

def ok(expression, message=''):
    if expression:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], message=message)
        return False


def not_ok(expression, message=''):
    if not expression:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], message=message)
        return False


def equals(got, expected, message=''):
    if got == expected:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], got, expected, message)
        return False


def not_equals(got, expected, message=''):
    if got != expected:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], got, 'Anything else', message)
        return False


def less_than(got, expected, message=''):
    if got < expected:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], got, 'less than ' + str(expected), message)
        return False


def greater_than(got, expected, message=''):
    if got > expected:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], got, 'greater than ' + str(expected), message)
        return False


def is_type(got, expected, message=''):
    if type(got) is expected:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], type(got), expected, message)
        return False


def isnt_type(got, expected, message=''):
    if type(got) is not expected:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], type(got), 'Anything else', message)
        return False


def is_in(value, sequence, message=''):
    if value in sequence:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], "{} is not in {}.".format(value, sequence), message=message)
        return False


def isnt_in(value, sequence, message=''):
    if value not in sequence:
        _g.script_run.log_success(message)
        return True
    else:
        _g.script_run.log_failure(inspect.stack()[1], "{} is in {}.".format(value, sequence), message=message)      
        return False


def succeed(message=''):
    _g.script_run.log_success(message)
    return True


def fail(message=''):
    _g.script_run.log_failure(inspect.stack()[1], message=message)
    return False


def _runtests(scripts):
    '''
    The heart. Runs all the scripts, stores results, and returns an overall run object.
    Called from go().
    '''
    for script in scripts:
        # Import each script and try to run test_main().
        try:
            if _g.verbosity == 2:
                _print_header(script['module'] + '.py')
            module = imp.load_source(script['module'], '{}/{}.py'.format(script['path'], script['module']))
            test_main_obj = getattr(module, 'test_main')
            
        except: # Failure to import or to find test_main
            _g.script_run = _Run(script, 0)
            _g.script_run.stack_traces = [traceback.format_exc()]
            _g.script_run.errors += 1
            _g.script_run.end_time = datetime.datetime.utcnow()
            _g.script_run.time_elapsed = _g.script_run.end_time - _g.script_run.start_time
            if _g.verbosity == 2:
                print(colorama.Fore.MAGENTA + traceback.format_exc())
            _Newline.set(False)
            _g.overall_run.complete_failures.append('{}/{}.py'.format(script['path'], script['module']))
        else:
            try:
                test_main_default_args = inspect.getargspec(test_main_obj).defaults
                plan = 0
                if test_main_default_args:
                    plan = test_main_default_args[0]

                _g.script_run = _Run(script, plan)
                if _g.verbosity == 2 and _g.script_run.plan:
                    print(colorama.Fore.RESET + '1..{}'.format(plan))
                module.test_main()
            except:
                _g.script_run.log_error()

            _g.script_run.collect()
            if (not _g.multi or (_g.multi and _g.verbosity == 2)) and not (_g.clargs.parallel and _g.verbosity < 2):
                _g.script_run.summarize()

        _g.overall_run.script_runs.append(_g.script_run)

    _g.overall_run.collect()
    return _g.overall_run


def _parse_cl(paths=None, suite_file=None, recursive=None, parallel=None, minimal=None, quiet=None, timestamp=None):
    '''
    Parses the command line for arguments and figures out which scripts to run.
    Called from go().
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*')
    parser.add_argument('--file', '-f', help='Run test scripts in the specified file, e.g. -f suite.txt.')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recursively search directories which may or may not be specified.')
    parser.add_argument('--parallel', '-p', nargs='?', const=1, type=int, help='Run with specified number of parallel processes per script.')
    parser.add_argument('--minimal', '-m', action='store_true', help='Minimal output, i.e. dots & letters')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output, i.e. overview & summary information only')
    parser.add_argument('--timestamp', '-t', action='store_true', help='Print time stamp between each script.')
    _g.clargs = parser.parse_args()

    if paths: _g.clargs.paths = paths
    if suite_file: _g.clargs.file = suite_file
    if recursive: _g.clargs.recursive = recursive
    if parallel: _g.clargs.parallel = parallel
    if minimal: _g.clargs.minimal = minimal
    if quiet: _g.clargs.quiet = quiet
    if timestamp: _g.clargs.timestamp = timestamp

    # May remove -q & -m in favor of -v 0 & -v 1.
    if _g.clargs.quiet: _g.verbosity = 0
    elif _g.clargs.minimal: _g.verbosity = 1

    # If this is true we've run a script from the command line, e.g. $ test_simple.py.
    if fnmatch(sys.argv[0], '*test_*.py'):
        _g.clargs.paths = [sys.argv[0]]

    # If no paths or suite file specified, run against the current directory.
    elif not _g.clargs.paths and not _g.clargs.file:
        _g.clargs.paths = '.'

    # If this is true we have a --file argument. Used 'elif' instead of 'if' in case
    # someone tries to do something like `$ test_simple.py -f suite.txt`.
    elif _g.clargs.file:
        with open(_g.clargs.file) as f:
            lines = f.readlines()
            suite_path = os.path.dirname(_g.clargs.file)
            if not suite_path:
                suite_path = '.'

            for line in lines:
                # Strip whitespace.
                line = line.strip()
                # If not a whitespace-only line or is commented out:
                if line != '' and not line.startswith('#'):
                    # If not an absolute path, add suite's path to it.
                    if not os.path.isabs(line):
                        line = suite_path + '/' + line
                        # If it can't be globbed, we have a bad path. Bail.
                        if glob2.glob(line) == []:
                            sys.exit('Bad path: ' + line)
                _g.clargs.paths.extend(glob2.glob(line))

    # Build our scripts list which will look something like this:
    # [{'path': '/path/to', 'module': 'test_go'}, {'path': '/path/to', 'module': 'test_stop'}]
    scripts = []
    for path in _g.clargs.paths:
        if not os.path.exists(path):
            sys.exit('Bad path: ' + path)
        elif os.path.isfile(path) and fnmatch(path, '*test_*.py'):
            scripts.append({'path': os.path.abspath(os.path.dirname(path)), 'module': os.path.basename(path).replace('.py', '')})
        elif os.path.isdir(path):
            if _g.clargs.recursive:
                for file_path in glob2.glob(path + '/**/test_*.py'):
                    scripts.append({'path': os.path.abspath(os.path.dirname(file_path)), 'module': os.path.basename(file_path).replace('.py', '')})
            else:
                for file_path in glob2.glob(path + '/test_*.py'):
                    scripts.append({'path': os.path.abspath(os.path.dirname(file_path)), 'module': os.path.basename(file_path).replace('.py', '')})

    if scripts == []:
        sys.exit('No scripts to run.')

    return scripts, _g.clargs


def skip(func):
    '''
    Decorate functions with this if you want them skipped by run_class.
    '''
    func.__dict__['not_a_test_function'] = True
    return func


def ctc(test_function):
    '''
    Decorate test functions with this if you think they may throw an exception.
    It will catch it and move on with the rest of the script. ctc stands for
    "cleartest catcher."
    '''
    def _run(*args, **kwargs):
        try:
            return test_function(*args,**kwargs)
        except:
            _g.script_run.log_error()
    return _run


def Ctc(cls):
    '''
    Decorate a class with this to have the @ctc decorator applied to all of its
    functions except those already decorated with @skip.
    '''
    for attr_name in dir(cls):
        attr_value = getattr(cls, attr_name)
        if (inspect.isfunction(attr_value) or inspect.ismethod(attr_value)) and ('not_a_test_function' not in attr_value.__dict__):
            setattr(cls, attr_name, ctc(attr_value))
    return cls 


def run_class(test_obj):
    '''
    Runs every function in a class in a random order.
    '''
    methods = []
    for name, method in inspect.getmembers(test_obj, inspect.ismethod):
        if not name.endswith('__') and name != 'apply_ctc' and 'not_a_test_function' not in method.__dict__:
            methods.append(method)
    shuffle(methods)
    for method in methods:
        method()


class _Newline(object):
    '''
    Intelligently figures out when to print a newline.
    '''
    _needed = True

    @staticmethod
    def set(bool):
        _Newline._needed = bool

    @staticmethod
    def make(needed=True):
        if _Newline._needed:
            print() # '----->', inspect.stack()[1][2]
        _Newline._needed = needed


def _print_header(name):
    '''
    Prints header information at the beginning of each script run.
    '''
    _Newline.make()
    print(colorama.Fore.CYAN  + '# ' + name)


def _datetimestamp(moment):
    '''
    Returns a date & time stamp.
    '''
    return moment.strftime('%a %Y %b %d %H:%M:%S UTC')


def _timestamp(moment):
    '''
    Returns a time stamp.
    '''
    return moment.strftime('%H:%M:%S UTC')


def _s(number):
    '''
    Makes a word plural if it needs it.
    '''
    if int(number) == 1:
        return ''
    else:
        return 's'


def _runtest_worker(script):
    '''
    Used for parallel runs. Called from go().
    '''
    return _runtests([script])


def go(paths=None, suite_file=None, recursive=None, parallel=None, minimal=None, quiet=None, timestamp=None):
    '''
    A wrapper for _runtests. Necessary for handling parallel runs, but serial runs are
    wrapped as well. Execution starts here.
    '''
    colorama.init()
    _g.overall_run = _OverallRun()

    _g.overall_run.scripts, _g.clargs = _parse_cl(paths, suite_file, recursive, parallel, minimal, quiet, timestamp)
    if _g.clargs.parallel and platform.system() == 'Windows':
        sys.exit('Parallel testing is not supported on Windows.')

    if len(_g.overall_run.scripts) > 1:
        _g.multi = True
    _g.overall_run.overview()

    if _g.clargs.parallel:
        from multiprocessing import Pool
        _g.overall_run.scripts = _g.overall_run.scripts * int(_g.clargs.parallel)
        pool = Pool(len(_g.overall_run.scripts))

        temps = pool.map(_runtest_worker, _g.overall_run.scripts)
        pool.close()
        pool.join()

        for temp in temps:
            _g.overall_run.script_runs.append(temp.script_runs[0])
            if temp.complete_failures:
                _g.overall_run.complete_failures.append(temp.complete_failures[0])
        _g.overall_run.collect()
    else:
        _runtests(_g.overall_run.scripts)

    if _g.multi or _g.clargs.parallel:
        _g.overall_run.summarize()
    return _g.overall_run
