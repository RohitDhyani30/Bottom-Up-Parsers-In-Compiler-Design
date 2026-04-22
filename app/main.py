from fastapi import FastAPI
from pydantic import BaseModel
from .grammar import Grammar
from .first_follow.first_follow import FirstFollow
from .lr0 import LR0
from .slr1 import SLR1
from .clr1 import CLR1
from .lalr1 import LALR1
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GrammarInput(BaseModel):
    grammar: str

class ParseInput(BaseModel):
    grammar: str
    input_string: str


# 🔥 COMMON VALIDATION FUNCTION
def validate_and_continue(grammar_text):
    g = Grammar(grammar_text)
    errors, warnings = g.validate_cfg()

    if errors:
        return None, {
            "valid": False,
            "errors": errors,
            "warnings": warnings
        }

    return g, None


@app.get("/")
def root():
    return {"message": "Compiler Parser Backend Running"}


@app.post("/validate-grammar")
def validate_grammar(data: GrammarInput):
    g = Grammar(data.grammar)
    errors, warnings = g.validate_cfg()

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


# ---------------- FIRST/FOLLOW ---------------- #
@app.post("/first-follow")
def compute_sets(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    ff = FirstFollow(g)
    return {
        "first": {k: list(v) for k, v in ff.compute_first().items()},
        "follow": {k: list(v) for k, v in ff.compute_follow().items()}
    }


# ---------------- LR(0) ---------------- #
@app.post("/lr0-states")
def lr0_states(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()
    lr = LR0(g)
    states = lr.build_canonical_collection()

    result = []
    for i, state in enumerate(states):
        items = [{"left": l, "right": list(r), "dot": d} for (l, r, d) in state]
        result.append({"state": i, "items": items})

    return {"states": result}


@app.post("/lr0-table")
def lr0_table(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()
    lr = LR0(g)
    lr.build_canonical_collection()

    action, goto, conflicts = lr.build_parsing_table()
    return {"action": action, "goto": goto, "conflicts": conflicts}


@app.post("/lr0-parse")
def lr0_parse(data: ParseInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()
    lr = LR0(g)
    lr.build_canonical_collection()

    action, goto, conflicts = lr.build_parsing_table()

    if conflicts:
        return {"error": "Grammar is not LR(0)", "conflicts": conflicts}

    return lr.parse_string(action, goto, data.input_string)


# ---------------- SLR(1) ---------------- #
@app.post("/slr1-states")
def slr1_states(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()
    slr = SLR1(g)
    slr.build_canonical_collection()

    result = []
    for i, state in enumerate(slr.states):
        items = [{"left": l, "right": list(r), "dot": d} for (l, r, d) in state]
        result.append({"state": i, "items": items})

    return {"states": result}


@app.post("/slr1-table")
def slr1_table(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()
    ff = FirstFollow(g)
    ff.compute_first()

    slr = SLR1(g)
    slr.build_canonical_collection()

    action, goto, conflicts = slr.build_parsing_table_slr(ff)
    return {"action": action, "goto": goto, "conflicts": conflicts}


@app.post("/slr1-parse")
def slr1_parse(data: ParseInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()
    ff = FirstFollow(g)
    ff.compute_first()

    slr = SLR1(g)
    slr.build_canonical_collection()

    action, goto, conflicts = slr.build_parsing_table_slr(ff)

    if conflicts:
        return {"error": "Grammar is not SLR(1)", "conflicts": conflicts}

    return slr.parse_string(action, goto, data.input_string)


# ---------------- CLR(1) ---------------- #
@app.post("/clr1-states")
def clr1_states(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()

    ff = FirstFollow(g)
    ff.compute_first()

    clr = CLR1(g, ff)
    clr.build_canonical_collection()

    states = [
        {
            "state": i,
            "items": [
                {
                    "left": l,
                    "right": list(r),
                    "dot": d,
                    "lookahead": la
                }
                for (l, r, d, la) in state
            ]
        }
        for i, state in enumerate(clr.states)
    ]

    return {"states": states}

@app.post("/clr1-table")
def clr1_table(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()

    ff = FirstFollow(g)
    ff.compute_first()

    clr = CLR1(g, ff)
    clr.build_canonical_collection()

    action, goto, conflicts = clr.build_parsing_table()

    return {
        "action": action,
        "goto": goto,
        "conflicts": conflicts
    }
    

@app.post("/clr1-parse")
def clr1_parse(data: ParseInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()

    ff = FirstFollow(g)
    ff.compute_first()

    clr = CLR1(g, ff)
    clr.build_canonical_collection()

    action, goto, conflicts = clr.build_parsing_table()

    if conflicts:
        return {"error": "Grammar is not CLR(1)", "conflicts": conflicts}

    return clr.parse_string(action, goto, data.input_string)


# ---------------- LALR(1) ---------------- #
@app.post("/lalr1-states")
def lalr1_states(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()

    ff = FirstFollow(g)
    ff.compute_first()

    lalr = LALR1(g, ff)
    lalr.build_from_clr()

    result = []
    for i, state in enumerate(lalr.merged_states):
        items = [
            {
                "left": l,
                "right": list(r),
                "dot": d,
                "lookahead": la
            }
            for (l, r, d, la) in state
        ]
        result.append({"state": i, "items": items})

    return {"states": result}

@app.post("/lalr1-table")
def lalr1_table(data: GrammarInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()

    ff = FirstFollow(g)
    ff.compute_first()

    lalr = LALR1(g, ff)
    lalr.build_from_clr()

    action, goto, conflicts = lalr.build_parsing_table()

    return {
        "action": action,
        "goto": goto,
        "conflicts": conflicts
    }

@app.post("/lalr1-parse")
def lalr1_parse(data: ParseInput):
    g, err = validate_and_continue(data.grammar)
    if err: return err

    g.augment_grammar()

    ff = FirstFollow(g)
    ff.compute_first()

    lalr = LALR1(g, ff)
    lalr.build_from_clr()

    action, goto, conflicts = lalr.build_parsing_table()

    if conflicts:
        return {"error": "Grammar is not LALR(1)", "conflicts": conflicts}

    return lalr.parse_string(action, goto, data.input_string)