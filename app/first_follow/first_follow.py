# app/first_follow.py

class FirstFollow:
    def __init__(self, grammar):
        self.grammar = grammar
        self.first = {nt: set() for nt in grammar.non_terminals}
        self.follow = {nt: set() for nt in grammar.non_terminals}

    # ---------------- FIRST ---------------- #

    def compute_first(self):
        changed = True

        while changed:
            changed = False

            for left in self.grammar.productions:
                for production in self.grammar.productions[left]:

                    for symbol in production:
                        # If terminal → add and stop
                        if symbol in self.grammar.terminals:
                            if symbol not in self.first[left]:
                                self.first[left].add(symbol)
                                changed = True
                            break

                        # If non-terminal → add FIRST(symbol)
                        else:
                            before = len(self.first[left])
                            self.first[left].update(self.first[symbol])
                            if len(self.first[left]) > before:
                                changed = True
                            break

        return self.first

    # ---------------- FOLLOW ---------------- #

    def compute_follow(self):
        # Add $ to start symbol
        self.follow[self.grammar.start_symbol].add('$')

        changed = True

        while changed:
            changed = False

            for left in self.grammar.productions:
                for production in self.grammar.productions[left]:

                    for i in range(len(production)):
                        symbol = production[i]

                        if symbol in self.grammar.non_terminals:

                            # Case 1: Symbol followed by something
                            if i + 1 < len(production):
                                next_symbol = production[i + 1]

                                if next_symbol in self.grammar.terminals:
                                    if next_symbol not in self.follow[symbol]:
                                        self.follow[symbol].add(next_symbol)
                                        changed = True
                                else:
                                    before = len(self.follow[symbol])
                                    self.follow[symbol].update(self.first[next_symbol])
                                    if len(self.follow[symbol]) > before:
                                        changed = True

                            # Case 2: Symbol at end
                            else:
                                before = len(self.follow[symbol])
                                self.follow[symbol].update(self.follow[left])
                                if len(self.follow[symbol]) > before:
                                    changed = True

        return self.follow