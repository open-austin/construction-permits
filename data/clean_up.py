import os

for root, dirs, files in os.walk("."):
    for name in files:
        if "new_" in name:
            current_file = os.path.join(root, name)
            new_file = os.path.join(root, name[4:])
            os.replace(current_file, new_file)
