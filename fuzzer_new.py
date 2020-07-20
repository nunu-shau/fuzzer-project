#!/usr/bin/python3
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
    """Generates a string with random characters with a length between min_length and max_length"""
    
    string_length = random.randrange(min_length, max_length + 1)
    out = ""
    for i in range(0, string_length):
        out += chr(random.randrange(32, 127))
    return out

# choose one fuzz method to mutate string
def mutate(s):
    """Randomly choose one fuzzing strategy to mutate a string with"""
    mutators = [
        "delete",
        "insert",
        "bit_flip",
        "random",
        "enlarge",
        "empty",
        "none"
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
    elif mutator == "random":
        return generateRandomStr(1, 100)
    elif mutator == "enlarge":
        return s * random.randint(2, 1000)
    elif mutator == "none":
        return ""
    else:
        return s

# needs to improverandint
def repeter(inp, n=1000):
    return inp * n

# only deal with 3 spefic types of data
def handleDataType(value):
    """Determines what data type a field contains and mutates accordingly"""
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
        return temp                 # no idea how to deal with list in a good way
    elif type(value) == str:
        return mutate(value)
    else:
        return value

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

def is_JSON(fileName):
    is_json_file = True
    try:
        with open(fileName, 'r') as f:
            json.load(f)
    except:
        is_json_file = False
    return is_json_file

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
    def __init__(self, inputFile):
        # Generic varaibles to manage array representation of fields
        self._input = None
        self.index = 0
        self.it = 0
        self._type = None  

    def _read_as_str(self, fileName):
        self._str = ""
        try:
            with open(fileName, 'r') as f:
                for line in f:
                    self._str += line + "\n"
        except:
            print(f"Failed to read string from file: {fileName}")
            exit(1)


    # Mutates a fields with input that attack common vulnerabilities
    # Will select input depending on input type and itteration
    # Modifies the "input" attribute of fuzzer
    # Returns True on success, return False otherwise
    def dictionary_attack(self):
        mutation = None
        while (mutation == None):
            if (self.index >= len(self._input)):
                break
            if (self.it == 0):
                self._type = type(self._input[self.index])
            
            if (self._type == int):
                mutation = self._dictionary_int()
                if (not mutation == None): 
                    self._input[self.index] = mutation
                    self.it += 1
                else:
                    self.index += 1
                    self.it = 0
            elif (self._type == str):
                mutation = self._dictionary_str()
                if (not mutation  == None):
                    self._input[self.index] = mutation
                    self.it += 1
                else:
                    self.index += 1
                    self.it = 0
            else:
                mutation = False

        return mutation == None



    def _dictionary_str(self):
        # Add more strs that may be usefull agains common vulnerabilities
        large_num = 0x100
        str_vulns = ["%n"*large_num,"%s"*large_num,  "\"", "\'", "`",  ";", "{", "}", "(", ")", "<", ">"]
        if (self.it < len(str_vulns)):
            return str_vulns[self.it]
        else:
            return None

    # Returns a int which can be used against common vulnerabilities
    def _dictionary_int(self):
        # Add more ints that may be usefull agains common vulnerabilities
        int_vulns = [0, 1, -1, 0x100, 0x10000, 0xffffffff]
        if(self.it < len(int_vulns)):
            return int_vulns[self.it]
        else:
            return None


    # Mutates the structure of the input to attack assumptions of input without error checking
    # Implementation will be dependant on input type
    def structure_mutation(self):
        pass

    # Mutates a field specified with index
    def random_mutation(self):
        for i in range(len(self._input)):
            self._input[i] = mutate(self._input[i])

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
    def __init__(self, inputFile):
        super().__init__(inputFile)
        self.file = inputFile
        self._read_as_str(inputFile)
        self._csv_as_array(inputFile)

    def _csv_as_array(self, fileName):
        self.original_cells = []
        self.original_cols = []
        try:
            with open(fileName, 'r') as f:
                csv_reader = csv.reader(f, delimiter=',')
                for row in csv_reader:
                    self.original_cols.append(len(row))
                    for cell in row:
                        try:
                            self.original_cells.append(int(cell))
                        except:
                            self.original_cells.append(cell)
        except:
            print(f"Failed to read csv from file: {fileName}")
            exit(1)

    def _csv_from_array(self):
        curr = 0
        i = 0
        string = ""
        for j in range(0, len(self._input)):
            if type(self._input[j]) == int:
                self._input[j] = str(self._input[j])
        while (curr < len(self._input)):
            cols = self.cols[i]
            string += ','.join(self._input[curr:curr+cols]) + "\n"
            curr += cols
        return string

    def copy(self):
        self._input = []
        self.cols = []
        for cell in self.original_cells:
            self._input.append(cell)
        for col in self.original_cols:
            self.cols.append(col)

    def fuzz(self):
        # mutated_csv = parseCSV(self.file)
        self.copy()
        state = self.dictionary_attack()
        if (state):
            self.random_mutation()

        # mutated_string
        return self._csv_from_array()

class jsonFuzzer(Fuzzer):
    def __init__(self, inputFile):
        super().__init__(inputFile)
        self.file = inputFile
        self._read_as_str(inputFile)
        self._json_as_array()
        self.array_copy()
        print(self._json_from_array())


    def _json_as_array(self):
        obj = json.loads(self._str)
        self.original_formatter, self.original_values = self._obj_as_array(obj)

        print(self.original_formatter)
        print(self.original_values)

    def _obj_as_array(self, obj):
        formatter = []
        values = []
        obj_type = type(obj)
        if (obj_type ==dict):
            formatter.append("dict_start")
            for key in obj.keys():
                f, v = self._obj_as_array(key)
                formatter += f
                values += v
                f, v = self._obj_as_array(obj[key])
                formatter += f
                values += v
            formatter.append("dict_end")

        elif (obj_type == list):
            formatter.append("list_start")
            for item in obj:
                f, v = self._obj_as_array(item)
                formatter += f
                values += v
            formatter.append("list_end")


        elif (obj_type == str):
            formatter.append(str)
            values.append(str(obj))

        elif (obj_type == int):
            formatter.append(int)
            values.append(int(obj))

        else:
            print("Unkown data type")
            exit(2)

        return (formatter, values)

    def _json_from_array(self):
        o, f, v = self._obj_from_array(self.formatter, self._input)
        return json.dumps(o)

    def _obj_from_array(self, formatter, values):
        format_index = 0
        value_index = 0
        obj = None
        if (formatter[format_index] == "dict_start"):
            obj = dict()
            format_index += 1
            while (not formatter[format_index] == "dict_end"):
                key, f_i, v_i = self._obj_from_array(formatter[format_index:], values[value_index:])
                format_index += f_i
                value_index += v_i
                value, f_i, v_i = self._obj_from_array(formatter[format_index:], values[value_index:])
                format_index += f_i
                value_index += v_i
                obj[key] = value
            format_index += 1
            

        elif (formatter[format_index] == "list_start"):
            obj = list()
            format_index += 1
            while (not formatter[format_index] == "list_end"):
                value, f_i, v_i = self._obj_from_array(formatter[format_index:], values[value_index:])
                format_index += f_i
                value_index += v_i
                obj.append(value)
            format_index += 1

        elif (formatter[format_index] == str):
            obj = str(values[value_index])
            format_index += 1
            value_index += 1
        elif (formatter[format_index] == int):
            obj = int(values[value_index])
            format_index += 1
            value_index += 1
        else:
            print("Unknown data type specified")
            exit(3)
        return (obj, format_index, value_index)

    def array_copy(self):
        self.formatter = []
        self._input = []
        for item in self.original_formatter:
            self.formatter.append(item)
        for item in self.original_values:
            self._input.append(item)



    def fuzz(self):
        self.array_copy()
        state = self.dictionary_attack()
        print(state)
        if (state):
            self.random_mutation()
        mutated_string = self._json_from_array()
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

    num_of_iteration = 1000
    # here is just a basic judgement
    if is_JSON("./" + source_input):
        print("JSON")
        json_fuzzer = jsonFuzzer("./" + source_input)
        for i in range(num_of_iteration):
            print(f"{i+1}th time: ", end=' ')
            result = json_fuzzer.run(runner)[0]
            if result.returncode < 0:
                print(result.returncode)
                print("**", result.stdout)
                exit(0)
    else:
        csv_fuzzer = csvFuzzer("./" + source_input)
        for i in range(num_of_iteration):
            print(f"{i+1}th time: ", end=' ')
            result = csv_fuzzer.run(runner)[0]
            if result.returncode < 0:
                print(result.returncode)
                print("**", result.stdout)
                exit(0)
    if False:
        print("input file error")
        sys.exit()
