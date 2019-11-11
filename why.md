# Why I Made cleartest

I made cleartest because I needed a streamlined alternative to the wordy, high-overhead, restrictive test frameworks in common use. Included in the alternative I wanted:

* Easy parameterized testing
* A simple, customizable test runner
* Full code access to test results
* Built-in options for concurrent testing
* Synchronized standard & error output


 Below are my reasons in more detail.

### To reduce overhead

Modern testing frameworks generally require that every test be wrapped in a function wrapped in a class. cleartest does away with these requirements. Each test is a simple function call. Compare these examples of the same testing:

#### PyUnit (unittest)
```
import unittest

class Overhead(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO','upper()')
    
    def test_lower(self):
        self.assertEqual('FOO'.lower(), 'foo', 'lower()')

    def test_strip(self):
        self.assertEqual(' foo '.strip(), 'foo', 'strip()')
```

#### cleartest
```
import cleartest

def test_main():
    equals('foo'.upper(), 'FOO', 'upper()')
    equals('FOO'.lower(), 'foo', 'lower()')
    equals(' foo '.strip()), 'foo', 'strip()') 
```

cleartest is more concise.

However, you are free to wrap your tests in functions. The main benefit of doing so is exception handling. You're also free to further wrap them in classes. Benefits of that include generalized exception andling and, in the case of cleartest, a built-in option for randomization of test-ordering. cleartest gives you options for both exception handling and randomization. See [Exception Handling](readme.md#exception-handling) and [Class-Based Test Organization](readme.md#class-based-test-organization). The choice is yours. Either way, each test's results are recorded whether it lives in a function or not.

### To give you full access to Python

Python provides you with most of what you need to structure your test code. The design of cleartest is opinionated, but not prescriptive. It offers guidelines, but doesn't limit your options.

### To allow you to order your tests when it matters

A popular idea in testing is that the order of your tests shouldn't matter. As with most things, the truth is more complicated. Often you do need to test an ordered sequence of actions. Other frameworks don't allow you to order your tests and so you're forced to put an entire sequence of actions into a single test. That works, but you lose the granularity of reporting you'd get if you could simply run the actions in order and report the results of each with a test. cleartest allows that.

If you like, you can compress actions into a single test by simply testing the last action or checking state afterward. It also builds in the option of truly randomizing the order of your tests (one framework "randomizes" by running your tests in alphabetical order). The choice is yours. You have full access to Python with cleartest. Nothing is taken from you.

### To ease data-driven/parameterized testing

Parameterized testing is a time & code saver on just about every project. Most testing frameworks don't allow it without additional libraries (that often feature very strange syntax). cleartest doesn't restrict parameterized testing, nor does it build it in. It doesn't need to because Python (and every other language) is built for it already. Simply put your test data into a list or a list of dictionaries or any other data structure and loop over it. You already know how to do that. Example [here](readme.md#data-driven-testing).

### To provide a simple, customizable test runner

cleartest provides flexible and easy methods for running your test suites.
1. With straightforward [command-line arguments](readme.md#organizing-and-running-your-scripts) you can run any combination of files and/or directories. Wildcards are fully supported.
2. You can easily [customize the test runner](readme.md#custom-runners-and-saving-results) with all the same options available from the command line.
3. You can create [simple text files](readme.md#--file-file--f-file) with a list of files and/or directories to run. Again, wildcards are fully supported.

### To make it easy to save & report results

Saving and reporting on test results is essential for anything but one-off testing. cleartest gives you full code access to your results via its `Run` object. Details [here](readme.md#custom-runners-and-saving-results).

### To make concurrent testing simple

Concurrent (i.e. parallel) testing is built into cleartest and is accomplished through a simple argument passed via the command line or in a custom runner. Use it for load testing or simply to save time by running tests concurrently. Details [here](readme.md#testing-in-parallel).

### To have all your output go to one place

So that *all* the results of your tests appear in one place and in the order they happened, cleartest does not use STDERR. Thus in your results you'll see errors in the neighborhood of where they happened and not in a separate log of events out of synch with STDOUT.
