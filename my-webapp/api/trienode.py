class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_phrase = False
        
class Trie:
    def __init__(self):
        self.root = TrieNode()
        
    def insert(self, phrase):
        node = self.root
        for char in phrase:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_phrase = True
        
    def search(self, text):
        node = self.root
        for i, char in enumerate(text):
            if char in node.children:
                node = node.children[char]
                if node.is_phrase:
                    return text[:i+1]
            else:
                break
        return ""