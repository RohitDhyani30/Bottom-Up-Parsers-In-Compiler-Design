from collections import defaultdict
from .clr1 import CLR1


class LALR1:
    def __init__(self, grammar, first_follow):
        self.grammar = grammar
        self.ff = first_follow
        self.states = []
        self.merged_states = []
        self.transitions = {}

    # ---------------- CORE (LR0 PART) ---------------- #
    def get_core(self, state):
        return frozenset((l, r, d) for (l, r, d, la) in state)

    # ---------------- BUILD FROM CLR ---------------- #
    def build_from_clr(self):
        clr = CLR1(self.grammar, self.ff)
        clr.build_canonical_collection()

        core_map = {}
        merged = []

        # group states by LR0 core
        for state in clr.states:
            core = self.get_core(state)

            if core not in core_map:
                core_map[core] = []
            core_map[core].append(state)

        # merge states
        for core, group in core_map.items():
            merged_state = {}

            for state in group:
                for (l, r, d, la) in state:
                    key = (l, r, d)
                    if key not in merged_state:
                        merged_state[key] = set()
                    merged_state[key].add(la)

            final_items = set()
            for (l, r, d), las in merged_state.items():
                for la in las:
                    final_items.add((l, r, d, la))

            merged.append(final_items)

        self.merged_states = merged

        # rebuild transitions
        self.build_transitions(clr)

    # ---------------- TRANSITIONS ---------------- #
    def build_transitions(self, clr):
        core_to_index = {}

        for i, state in enumerate(self.merged_states):
            core = self.get_core(state)
            core_to_index[core] = i

        symbols = list(self.grammar.non_terminals | self.grammar.terminals)

        for i, state in enumerate(self.merged_states):
            self.transitions[i] = {}

            for sym in symbols:
                moved = set()

                for (l, r, d, la) in state:
                    if d < len(r) and r[d] == sym:
                        moved.add((l, r, d + 1))

                if not moved:
                    continue

                target_core = frozenset(moved)

                if target_core in core_to_index:
                    self.transitions[i][sym] = core_to_index[target_core]

    # ---------------- PROD INDEX ---------------- #
    def find_production_index(self, left, right):
        for i, (l, r) in enumerate(self.grammar.production_list):
            if l == left and r == list(right):
                return i
        return None

    # ---------------- TABLE ---------------- #
    def build_parsing_table(self):
        action = {}
        goto_table = {}
        conflicts = []

        for i, state in enumerate(self.merged_states):
            action[i] = {}
            goto_table[i] = {}

            for (l, r, d, la) in state:

                # SHIFT
                if d < len(r):
                    sym = r[d]

                    if sym in self.transitions[i]:
                        j = self.transitions[i][sym]

                        if sym in self.grammar.terminals:
                            if sym in action[i] and action[i][sym] != f"s{j}":
                                conflicts.append((i, sym))
                            action[i][sym] = f"s{j}"
                        else:
                            goto_table[i][sym] = j

                # REDUCE / ACCEPT
                else:
                    if l == self.grammar.start_symbol:
                        action[i]['$'] = "acc"
                    else:
                        prod_index = self.find_production_index(l, r)

                        if prod_index is None:
                            continue

                        if la in action[i] and action[i][la] != f"r{prod_index}":
                            conflicts.append((i, la))

                        action[i][la] = f"r{prod_index}"

        return action, goto_table, conflicts