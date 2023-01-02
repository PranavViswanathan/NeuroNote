import nltk
import re
from nltk.tokenize import sent_tokenize, word_tokenize

class Block:
    '''def create_links(self, text, page):
        tokens = nltk.word_tokenize(text)
        pos_tags = nltk.pos_tag(tokens)
        linked_text = []
        for token, pos in pos_tags:
            if pos == "NN" or pos == "NNP":
                if token in page.block_names:
                    # If so, create a link to the topic's page or block
                    linked_text.append(token)
        return linked_text'''

    def match_phrases(self, text, page):
        pattern = '|'.join(page.block_names)
        matches = re.findall(pattern, text)
        return matches

    def __init__(self, name, text, page):
        self.name = name
        self.text = text
        self.links = self.match_phrases(self.text, page)
        
    def __str__(self):
        return f"{self.name}, {self.text}, {self.links}"
        

class Page:
    blocks = []
    block_names = set()
    block_map = {} # dict to store block name-to-object mappings


    def __init__(self, name):
        self.name = name

    '''def __init__(self, name, blocks):
            self.name = name
            self.blocks = blocks '''

    def addBlock(self, name, text):
        if(name in self.block_names):
            print('topic exists')
            return
        new_block = Block(name, text, self)
        self.blocks.append(new_block)
        self.block_names.add(name)
        self.block_map[name] = new_block  # Add entry to block map
        
        '''self.blocks.append(Block(name, text, self))
        self.block_names.add(name)'''
        
    
    def printDetails(self):
        for name in self.block_names:
            print(name)

    def __str__(self):
        return f"{self.name} has {len(self.block_names)} blocks"
        
# Display the text for a given block
def display_block(block_name, page):
    if block_name in page.block_map:
        block = page.block_map[block_name] # Look up the block object in the block map
        print("Here's the block text")
        print(block.text) # Display the block's text
    else:
        print(f"Error: block '{block_name}' does not exist on page '{page.name}'")

# Scroll to the next block
def scroll_next(current_block_name, page):
  current_block = page.block_map[current_block_name] # Look up the current block object in the block map
  current_index = page.blocks.index(current_block) # Find the index of the current block in the page's block list
  # If the current block is not the last block on the page,
  # display the text for the next block
  if current_index < len(page.blocks) - 1:
    next_block = page.blocks[current_index + 1]
    display_block(next_block.name, page)
  else:
    print("You are already at the last block on this page.")

# Scroll to the previous block
def scroll_prev(current_block_name, page):
  current_block = page.block_map[current_block_name] # Look up the current block object in the block map
  current_index = page.blocks.index(current_block) # Find the index of the current block in the page's block list
  # If the current block is not the first block on the page,
  # display the text for the previous block
  if current_index > 0:
    prev_block = page.blocks[current_index - 1]
    display_block(prev_block.name, page)
  else:
    print("You are already at the first block on this page.")

p1 = Page('p1')
p1.addBlock('b1', 'lorem ipsum')
p1.addBlock('b2', 'b lorem')
p1.addBlock('b3', 'b1 b2')
print(p1.blocks[2])

display_block('b3',p1)
scroll_next('b1', p1)  # Scrolls to the next block on page 'p1' starting from block 'b3'
scroll_prev('b2', p1)  # Scrolls to the previous block on page 'p1' starting from block 'b2'