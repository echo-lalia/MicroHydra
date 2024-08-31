"""
This script can easily compare the speed of two functions, to help you write faster code.

Please keep in mind that the order of the tests can affect the results. (around 0~10% usually, in my testing. Sometimes much more.)
Lots of other things can also affect the speed, so speed differences in this environment could be super different than speed differences in others.
The test process itself also uses a little bit of time, so functions that are already very fast will be harder to test.

You should be skeptical of the results given by this test, but large differences can be super informative.
"""

import time
import random




# #==============================================================================#
# ||                                                                            ||
# ||                              Test Functions:                               ||
# ||                                                                            ||
# #==============================================================================#
# Define the functions you want to compare here.


def test_a(val1, val2):
    return min(val1, val2)


def test_b(val1, val2):
    if val1 < val2:
        return val1
    return val2




# #==============================================================================#
# ||                                                                            ||
# ||                                Test Setup:                                 ||
# ||                                                                            ||
# #==============================================================================#
# Edit these parameters to configure the tests


# A list of functions to test:
functions = [
    test_a,
    test_b,
]

# Optionally, assign functions a friendly name here:
# This is useful for viper functions, because they have no __name__
# The key should be the function itself, and the value should be a string.
friendly_names = {
    test_a:'test a',
}


# The type and length of the input data for the tests:
# Should be a list of dicts with 'type', 'min', and 'max'
# current allowed types are 'int', 'float', and 'str'
# if 'str' is specified, the min/max defines the length of the string.
input_params = [
    {'type':int, 'min':-100, 'max':100},
    {'type':float, 'min':0, 'max':100},
]

# how many tests to do:
# Before each pair of tests, random data must be generated equal to tests_per_run,
# which can quickly cause memory errors if the number is too large.
# For each run, both functions are tested, and the test order is reversed.
# So the total number of functions called will be num_runs * tests_per_run * 2
tests_per_run = 200
num_runs = 10

# this is the timing unit to use:
# acceptable values are "s", "ms", "us", or "cpu"
# Really small units like "cpu" will usually be inaccurate due to overflow
timing_unit = 'ms'




# #==============================================================================#
# ||                                                                            ||
# ||                                Test Script:                                ||
# ||                                                                            ||
# #==============================================================================#
# This is the body of the script.
# You shouldn't need to edit this unless you want to extend the script (or see how it works).

# the dict above is required because viper functions have no name
# We actually want an ordered list for the tests, so make that now:


# store total ticks for each function in a dict
test_results = {func:0 for func in functions}
output_data = {func:[] for func in functions}


# set timing function from unit name
if timing_unit == 'ms':
    timing_func = time.ticks_ms
elif timing_unit == 'us':
    timing_func = time.ticks_us
elif timing_unit == 'cpu':
    timing_func = time.ticks_cpu
elif timing_unit == 's':
    timing_func = time.time
else:
    raise ValueError(f"'{timing_unit}' isn't a valid timing unit.")


# test data generator
def gen_data(data_def):
    d_type = data_def['type']
    d_min = data_def['min']
    d_max = data_def['max']
    
    if d_type == int:
        return random.randint(d_min, d_max)
    if d_type == float:
        return random.uniform(d_min, d_max)
    if d_type == str:
        str_len = random.randint(d_min, d_max)
        # randomly gen or dont gen ext chars
        max_ord = 1_112_064 if random.randint(0,3) == 0 else 127
        return ''.join(chr(random.randint(0, max_ord)) for _ in range(str_len))


# fallback for functions with no '__name__'
def func_name(func):
    if func in friendly_names:
        return friendly_names[func]
    if hasattr(func, '__name__'):
        return func.__name__
    return str(func)



# do each run
for run in range(num_runs):
    print(f"Run {run}...")
    
    # generate data for the tests in this run
    test_data = []
    for _ in range(tests_per_run):
        test_data.append(
            tuple(gen_data(data_def) for data_def in input_params)
        )
    
    
    for test_func in functions:
        start_time = timing_func()
        
        # for each test, unpack the input data and feed it to the test func
        # and, capture the output to inspect later
        for i in range(tests_per_run):
            output_data[test_func].append(
                test_func(*test_data[i])
            )
        
        end_time = timing_func()
        
        # add the time difference to the test results
        test_results[test_func] += time.ticks_diff(end_time, start_time)
    

    # only for final run, print a bit of diagnostic data on the tests
    if run == num_runs - 1:
        print(f"Sample of test data: {test_data[:6]}")
    
        for func in functions:
            print(f"Sample of '{func_name(func)}' output: {output_data[func][:10]}")



    # reverse order for next run
    functions.reverse()
    # reset output data (so it doesn't get too large)
    output_data = {func:[] for func in functions}


# get the functions with best/worst performance
best_func = min(functions, key=lambda f: test_results[f])
worst_func = max(functions, key=lambda f: test_results[f])
max_difference = test_results[worst_func] - test_results[best_func]

print("\nTest complete.")
for func in functions:
    print(f"- '{func_name(func)}' took {test_results[func]}{timing_unit} to complete {tests_per_run*num_runs} tests.")

# if test is too fast, no result can be observed (also a divide by zero will happen)
if test_results[worst_func] == 0:
    print(f"The slowest function took 0{timing_unit} to complete, so no comparison can be made.")
elif test_results[worst_func] == test_results[best_func]:
    print(f"All of the functions took {test_results[best_func]}{timing_unit} to complete.")
else:
    print(f"""
'{func_name(worst_func)}' was the slowest function.

'{func_name(best_func)}' was the fastest, beating the slowest by {max_difference}{timing_unit},
or {(max_difference / test_results[worst_func]) * 100:.2f}%

""")

