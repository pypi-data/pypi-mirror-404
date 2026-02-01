#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
========================================================================
Command line interface
========================================================================
'''

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Help message for input")
    args = parser.parse_args()
    print(args.input)
    ## ... this is a dummy CLI for now
    ## call from cmd line with e.g. >$ turbx 'hello'
