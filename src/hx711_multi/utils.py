#!/usr/bin/env python3
"""
This file holds general utilities used elsewhere in the code
"""


def convert_to_list(input, _type=int, _default_output=None):
    """
    Converts the input to a list if not already.
    Also performs checks for type of list items and will set output to the default value if type criteria isn't met

    Args:
        input: input that you are analyzing to convert to list of type
        type (optional): type of items in list to confirm. Defaults to int. A value of None for this input result in no type checking
        default_val (optional): value to pass if no other criteria is used. Defaults to None.
    """
    output = _default_output
    if type(input) is list:
        if _type is not None:
            if all([(type(x) is _type) for x in input]):
                # set to output if is list and all instances match type
                output = input
        else:
            # set to output if is list (no type specified)
            output = input
    elif ((type(input) is _type) and (_type is not None)) or ((input is not None) and (_type is None)):
        # set to output as a single element list if is type match, or no type was specified and input is not None
        output = [input]
    return output
