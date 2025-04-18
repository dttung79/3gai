# Utility functions for the intro_gemini package
# read keys.txt to get the key
def get_key(model='gemini'):
    with open('keys.txt') as f:
        key = f.readline().strip().split(':')[-1] # keyname:key
    return key