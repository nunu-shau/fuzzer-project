#! /usr/bin/env python3

#originally named 'Fuzzer_bitflip_shau.py'

from pwn import *
import subprocess
import json
import random

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
      print(f"Trying {mutated}")
      result = runner.run(mutated)[0]

      if result.returncode < 0:
        with open("bad.txt", 'a') as f:  
          f.write(mutated)
          f.write("\n")
      return runner.run(mutated)

       
class csvFuzzer(Fuzzer):
    def __init__():
      
      pass

    def fuzz(self):
      
      pass


class jsonFuzzer(Fuzzer):
    def __init__(self, sample_input):
      self.file = sample_input

    def fuzz(self):
      # read source file & extract fields  (alternative way: string = open(self.file, 'r').read())
      with open(self.file, "r") as f:
        json_data = json.load(f)
      string = json.dumps(json_data)

      # mutate field names and field values
      percent_of_flip = random.uniform(0, 0.2)  # adjust the percent of flipping characters here.
      mutated_string = bit_flip(string, percent_of_flip)

      # return mutated input
      print(f"Trying {mutated_string}")   #!!!!!!
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
  # print(runner.run(inl)[0].stdout)
  

  # here is just a basic judgement
  if "csv" in source_input:
    # csv_fuzzer = csvFuzzer()
    pass
  elif "json" in source_input:
    num_of_iteration  = 1000
    for i in range(num_of_iteration):
      print(f"{i+1}th time: ", end=' ')
      json_fuzzer = jsonFuzzer("./" + source_input)
      print(json_fuzzer.run(runner)[0].returncode)
  else:
    print("input file error")
    sys.exit()



