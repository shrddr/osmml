import math

def mil(fp):
    return math.floor(fp*1000000)

class Lookup:
    def __init__(self, data):
        self.data = data
        self.dict = None
        
    def contains(self, needle):
        if self.dict is None:
            d = {}
            for p in self.data:
                if p[0] in d:
                    d[p[0]].append(p[1])
                else:
                    d[p[0]] = [p[1]]
            for k in d:
                d[k] = set(d[k])
            self.dict = d

        if needle[0] in self.dict:
            if needle[1] in self.dict[needle[0]]:
                return True
        return False


if __name__ == "__main__":
    points = [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4), ]
    haystack = Lookup(points)
    needle = (1,2)
    print(haystack.contains(needle))