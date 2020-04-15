from collections import OrderedDict
import yaml

# Credit to: mayou36/python-yamlordereddictloader

def represent_ordereddict(self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items())

class OrderedDictDumper(yaml.CDumper):
    def __init__(self, *args, **kwargs):
        yaml.CDumper.__init__(self, *args, **kwargs)
        self.add_representer(OrderedDict, type(self).represent_ordereddict)

    represent_ordereddict = represent_ordereddict
