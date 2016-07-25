import sys
from jsonschema import validate
import json

<<<<<<< HEAD
=======

>>>>>>> abbottLane-substance_detection
def load_json(filepath):
    with open(filepath) as data_file:
        data = json.load(data_file)
        return data

<<<<<<< HEAD
=======

>>>>>>> abbottLane-substance_detection
def main(args):
    # only let the script run if there are 2 arguments + the .py script arg
    #  or
    # 0 arguments, in which case default values will be attempted
<<<<<<< HEAD
    if len(args) != 3 and len(args)!= 1:
=======
    if len(args) != 3 and len(args) != 1:
>>>>>>> abbottLane-substance_detection
        print("Invalid number of arguments: " + str(len(args)))
        return 1

    # default pointers
    schema_dir = "../schema.json"
    sysout_dir = "../transfer2.nlp.json"

    # if arguments provided, change default pointers
    if len(args) == 3:
        schema_dir = args[1]
        sysout_dir = args[2]

    # load the json files
    schema = load_json(schema_dir)
    sys_out = load_json(sysout_dir)

    # validate and print results: no error means the validation succeeded
    print(validate(sys_out, schema))

<<<<<<< HEAD
=======

>>>>>>> abbottLane-substance_detection
if __name__ == '__main__':
    main(sys.argv)