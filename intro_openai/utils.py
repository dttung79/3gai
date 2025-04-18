# Utility functions for the intro_gemini package
# read keys.txt to get the key
def get_key():
    with open('keys.txt') as f:
        key = f.readline().strip().split(':')[-1] # keyname:key
    return key

def print_message_content(content):
    full_response = []
    for content_block in content:
        # Handle content with type attribute and text.value structure
        if hasattr(content_block, 'type') and content_block.type == 'text':
            if hasattr(content_block, 'text') and hasattr(content_block.text, 'value'):
                full_response.append(content_block.text.value)
        # Handle content with direct text attribute that has value
        elif hasattr(content_block, 'text') and hasattr(content_block.text, 'value'):
            full_response.append(content_block.text.value)
        # Handle string content
        elif isinstance(content_block, str):
            full_response.append(content_block)
    
    print('[AI]:', ' '.join(full_response))