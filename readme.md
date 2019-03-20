# cleartest: Straightforward Testing for Python

**cleartest** is a lightweight test automation framework for Python 2.7 and Python 3. It features:
* Simple syntax
* Minimal boilerplate code
* Flexible options for discovering and running tests
* Full code access to results
* A parallel processing option (except on Windows)
* Opinions, but few rules on how to structure your code

---

## Contents

* [Installation](#installation)
* [An Example](#an-example)
* [Script Structure](#script-structure)
* [The Test Functions](#the-test-functions)
* [Organizing and Running Your Scripts](#organizing-and-running-your-scripts)
* [Testing in Parallel](#testing-in-parallel) 
* [Custom Runners and Saving Results](#custom-runners-and-saving-results)
* [Exception Handling](#exception-handling)
* [Class-Based Test Organization](#class-based-test-organization)
* [Data-Driven Testing](#data-driven-testing)
* [Other Things to Know](#other-things-to-know)

---

## Installation

`$ pip install cleartest`

---

## An Example

```
from cleartest import ok

def test_main(plan=2):
    ok(True, "This passes.")
    ok(2 + 2 == 4, "This also passes.")
```

To run it:

```
$ runtests test_clear.py
Mon, 2084 Jan 03 10:00:12 UTC

# test_clear.py
1..2
ok 1 - This passes.
ok 2 - This also passes.

# 2 passed, 0 failed.

Mon, 2084 Jan 03 10:00:12 UTC
Time elapsed: 0:00:00.002084
```

If you prefer minimal output (dots), use the -m argument:

```
$ runtests test_39_more.py -m
Mon, 2084 Jan 03 10:00:22 UTC
......................................
# 39 passed, 0 failed.

Time elapsed: 0:00:20.842084
```

---

## Script Structure

Let's explain the structure of a cleartest script by way of our first example:

```
from cleartest import ok

def test_main(plan=2):
    ok(True, "This passes.")
    ok(2 + 2 == 4, "This also passes.")
```

#### The Import
Every cleartest script imports at least one cleartest function. In this case we imported `ok`.

#### test_main

Every cleartest script has a `test_main` function. When cleartest launches it looks for and runs this function. You can put all your tests in `test_main`, but it's better to put them in other functions and call them from `test_main`. Doing so helps to organize your tests and enables finer control of exception handling as we'll see later.

```
from cleartest import ok

def function_one():
    ok(True, "This test is in function_one()")
    ok(True, "This test is also in function_one()")	

def function_two():
    ok(True, "This test is in function_two()")
    ok(True, "This test is also in function_two()")	

def test_main(plan=4):
    function_one()
    function_two()
```

#### The plan

To tell cleartest how many tests you expect to run, include a `plan` parameter in `test_main`, e.g:

`def test_main(plan=4)`

If an unexpected number of tests are run, cleartest will report that. If you *don't* specify a plan, cleartest will simply run the script with no such expectations. We recommend having a plan for all your testing.

---

## The Test Functions

There are 12 test functions:

* ok
* not_ok
* equals
* not_equals
* less_than
* greater_than
* is_type
* isnt_type
* is_in
* isnt_in
* succeed
* fail

---

#### ok & not_ok

`ok` and `not_ok` have two parameters: a required expression and an optional message. `ok` willl pass if the expression evaluates to True. `not_ok` will pass if the expression evaluates to False. For example, both of these tests pass:

```
result = 1

ok(result == 1, "This message is optional.")
not_ok(result == 2)
```

Note that the message will not appear if you choose minimal (-m) output.

---

#### equals, not_equals, less_than, greater_than, is_type, isnt_type, is_in, isnt_in

These eight functions take three parameters: two required expressions and an optional message. The expressions are compared as indicated by the function's name. Here are passing examples of each:

```
result = 1

equals(result, 1, "This message is optional.")
not_equals(result, 2)

less_than(result, 2)
greater_than(result, 0, "This message is optional.")

is_type(result, int, "This message is optional.")
isnt_type(result, bool)

is_in('a', 'abc')
isnt_in(3, [0, 1, 2], "This message is optional.")
```

Using these functions is generally preferred over ok & not_ok for their more detailed failure reporting. For example:

```
result = 1

ok(result == 0)
equals(result, 0)
```

Produces:

```
not ok 1
#   Failure at line 8 in /path/to/test_sample.py.

not ok 2
#   Failure at line 9 in /path/to/test_sample.py.
#        got: 1
#   expected: 0
```

`ok` only tells you the line where the failure happened; `equals` also tells you what it expected and what it got.

---

#### succeed & fail

Sometimes you just want to report that a test has passed or failed. Usually this is because the pass/fail condition is difficult to fit into a single statement. That's what `succeed` and `fail` are for. `fail` is also used for exception testing as you'll see later.

```
if the_complicated_code_did_what_we_expected:
    succeed('The complicated code did what we expected.')
else:
    fail('The complicated code did NOT do what we expected.')
```

---

#### Return Values

All test functions return `True` if they succeed and `False` if they fail so you may use them as conditions in your code.

---

## Organizing and Running Your Scripts

#### Naming Requirement

All test scripts must have a name of the form "test_*.py". Examples:

* test_requests.py
* test_left_search.py

#### Using runtests

To run all the test scripts in the current directory, use **runtests** with no arguments:

`$ runtests`

To run a specific script or set of scripts, add their paths as arguments. Unix-style wildcards and directory expansion are supported:

```
$ runtests test_requests.py
$ runtests test_requests.py test_search.py secure/test_https.py
$ runtests test_load* test_??.py

$ runtests ../
$ runtests security_tests/
$ runtests ui_tests/ security_tests/ load_tests/test_basic* test_initialize.py
```

#### Making Test Scripts Executable

To make a test script executable so it can run on its own:
1. Set the script's permissions to executable (e.g. chmod 755).
2. Add the appropriate hash-bang line to the top of the script.
3. Import and call the `go` function under `if __name__ == "__main__"`.

```
#!/usr/bin/env python

from cleartest import ok, go

def test_main():
	ok(True, "This passes.")

if __name__ == '__main__':
	go()
```

Assuming this script was called test_individual.py you can now run it like this:

```
$ ./test_individual.py
```

Of course, you can still run it as an argument to **runtests**, i.e. `$ runtests test_individual.py`.

### Arguments

#### --recursive, -r

To recursively search directories for test scripts to run, use the `-r` argument. It's an all-or-nothing feature so the 2nd example below will recursively search both directories:

```
$ runtests -r
$ runtests edit_dir/ search_dir/ -r
```

#### --file FILE, -f FILE

To make a custom suite of scripts to run, list their paths in a text file, one per line. Paths may be absolute or relative to the location of the text file. For example, *test_suite.txt* might contain the lines below.

test_suite.txt:
```
request_types/test_secure_calls.py
load_tests/test_*
test_???.py
load_dir/
/path/to/distant/directory/
/path/to/other/directory/test_the_others.py
```

To run the suite:

```
$ runtests -f test_suite.txt
```

#### --minimal, -m

For minimal output (dots), use the `-m` argument:

```
$ runtests -m
$ ./test_sample -m
```

#### --quiet, -q

For quiet output, use the `-q` argument. You'll only see the overview, summary, and failure & exception output:

```
$ runtests -q
$ ./test_sample -q
```

#### --timestamp, -t

To print a UTC timestamp between each script run, use the `-t` argument:

```
$ runtests -t
```

Partial example output:

```
ok 24
ok 25

# 25 passed, 0 failed.

Time elapsed: 0:00:03.676329

00:19:81 UTC

# test_likes.py
1..17
ok 1
ok 2
```

This option does nothing with quiet `-q` or minimal `-m` output or when running a single script.

#### --parallel [PARALLEL], -p [PARALLEL]

To run tests scripts in parallel, use the -p argument. See the next section for details.

---

## Testing in Parallel

For load/stress/availability testing or just to save time you can run test scripts in parallel with the `-p` or `--parallel` argument along with the number of instances of each script to run. The default number of instances is 1 so `-p` and `-p 1` are equivalent.

This feature isn't supported on Windows.

Here we launch 100 instances of test_load.py, each in its own process. We also use the minimal (-m) option to avoid the jumbled output parallel runs produce.

```
$ runtests test_load.py -m -p 100
```

To save time on functional tests you can also run multiple scripts in parallel. For example, if the *functional* directory contains 3 test scripts, either command below will run all 3 in parallel.

```
$ runtests functional/ -m p
$ runtests functional/ -m p 1
```

If you want to add load to the example above, increase the number of processes. For example, the command below will run 10 instances of each script in the *functional* directory in parallel for a total of 30 processes.

```
$ runtests functional/ -m -p 10
```

---

## Custom Runners and Saving Results

cleartest gives you full access to a test script's results via its `Run` object. You can access those results, save, and report on them.  Here are the properties of a `Run` object:

* **name** - The module name of the script, e.g. "test_conditional"
* **path** - The path to the script, e.g. "/path/to/test_conditional.py"
* **plan** - # of tests we planned to run
* **ran** - # of tests we actually ran
* **passed** - # of tests that passed
* **failed** - # of tests that failed
* **errors** - # of exceptions thrown
* **underrun** - True if we ran fewer tests than planned, false otherwise
* **overrun** - True if we ran more tests than planned, false otherwise
* **failures** - A list of test failure details
* **stack_traces** - A list of stack traces from unexpected exceptions
* **start_time** - A UTC datetime.datetime object set at the beginning of the run
* **end_time** - A UTC datetime.datetime object set at the end of the run
* **time_elapsed** - A datetime.timedelta object of the duration of the run

#### The overall `Run` object also has the following properties:

* **parallel** - # of instances per script if run in parallel (e.g. -p 2 will set this to 2.)
* **script_runs** - A list of `Run` objects, one for each script run
* **complete_failures** - A list of scripts which failed to run

---

To see how to use the `Run` object let's first have a look at **runtests**, the default cleartest runner:

```
from cleartest import go
go()
```

That's it. It imports the `go` function and calls it. What it doesn't show is that `go()` returns a `Run` object. The `Run` object contains our overall results and the results of each script in `script_runs`. Let's make our own runner which saves the `Run` object in a variable we'll call `results`. Then we'll print its contents.

```
from cleartest import go
results = go()

print "\nContents of TestRun object"
print "--------------------------"

# Overall object
print 'name:', results.name
print 'start_time:', results.start_time
print 'end_time:', results.end_time
print 'time_elapsed:', results.time_elapsed
print 'parallel:', results.parallel
print 'plan:', results.plan
print 'ran:', results.ran
print 'passed:', results.passed
print 'failed:', results.failed
print 'errors:', results.errors
print 'underrun:', results.underrun
print 'overrun:', results.overrun
print 'script_runs:', results.script_runs
print 'failures:', results.failures
print 'stack_traces:', results.stack_traces
print 'complete_failures:', results.complete_failures
print
for script_run in results.script_runs:
    print 'name:', script_run.name
    print 'path:', script_run.path
    print 'start_time:', script_run.start_time
    print 'end_time:', script_run.end_time
    print 'time_elapsed:', script_run.time_elapsed
    print 'plan:', script_run.plan
    print 'ran:', script_run.ran
    print 'passed:', script_run.passed
    print 'failed:', script_run.failed
    print 'errors:', script_run.errors
    print 'underrun:', script_run.underrun
    print 'overrun:', script_run.overrun
    print 'failures:', script_run.failures
    print 'stack_traces:', script_run.stack_traces
    print
```

Let's call it custom_runner.py and run it against a couple of sample scripts, e.g.

```
$ python custom_runner.py test_1.py test_2.py
```

We see our usual output plus all the things we explicitly printed:

```
Contents of TestRun object
--------------------------
name: Overall
start_time: 2084-01-03 10:00:00.001000
end_time: 2084-01-03 10:00:00.005000
time_elapsed: 00:00:00.002000
parallel: None
plan: 5
ran: 4
passed: 3
failed: 1
errors: 1
underrun: True
overrun: False
script_runs: [<cleartest.Run object at 0x10d7f4c10>, <cleartest.Run object at 0x10d818510>]
failures: [{'expected': 3, 'got': 4, 'line': 10, 'script': '/path/to/test_1.py'}]]
stack_traces: ['Traceback (most recent call last):\n  File "/path/to/cleartest.py", line 226, in _run\n    return test_function(*args,**kwargs)\n  File "/path/to/test_2.py", line 7, in unexpected_exception\n    throw_exception = 1 / 0\nZeroDivisionError: integer division or modulo by zero\n']
complete_failures: []

name: test_1
path: /path/to/test_1.py
start_time: 2084-01-03 10:00:00.002000
end_time: 2084-01-03 10:00:00.003000
time_elapsed: 00:00:00.001000
plan: 2
ran: 2
passed: 1
failed: 1
errors: 0
underrun: False
overrun: False
failures: [{'expected': 3, 'got': 4, 'line': 10, 'script': '/path/to/test_1.py'}]
stack_traces: []
complete_failure: None

name: test_2
path: /path/to/test_2.py
start_time: 2084-01-03 10:00:00.003100
end_time: 2084-01-03 10:00:00.004100
time_elapsed: 00:00:00.001000
plan: 3
ran: 2
passed: 2
failed: 0
errors: 1
underrun: True
overrun: False
failures: []
stack_traces: ['Traceback (most recent call last):\n  File "/path/to/cleartest.py", line 226, in _run\n    return test_function(*args,**kwargs)\n  File "/path/to/test_2.py", line 7, in unexpected_exception\n    throw_exception = 1 / 0\nZeroDivisionError: integer division or modulo by zero\n']
complete_failure: None
```

First we see the contents of the overall `Run` object. Then we see the results of each script in `results.script_runs`. Each item in this list is a `Run` object itself.

Of course you can do more than just print your results; Save them to a database, put them on a web page, email them, or post them to a group chat. Do as you like.

### A couple of things to note:

* The overall `Run` object has a consolidated list of failures and stack traces from all scripts.
* `stack_traces` only stores the traces from unexpected exceptions.

---

### Command-line Arguments and Custom Runners

Command-line arguments (paths, -f, -r, -p, -m, -q, -t) still apply to custom runners like the one above. However, you can override or set them by calling `go` with any combination of these arguments:

* **paths** - A list of file and/or directory paths, each in string form
* **suite_file** - The path of a suite file in string form
* **recursive** - A boolean
* **parallel** - An int
* **minimal** - A boolean
* **quiet** - A boolean
* **timestamp** - A boolean

Examples:

```
results=go(paths=['test_simple.py', 'test_not_so_simple.py'])
results=go(suite_file='/path/to/load_suite.txt')
results=go(recursive=True)
results=go(parallel=64)
results=go(minimal=True)
results=go(quiet=True)
results=go(timestamp=True)

results=go(paths=['load/'], parallel=16, recursive=True)
results=go(parallel=0, recursive=False)
results=go(paths=['ui_tests/', 'security_tests/', 'load_tests/test_basic*', 'test_initialize.py'], timestamp=True)
```

Here's a simplified example of a runner that runs a suite of tests serially, then checks that it ran the correct number of tests. If so, it runs the same tests in parallel and compares results:

```
from cleartest import go

serial_run = go(suite_file='test_suite.txt')
if serial_run.ran == 2084:
    parallel_run = go(parallel=1, suite_file='test_suite.txt')

if parallel_run.passed == serial_run.passed == parallel_run.plan == serial_run.plan
    print 'Deploy!'
```

Here's a simplified example of a runner that runs three sets of tests and reports the passing percentage of each to a Slack channel:

```
from cleartest import go
import json, requests

data_validation = go(paths=['/path/to/data_validation/'], quiet=True)
ui = go(paths=['/path/to/ui/'], quiet=True)
availability = go(paths=['/path/to/availability/'], parallel=16, quiet=True)

results = "Data Validation: {:.2%} passed.\n".format(float(data_validation.passed) / data_validation.plan)
results += "UI: {:.2%} passed.\n".format(float(ui.passed) / ui.plan)
results += "Availability: {:.2%} passed.".format(float(availability.passed) / availability.plan)

response = requests.post(
    'https://hooks.slack.com/services/AAAAAAAAA/BBBBBBBBB/CCCCCCCCCCCCCCCCCCCCCCCC',
    data=json.dumps({'text': results, 'username': 'autobot', 'channel': '#automation'}),   
    headers={'Content-Type': 'application/json'}
)
```

Output to Slack would look something like this:

```
autobot APP [05:00 PM]  
Data Validation: 100.00% passed.  
UI: 99.50% passed.  
Availability: 100.00% passed.
```

---

#### Logging Example

This runner sends *all* of its output to STDOUT and to a log file named with a timestamp, e.g, `2084.01.03-05.00.01.001981.log`

```
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(datetime.datetime.utcnow().strftime('%Y.%m.%d-%H.%M.%S.%f.log'), 'w', 0)

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass

sys.stdout = Logger()

print ' '.join(sys.argv) # Log the command line.
from cleartest import go
results = go()
```

Note that **cleartest** does not use STDERR for errors that it handles.

---

## Exception Handling

As with any Python script, execution of a test script will cease if it throws an exception. If this happens **runtests** itself will not cease; It will simply continue to the next script in its queue. However, to handle unexpected exceptions on a per-function basis use the `@ctc` decorator (*cleartest catcher*) on your test functions. Note that `test_main` is not a test function.

```
from cleartest import ctc, ok

@ctc
def worrisome():
    throw_exception = 1 / 0
    ok(True, 'This would pass but for that exception.')

def carry_on():
    ok(True, 'This function ran because cleartest caught the exception above.')

def test_main(plan=3):
    worrisome()
    carry_on()
    ok(True, 'This test is in test_main() and ran because cleartest caught the exception above.')
```

Produces:

```
1..3
Traceback (most recent call last):
  File "/path/to/cleartest.py", line 149, in _run
    return test_function(*args,**kwargs)
  File "/path/to/test_unexpected_exception.py", line 7, in worrisome
    throw_exception = 1 / 0
ZeroDivisionError: integer division or modulo by zero

ok 1 - This function ran because cleartest caught the exception above.
ok 2 - This test is in test_main() and ran because cleartest caught the exception above.

# Looks like you ran 2 tests, but planned 3.

# 2 passed, 0 failed.
# 1 error
```

In this case an "unexpected" exception occurred at the top of `worrisome` so the rest of the function didn't run. However, because we decorated it with the exception catcher `@ctc`, execution continued to our next function `carry_on`. Note cleartest's reporting on the exception and the script not living up to its plan.

If you remove the `@ctc` decorator from `worrisome` the script will throw an exception and quit before any tests have a chance to run. cleartest will then move on to the next script in its queue.

```
1..3
Traceback (most recent call last):
  File "/path/to/cleartest.py", line 274, in runtests
    vars.__call__()[script['module']].test_main()
  File "/path/to/test_unexpected_exception.py", line 14, in test_main
    unexpected_exception()
  File "/path/to/test_unexpected_exception.py", line 7, in unexpected_exception
    throw_exception = 1 / 0
ZeroDivisionError: integer division or modulo by zero

# Looks like you ran 0 tests, but planned 3.

# 0 passed, 0 failed.
# 1 error
```

---

#### Class-Based Exception Handling

If you'd like to decorate a large number of functions with `@ctc`, you can save keystrokes by placing them in a class decorated with `Ctc` as follows:

1. Import `Ctc` (note the upper case C).
2. Decorate a test class with it.
3. Create your test functions as instance methods of the class.

```
from cleartest import Ctc

@Ctc
class ExceptionalTests(object):

    def worrisome(self):
        ...

    def carry_on(self):
        ...
```

This will apply `@ctc` to every function in `ExceptionalTests`.

---

## Class-Based Test Organization

As a shortcut, you can use `run_class` to call every method in a class instance in random order.

```
from cleartest import run_class

class ExceptionalTests():

    def test_this(self):
        ...

    def test_that(self):
        ...

def test_main():
    run_class(ExceptionalTests())
```

This will run `test_this`, `test_that`, and any other functions that may be in `ExceptionalTests` in random order. 

Decorate instance methods with `@skip` if you want `run_class` to ignore them.

```
@skip
def utility_function_containing_no_tests()
    ...
```

For more control, call the methods individually. Or don't use classes at all.

---

#### Testing for Exceptions

To test expected exceptions use a **try/except** block:

```
from cleartest import *

def expected_exception():
    try:
        new_variable = undefined_variable
        fail('There should have been an exception here.')
    except Exception as e:
        equals(str(e), "global name 'undefined_variable' is not defined", str(e))

    ok(True, 'This passes.')

def test_main(plan=2):
    expected_exception()
```

Produces:

```
1..2
ok 1 - global name 'undefined_variable' is not defined
ok 2 - This passes.

# 2 passed, 0 failed.
```

Notice how we use `fail` in the `try` block in case an exception is *not* thrown.

---

## Data-Driven Testing

Data-driven testing is just a matter of running different data over the same code. Make use of Python's built-in data structures and simply loop over them, e.g:

```
from cleartest import *
import requests

cases = [
    {
        'url': 'http://httpbin.org/html',
        'expected_content-type': 'text/html; charset=utf-8',
        'message': '/html Content-Type is text/html; charset=utf-8.'
    }, {
        'url': 'https://httpbin.org/json',
        'expected_content-type': 'application/json',
        'message': '/json Content-Type is application/json.'
    }, {
        'url': 'https://httpbin.org/xml',
        'expected_content-type': 'application/xml',
        'message': '/xml Content-Type is application/xml.'
    }
]

@ctc
def httpbin(case):
    results = requests.get(case['url'])
    equals(results.headers['Content-Type'], case['expected_content-type'], case['message'])

def test_main(plan=len(cases)):
    for case in cases:
        httpbin(case)

if __name__ == '__main__':
    go()
```

Produces:

```
1..3
ok 1 - /html Content-Type is text/html; charset=utf-8.
ok 2 - /json Content-Type is application/json.
ok 3 - /xml Content-Type is application/xml.

# 3 passed, 0 failed.
```

To summarize:
* We define sets of test data in a list called `cases`.
* In `test_main` we simply loop over `cases` feeding each set of data to our test function `httpbin`.
* Notice how we let the length of the `cases` list calculate the plan for us.

For more complex scenarios it usually makes sense to move the data out of your test scripts and into a separate file that you import. For very complex scenarios it's sometimes best to read test data out of a database.

---

## Other Things to Know

#### True vs. Truthy and False vs. Falsey

Earlier we wrote that an `ok` test will pass if its expression evaluates to `True`. In reality, it will pass if its expression evaluates to "truthy", e.g. `True`, `'ca'`, `15`, `int`, `['Brass', 'Gaia Project']` etc.

Similarly a `not_ok` test will pass if its expression evaluates to something "falsey": `False`, `0`, `''`, `[]` etc.

---

#### STDOUT and STDERR

**cleartest** does not use STDERR. A simple pipe or redirect will catch all of its output, e.g:

```
$ runtests smoke/ > temp.txt
$ runtests smoke/ >> results.log
$ runtests smoke/ | tee temp.txt
$ runtests smoke/ | more
```

Also see [logging example](#logging-example).
