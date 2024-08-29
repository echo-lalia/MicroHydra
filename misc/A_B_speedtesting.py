import time
import math
import random

# this script can easily compare the speed of two functions, to help you write faster code.
# please keep in mind that the order of the tests can affect the results. (around 0~10% usually, in my testing. Sometimes much more.)
# you should be skeptical of the results given by these tests, but large differences can be super informative. 


oneval = 10
twoval = 10


def function_A(val1, val2):
    return (val1 * 10) + oneval

def function_B(val1, val2):
    return (val1 * 10) + twoval





num_samples = 1000
input_list1 = []
input_list2 = []
output_listA = []
output_listB = []

#populate inputs with random numbers before testing
for i in range(num_samples):
    input_list1.append(random.randint(0,8))
    input_list2.append(random.randint(0,8))








print(f"Testing...")
time.sleep(0.1)


#test first function
start_time = time.ticks_cpu()

for i in range(num_samples):
    output_listA.append( function_A(input_list1[i], input_list2[i]) )

stop_time = time.ticks_cpu()
time_diff = time.ticks_diff(stop_time, start_time)

if time_diff > 1000:
    print(f"function_A took {round(time_diff / 1000, 1)}k ticks to complete {num_samples} cycles.")
else:
    print(f"function_A took {time_diff} ticks to complete {num_samples} cycles.")


time.sleep(0.1)


#test second function
start_time = time.ticks_cpu()

for i in range(num_samples):
    output_listB.append( function_B(input_list1[i], input_list2[i]) )

stop_time = time.ticks_cpu()
time_diff2 = time.ticks_diff(stop_time, start_time)

if time_diff2 > 1000:
    print(f"function_B took {round(time_diff2 / 1000, 1)}k ticks to complete {num_samples} cycles.")
else:
    print(f"function_B took {time_diff2} ticks to complete {num_samples} cycles.")
    


#adding more info
print('')
print("Sample of function_A results:", output_listA[0:10])
print("Sample of function_B results:", output_listB[0:10])

print('')

if time_diff < time_diff2:
    ticks_faster = (time_diff2 - time_diff)
    pct = ( ticks_faster / time_diff2 ) * 100
    print("function_A was faster than function_B by:")
    print(f"{ticks_faster} cpu ticks, or {round(pct,1)}%")
else:
    ticks_faster = (time_diff - time_diff2)
    pct = ( ticks_faster / time_diff ) * 100
    print("function_B was faster than function_A by:")
    print(f"{ticks_faster} cpu ticks, or {round(pct,1)}%")

