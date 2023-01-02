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
    def __init__(self, name):
        self.name = name

    '''def __init__(self, name, blocks):
            self.name = name
            self.blocks = blocks '''

    def addBlock(self, name, text):
        if(name in self.block_names):
            print('topic exists')
            return
        self.blocks.append(Block(name, text, self))
        self.block_names.add(name)
    
    def printDetails(self):
        for name in self.block_names:
            print(name)

    def __str__(self):
        return f"{self.name} has {len(self.block_names)} blocks"
        

p1 = Page('p1')
p1.addBlock('b1', 'lorem ipsum')
p1.addBlock('b2', 'b one lorem')
p1.addBlock('b3', 'b1 b2 b4')
print(p1.blocks[2])
