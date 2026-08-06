"""Luau syntax highlighter.

Build-time tokenizer -- no client-side highlighting library, so code is coloured
before it ever reaches the browser and there is no flash of unstyled code.

Pure stdlib. Handles the Luau subset that actually shows up in guides: comments
(line and block), strings (quoted, long-bracket, with escapes), numbers, keywords,
Roblox globals, method calls and punctuation.
"""

import html
import re

KEYWORDS = {
    "and", "break", "continue", "do", "else", "elseif", "end", "export", "false",
    "for", "function", "if", "in", "local", "nil", "not", "or", "repeat", "return",
    "then", "true", "until", "while", "type",
}

# Roblox and Lua globals worth colouring differently from local variables.
GLOBALS = {
    "game", "workspace", "Workspace", "script", "shared", "plugin",
    "Enum", "Instance", "Vector2", "Vector3", "CFrame", "Color3", "UDim", "UDim2",
    "BrickColor", "Random", "TweenInfo", "NumberRange", "NumberSequence",
    "ColorSequence", "Ray", "Region3", "Rect", "PhysicalProperties", "Font",
    "task", "os", "math", "table", "string", "coroutine", "utf8", "buffer", "bit32",
    "print", "warn", "error", "assert", "pcall", "xpcall", "select", "typeof",
    "type", "tonumber", "tostring", "ipairs", "pairs", "next", "unpack", "require",
    "setmetatable", "getmetatable", "rawget", "rawset", "rawequal", "rawlen",
    "tick", "time", "wait", "spawn", "delay", "newproxy", "gcinfo",
}

# One pass, longest-match-first. Order matters.
TOKEN_RE = re.compile(
    r"""
    (?P<blockcomment>--\[(?P<bceq>=*)\[.*?\](?P=bceq)\])
  | (?P<comment>--[^\n]*)
  | (?P<longstring>\[(?P<lseq>=*)\[.*?\](?P=lseq)\])
  | (?P<string>"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')
  | (?P<number>0[xX][0-9a-fA-F_]+|0[bB][01_]+|(?:\d[\d_]*)?\.?\d[\d_]*(?:[eE][+-]?\d+)?)
  | (?P<method>[:.]\s*(?P<mname>[A-Za-z_]\w*)(?=\s*[({"']))
  | (?P<prop>\.\s*(?P<pname>[A-Za-z_]\w*))
  | (?P<name>[A-Za-z_]\w*)
  | (?P<punct>[-+*/%^#=~<>(){}\[\];:,.]|\.\.\.?|::)
  | (?P<ws>\s+)
    """,
    re.VERBOSE | re.DOTALL,
)


def _span(cls, text):
    return f'<span class="t-{cls}">{html.escape(text, quote=False)}</span>'


def highlight(code):
    """Luau source -> HTML with <span class="t-*"> tokens."""
    out = []
    pos = 0

    for m in TOKEN_RE.finditer(code):
        # anything the tokenizer skipped passes through escaped
        if m.start() > pos:
            out.append(html.escape(code[pos:m.start()], quote=False))
        pos = m.end()

        kind = m.lastgroup
        text = m.group(0)

        if kind in ("blockcomment", "bceq") or m.group("blockcomment"):
            out.append(_span("com", text))
        elif m.group("comment"):
            out.append(_span("com", text))
        elif m.group("longstring") or m.group("string"):
            out.append(_span("str", text))
        elif m.group("number"):
            out.append(_span("num", text))
        elif m.group("method"):
            # keep the leading : or . uncoloured, colour the method name
            name = m.group("mname")
            lead = text[: text.index(name)]
            out.append(html.escape(lead, quote=False) + _span("fn", name))
        elif m.group("prop"):
            name = m.group("pname")
            lead = text[: text.index(name)]
            out.append(html.escape(lead, quote=False) + _span("prop", name))
        elif m.group("name"):
            if text in KEYWORDS:
                out.append(_span("key", text))
            elif text in GLOBALS:
                out.append(_span("glob", text))
            else:
                out.append(html.escape(text, quote=False))
        else:
            out.append(html.escape(text, quote=False))

    if pos < len(code):
        out.append(html.escape(code[pos:], quote=False))

    return "".join(out)


def highlight_block(code, lang):
    """Highlight if we know the language, otherwise just escape."""
    if lang in ("lua", "luau"):
        return highlight(code)
    return html.escape(code, quote=False)
