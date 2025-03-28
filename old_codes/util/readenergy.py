import os

def readenergy(filename):
    # Read the last eneryg in the (OSZICAR) output data file
    with open(filename, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()
        E_string = last_line.split()[4]
    return float(E_string)

def readfirstenergy(filename):
    # Only read the first energy in the (OSZICAR) output data file
    with open(filename, 'r') as f:
        for line in f:
            list_string = line.split()
            if len(list_string)==10:
                if list_string[1]=="F=":
                    return float(list_string[4])
    return "Error reading energy!"

#print(readtime("test.txt"))
#print(readfirstenergy("testfiles/OSZICAR271"))
