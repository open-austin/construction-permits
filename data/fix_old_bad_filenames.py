import os

for root, dirs, files in os.walk('.'):
    for name in files:
        if ('.csv' in name):
            if len(name) == 12:
                current_file = os.path.join(root, name)
                print(current_file)
                
                month = name[0:2]
                day = name[3:5]
                year = "20" + name[6:8]
                
                new_file = os.path.join(root, year + "-" + month + "-" + day + ".csv")
                os.rename(current_file, new_file)
