from fastapi import FastAPI
from pydantic import BaseModel
from app.grammar import Grammar
from app.first_follow import FirstFollow
from app.lr0 import LR0

app = FastAPI()

class GrammarInput(BaseModel):
    grammar: str


@app.get("/")
def root():
    return {"message": "Compiler Parser Backend Running"}


@app.post("/first-follow")
def compute_sets(data: GrammarInput):
    g = Grammar(data.grammar)
    g.augment_grammar()

    ff = FirstFollow(g)
    first = ff.compute_first()
    follow = ff.compute_follow()

    return {
        "first": {k: list(v) for k, v in first.items()},
        "follow": {k: list(v) for k, v in follow.items()}
    }
@app.post("/test-closure")
def test_closure(data: GrammarInput):
    g = Grammar(data.grammar)
    g.augment_grammar()

    lr = LR0(g)

    start_prod = g.productions[g.start_symbol][0]
    start_item = lr.create_item(g.start_symbol, start_prod, 0)

    closure = lr.closure({start_item})

    return {
        "closure": [
            {
                "left": item[0],
                "right": list(item[1]),
                "dot": item[2]
            }
            for item in closure
        ]
    }

@app.post("/lr0-states")
def generate_lr0(data: GrammarInput):
    g = Grammar(data.grammar)
    g.augment_grammar()

    lr = LR0(g)
    states = lr.build_canonical_collection()

    result = []

    for idx, state in enumerate(states):
        items = []
        for (left, right, dot) in state:
            items.append({
                "left": left,
                "right": list(right),
                "dot": dot
            })

        result.append({
            "state": idx,
            "items": items
        })

    return {
        "total_states": len(states),
        "states": result
    }

@app.post("/lr0-table")
def generate_lr0_table(data: GrammarInput):
    g = Grammar(data.grammar)
    g.augment_grammar()

    lr = LR0(g)
    lr.build_canonical_collection()
    action, goto_table, conflicts = lr.build_parsing_table()

    return {
        "action": action,
        "goto": goto_table,
        "conflicts": conflicts
    }
class ParseInput(BaseModel):
    grammar: str
    input_string: str


@app.post("/lr0-parse")
def parse_lr0(data: ParseInput):
    g = Grammar(data.grammar)
    g.augment_grammar()

    lr = LR0(g)
    lr.build_canonical_collection()
    action, goto_table, conflicts = lr.build_parsing_table()

    if conflicts:
        return {
            "error": "Grammar is not LR(0)",
            "conflicts": conflicts
        }

    result = lr.parse_string(action, goto_table, data.input_string)

    return result
@app.post("/lr0-parse")
def parse_lr0(data: ParseInput):
    g = Grammar(data.grammar)
    g.augment_grammar()

    lr = LR0(g)
    lr.build_canonical_collection()
    action, goto_table, conflicts = lr.build_parsing_table()

    if conflicts:
        return {
            "error": "Grammar is not LR(0)",
            "conflicts": conflicts
        }

    result = lr.parse_string(action, goto_table, data.input_string)
    return result