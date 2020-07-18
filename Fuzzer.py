#! /usr/bin/env python3
from pwn import *
import subprocess
import json
import random
import csv
from io import StringIO

def delete_random_character(s):
    """Returns s with a random character deleted"""
    flag = random.randint(0, 1)
    if flag == 0 or s == "":
        return s
    else:
        position = random.randint(0, len(s) - 1)
        return s[:position] + s[position + 1:]

def insert_random_character(s):
    """Returns s with a random character inserted"""
    # here you change adjust how possible you will do this kind of mutation to the string
    flag = random.randint(0, 1)
    if flag == 0:
        return s
    else:
        position = random.randint(0, len(s))
        random_character = chr(random.randrange(32, 127))
        return s[:position] + random_character + s[position:]

def generateRandomStr(min_length, max_length):
    string_length = random.randrange(min_length, max_length + 1)
    out = ""
    for i in range(0, string_length):
        out += chr(random.randrange(32, 127))
    return out

# choose one fuzz method to mutate string
def mutate(s):
    mutators = [
        "delete",
        "insert",
        "bit_flip",
        "radom",
        "enlarge",
    ]
    mutator = random.choice(mutators)
    if mutator == "delete":
        return delete_random_character(s)
    elif mutator == "insert":
        return insert_random_character(s)
    elif mutator == "bit_flip":
        return bit_flip(s, 1/len(s))
    elif mutator == "bit_flip":
        return generateRandomStr(1, 100)
    elif mutator == "enlarge":
        return s * 500
    else:
        return s

# only deal with 3 specific types of data
def handleDataType(value):
    if type(value) == int:
        # generate a random number
        # here can do more complicated operation on int number
        flag = random.randint(0, 1)
        if flag == 0:
            return value
        else:
            return random.randint(0, 100)  # adjust the range of number
    elif type(value) == list:
        temp = []
        for i in value:
            flag = random.randint(0, 1)
            if flag == 0:
                temp.append(i)
            else:
                temp.append(mutate(i))
        return temp                 #TODO: Mute list in a different wayS
    elif type(value) == str:
        return mutate(value)
    else:
        return value

# after parsing json file, mutate each field
def parseJson(jsonfile):
    with open(jsonfile, "r") as f:
        json_data = json.load(f)
    # separate keys and values of json_data
    keys = []
    values = []
    for i in json_data.keys():
        keys.append(i)
    for i in keys:
        values.append(json_data[i])

    # mutate keys
    for i in range(len(keys)):
        keys[i] = mutate(keys[i])
    # mutate values
    for i in range(len(values)):
        values[i] = handleDataType(values[i])

    # re-assemble the keys and values back to dict
    json_data = {}
    for i in range(len(keys)):
        json_data[keys[i]] = values[i]
    return json_data


def parseCSV(csvfile):
    output = ""
    with open(csvfile, "r") as f:
        if_header = True
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            if if_header:
                temp_row_list = []
                for i in range(len(row)):
                    temp_row_list.append(row[i])
                if_header = False
            else:
                temp_row_list = []
                for i in range(len(row)):
                    temp_row_list.append(mutate(row[i]))
            
            output += ",".join(temp_row_list)+ '\n'
    # print(output)
    return output

def bit_flip(s, percent_of_flip):
    length = len(s)
    num_of_flips = int(length * percent_of_flip)
    # print("num_of_flips: ", num_of_flips) #!!!!!!!!!!!!

    chosen_indexes = []
    # iterate selecting indexes until hit the num_of_flips number
    counter = 0
    while counter < num_of_flips:
        chosen_indexes.append(random.choice(range(length)))
        counter += 1
    # print("chosen_indexes: ", chosen_indexes)

    s_list = []
    for i in s:
        s_list.append(i)

    # flip one random bit in each chosen character
    for i in chosen_indexes:
        # convert char to 8-bit string
        current = "{:08b}".format(ord(s[i]))
        # print(f"current: binary of {s[i]} is ", current)

        # choose one bit of the character
        picked_index = random.choice(range(8))
        new_list = []
        for j in current:
            new_list.append(j)
        if new_list[picked_index] == '1':
            new_list[picked_index] = '0'
        else:
            new_list[picked_index] = '1'
        new = ""
        for j in new_list:
            new += j
        # print(f"    new: binary of {s[i]} is ", new)
        new_char = chr(int(new, 2))
        # print(f"old:{ord(s[i])} vs new:{int(new, 2)}")
        # print(f"old:{s[i]} vs new:{new_char}")
        s_list[i] = new_char

    new_s = ""
    for i in s_list:
        new_s += i

    # print("old string: ", s)
    # print("new string: ", new_s)
    return new_s


class BinaryRunner(object):
    # Test outcomes
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"

    def __init__(self, binary):
        """Initialize"""
        self.binary = binary

    def run_process(self, inp=""):
        """Run the program with `inp` as input.  Return result of `subprocess.run()`."""
        return subprocess.run(self.binary,
                              input=inp,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              universal_newlines=True)

    def run(self, inp=""):
        """Run the program with `inp` as input.  Return test outcome based on result of `subprocess.run()`."""
        result = self.run_process(inp)
        if result.returncode == 0:
            outcome = self.PASS
        elif result.returncode < 0:
            outcome = self.FAIL
        else:
            outcome = self.UNRESOLVED
        return (result, outcome)


class Fuzzer(object):
    def __init__(self):

        pass

    def fuzz(self):
        """Return mutated input"""
        return ""

    def run(self, runner):
        """Run `runner` with fuzz input"""
        # record the bad input
        mutated = self.fuzz()
        print("Trying!!!")
        print(mutated)
        result = runner.run(mutated)[0]
        if result.returncode < 0:
            with open("bad.txt", 'a') as f:
                f.write(mutated)
                f.write("\n")
        return runner.run(mutated)


class csvFuzzer(Fuzzer):
    def __init__(self, sample_input):
        self.file = sample_input

    def fuzz(self):
        mutated_csv = parseCSV(self.file)
        # mutated_string
        return mutated_csv

class jsonFuzzer(Fuzzer):
    def __init__(self, sample_input):
        self.file = sample_input

    def fuzz(self):

        mutated_json = parseJson(self.file)
        mutated_string = json.dumps(mutated_json)

        # return mutated input
        # print(f"Trying!!! {mutated_string}")   #!!!!!!
        return mutated_string


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("usage: fuzzer binary input")
        sys.exit()
    else:
        binary = sys.argv[1]
        source_input = sys.argv[2]

    # initialize the object to run the binary
    runner = BinaryRunner("./" + binary)
    # read the source input
    inl = open('./'+source_input, 'r').read()
    # print(runner.run(inl))

    num_of_iteration = 10
    # here is just a basic judgement
    if "csv" in source_input:
        for i in range(num_of_iteration):
            print(f"{i+1}th time: ", end=' ')
            csv_fuzzer = csvFuzzer("./" + source_input)
            result = csv_fuzzer.run(runner)[0]
            if result.returncode < 0:
                print(result.returncode)
                print("**", result.stdout)
    elif "json" in source_input:
        for i in range(num_of_iteration):
            print(f"{i+1}th time: ", end=' ')
            json_fuzzer = jsonFuzzer("./" + source_input)
            result = json_fuzzer.run(runner)[0]
            if result.returncode < 0:
                print(result.returncode)
                print("**", result.stdout)
    else:
        print("input file error")
        sys.exit()
