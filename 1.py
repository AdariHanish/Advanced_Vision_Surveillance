import os

def print_tree(start_path, prefix=""):
    items = sorted(os.listdir(start_path))

    for index, item in enumerate(items):
        path = os.path.join(start_path, item)

        connector = "└── " if index == len(items) - 1 else "├── "
        print(prefix + connector + item)

        if os.path.isdir(path):
            extension = "    " if index == len(items) - 1 else "│   "
            print_tree(path, prefix + extension)

# ===============================
# CHANGE THIS TO YOUR PROJECT PATH
# ===============================

project_path = r"C:\Users\honey\Desktop\Advanced_Vision_Surveillance"

print("\n📁 PROJECT STRUCTURE:\n")
print_tree(project_path)