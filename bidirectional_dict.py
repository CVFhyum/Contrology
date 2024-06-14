class BidirectionalDict:
    def __init__(self):
        self.dictionary = {}

    def __setitem__(self, key, value):
        if key in self.dictionary or value in self.dictionary.values():
            raise ValueError("Key or value already exists in BidirectionalDict")
        self.dictionary[key] = value
        self.dictionary[value] = key

    def __getitem__(self, key_or_value):
        return self.dictionary[key_or_value]

    def get_key(self, value):
        return self.dictionary[value]

    def get_value(self, key):
        return self.dictionary[key]

    def __delitem__(self, key):
        value = self.dictionary[key]
        del self.dictionary[value]
        del self.dictionary[key]

    def __contains__(self, item):
        return item in self.dictionary

    def __len__(self):
        return len(self.dictionary) // 2

    def __repr__(self):
        return f"BidirectionalDict({self.dictionary})"
