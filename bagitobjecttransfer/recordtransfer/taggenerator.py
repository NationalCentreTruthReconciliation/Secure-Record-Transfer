from collections import OrderedDict

from recordtransfer.objectfromform import ObjectFromForm

class BagitTags(ObjectFromForm):
    def __init__(self, form_data: dict):
        super().__init__(form_data)
        self.tags = OrderedDict()

    def _post_generation(self):
        self.object = self.tags

    def _new_item(self, title, data, **kwargs):
        is_array_item = kwargs.get('is_array_item') if 'is_array_item' in kwargs else False
        index1 = kwargs.get('index1') if 'index1' in kwargs else -1

        key = f'{title}_{index1}' if is_array_item else title
        value = data

        self.tags[key] = value

