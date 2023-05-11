#!/usr/local/bin python3
## ---------------------------
## Script name: PrintHierarchy.py
## Purpose: Input file paths and print out file heirarchy tree
## Author: Jonathan Serrano
## Copyright (c) Jonathan Serrano, 2023
## ---------------------------

import sys
import os

def add_to_tree(tree, path):
    if len(path) == 1:
        tree[path[0]] = {}
    else:
        add_to_tree(tree.setdefault(path[0], {}), path[1:])

def print_tree(tree, level=0, is_last=False, output_file=None):
    prefix = "|   " * (level - 1) + "|-- " if level > 0 else ""
    for i, (k, v) in enumerate(tree.items()):
        is_last = i == len(tree) - 1
        line = f"{prefix}{k}\n"
        output_file.write(line)
        print(line, end="")
        if isinstance(v, dict):
            print_tree(v, level + 1, is_last, output_file)

def main(input_paths):
    tree = {}

    for path in input_paths:
        if os.path.exists(path):
            add_to_tree(tree, path.split("/"))
        else:
            print(f"Warning: File or directory '{path}' does not exist.")

    home_dir = os.path.expanduser("~")
    output_file_path = os.path.join(home_dir, "tree_output.txt")

    with open(output_file_path, "w") as output_file:
        print_tree(tree, output_file=output_file)

    print(f"Tree output saved to: {output_file_path}")

def test():
    home_dir = os.path.expanduser("~")
    home_tree = {"~": {}}
    for root, dirs, files in os.walk(home_dir):
        curr_dir = root.replace(home_dir, "~")
        parent_dir = os.path.dirname(curr_dir)
        add_to_tree(home_tree.setdefault(parent_dir, {}), [os.path.basename(curr_dir)])
        for file in files:
            add_to_tree(home_tree.setdefault(curr_dir, {}), [file])
    
    print("Home Folder Hierarchy:")
    print_tree(home_tree)

if __name__ == "__main__":
    input_paths = sys.argv[1:]
    main(input_paths)

    # Uncomment the line below to enable the test
    # test()
