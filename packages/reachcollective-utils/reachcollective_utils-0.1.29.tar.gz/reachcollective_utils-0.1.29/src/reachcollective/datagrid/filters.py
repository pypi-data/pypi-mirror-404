class Filters:
    def __init__(self, qp=None):
        self.qp = qp
        self.init = {}
        self.equals = {}
        self.personalize = []
        self.customize = {}

    def process(self):
        for k, v in self.qp.items():
            if k.find('filter') >= 0:
                attr = k[k.find('[') + 1 : k.find(']')]
                t = self.process_value(attr, v)
                if attr in self.personalize:
                    self.customize = {**self.customize, **t}
                else:
                    self.equals = {**self.equals, **t}

    def get(self):
        r = {'init': self.init, 'equals': self.equals, 'customize': self.customize}
        return r

    @staticmethod
    def process_value(attr, value):
        parts = value.split('|')
        if len(parts) > 1:
            value = parts

        return {attr: value}
