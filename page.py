import nltk
nltk.download()
from nltk.tokenize import sent_tokenize, word_tokenize

class Block:
    def create_links(self, text, page):
        tokens = nltk.word_tokenize(text)
        pos_tags = nltk.pos_tag(tokens)
        linked_text = []
        for token, pos in pos_tags:
            if pos == "NN" or pos == "NNP":
                if token in page.block_names:
                    # If so, create a link to the topic's page or block
                    linked_text.append(token)
        return linked_text


    def __init__(self, name, text, page):
        self.name = name
        self.text = text
        self.links = self.create_links(self.text, page)

    
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
p1.addBlock('b one', 'lorem ipsum')
p1.addBlock('b two', 'b1 lorem')
print(p1.blocks[1])
        