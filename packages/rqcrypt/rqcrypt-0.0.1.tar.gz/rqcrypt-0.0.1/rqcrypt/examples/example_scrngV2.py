import sys
import time

import colorama

import rqcrypt as rc

colorama.init(autoreset=True)


def delay_print(s, delay: float = 0.1, end: str = "\n"):
    for c in s:
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(end)


def continous_input(prompt: str, msg_when_wrong: str, in_type):
    global correct
    correct = None
    a = input(prompt)
    while True:
        try:
            correct = in_type(a)
            break
        except ValueError:
            a = input(msg_when_wrong)
            continue
    return correct


def example_scrngV2():
    delay_print("Welcome to ShadowCrypt!", end=" ")
    time.sleep(0.5)
    delay_print("This is an example of the core algorithm.")
    delay_print(
        "-" * (67 - 1),  # SIX-SEVEN!!!!!!!
        delay=0.005,
    )
    time.sleep(0.5)
    delay_print("The function that you use is called random_nums().", end=" ")
    time.sleep(0.5)
    delay_print(
        "To use it, pass in your range, a and b, and how many numbers to generate, n.",
        end="\n",
    )
    time.sleep(0.2)
    print(colorama.Style.BRIGHT + "============= LEARNING IN PROGRESS =============")
    time.sleep(0.1)
    delay_print("Let's start with the range, a and b.")
    time.sleep(0.25)
    print("Enter a (any integer):", end=" ")
    a = continous_input("", "Please, an integer: ", int)
    time.sleep(0.05)
    print("Enter b (any integer):", end=" ")
    b = continous_input("", "Please, an integer: ", int)
    delay_print("Now, the amount of numbers you would like to generate, n.")
    time.sleep(0.25)
    print("Enter n (any integer):", end=" ")
    time.sleep(0.2)
    n = continous_input("", "Please, an integer: ", int)
    delay_print("There is also a base or pretty mode.", end=" ")
    time.sleep(0.5)
    delay_print("First, I'll show you the base mode:")
    time.sleep(0.1)
    print(colorama.Style.BRIGHT + "============= GENERATION IN PROGRESS =============")
    nums_base = rc.random_nums(a=a, b=b, n=n)
    delay_print("And your numbers are: ", end="")
    time.sleep(0.5)
    delay_print(str(nums_base), delay=0.05)
    delay_print("-" * (len(str(nums_base)) + 23), delay=0.005)
    time.sleep(0.5)
    delay_print("Now, the pretty mode (the output speaks for itself):")
    time.sleep(0.1)
    print(colorama.Style.BRIGHT + "============= GENERATION IN PROGRESS =============")
    _ = rc.random_nums(a=a, b=b, n=n, mode="pretty")
    time.sleep(0.5)
    delay_print("And that's all, folks! Thanks for using this tutorial.")
    delay_print(
        "------------------------------------------------------------", delay=0.005
    )
    delay_print("Copyright © 2026 Rohan Date.", delay=0.05)


if __name__ == "__main__":
    print(dir(rc))
    example_scrngV2()
