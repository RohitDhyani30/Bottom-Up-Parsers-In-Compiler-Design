# app/grammar.py

class Grammar:
    def __init__(self, grammar_text: str):
        self.productions = {}          # {NonTerminal: [[symbols], ...]}
        self.production_list = []      # [(left, [symbols]), ...]
        self.non_terminals = set()
        self.terminals = set()
        self.start_symbol = None

        self._parse_grammar(grammar_text)
        self._extract_terminals()
        self._build_production_list()

    def _parse_grammar(self, grammar_text: str):
        lines = [
            line.strip()
            for line in grammar_text.strip().split("\n")
            if line.strip()
        ]

        # Collect non-terminals first
        for line in lines:
            if "->" not in line:
                raise ValueError(f"Invalid production format: {line}")
            left, _ = line.split("->", 1)
            self.non_terminals.add(left.strip())

        # Parse productions
        for index, line in enumerate(lines):
            left, right = line.split("->", 1)
            left = left.strip()

            if index == 0:
                self.start_symbol = left

            alternatives = right.split("|")
            self.productions[left] = []

            for alt in alternatives:
                symbols = alt.strip().split()
                self.productions[left].append(symbols)

    def _extract_terminals(self):
        for left in self.productions:
            for production in self.productions[left]:
                for symbol in production:
                    if symbol not in self.non_terminals:
                        self.terminals.add(symbol)

    def _build_production_list(self):
        for left in self.productions:
            for prod in self.productions[left]:
                self.production_list.append((left, prod))

    def augment_grammar(self):
        augmented_start = self.start_symbol + "'"
        self.productions[augmented_start] = [[self.start_symbol]]
        self.non_terminals.add(augmented_start)
        self.start_symbol = augmented_start

        # rebuild production list after augmentation
        self.production_list = []
        self._build_production_list()