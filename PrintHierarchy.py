#!/usr/local/bin python3
## ---------------------------
## Script name: PrintHierarchy.py
## Purpose: Input file paths and print out file heirarchy tree
## Author: Jonathan Serrano
## Copyright (c) Jonathan Serrano, 2023
## ---------------------------

import sys

def add_to_tree(tree, path):
    if len(path) == 1:
        tree[path[0]] = {}
    else:
        if path[0] not in tree:
            tree[path[0]] = {}
        add_to_tree(tree[path[0]], path[1:])

def print_tree(tree, level=0):
    for k, v in tree.items():
        print("  " * level + k)
        if isinstance(v, dict):
            print_tree(v, level + 1)

def main(input_paths):
    tree = {}

    for path in input_paths:
        add_to_tree(tree, path.split("/"))

    print_tree(tree)

if __name__ == "__main__":
    # Extract input paths from command line arguments
    input_paths = sys.argv[1:]

    # Call the main function with the input paths
    main(input_paths)
