# Slidge-style-parser

[![PyPI version](https://badge.fury.io/py/slidge-style-parser.svg)](https://badge.fury.io/py/slidge-style-parser)

License: AGPL-3.0-or-later

A parsing library for [Slidge](https://sr.ht/~nicoco/slidge). Supports parsing these attributes:

- "\_underline_"
- "\*bold*"
- "\~strikethrough~"
- "\`code span`"
- "\```language

   code block

   \```"
- "\>quote"
- "\|\|spoiler||"
- "\\\_escape style_"

Most of them correspond to [XEP-0393: Message Styling](https://xmpp.org/extensions/xep-0393.html).

Methods: 

```python

format_for_telegram(body: String, mentions: Optional<(_, start, end_index_exclusive)>)
    -> (body: String, Vec<(format: String, offset: usize, length: usize, language: String)>)

format_for_matrix(body: String, mentions: Optional<(mxid, start, end_index_exclusive)>) -> body: String

format_body(body: String, new_tags: HashMap<String, (String, String)>) -> String

new_tags = {
    "_": ("<em>", "</em>"),
    "*": ("<strong>", "</strong>"),   
    "~": ("<del>", "</del>"),
    "`": ("<code>", "</code>"),
    "```": ("<pre><code>", "</code></pre>"),
    "```language": ('<pre><code class="language-{}">', "</code></pre>"),
    ">": ("<blockquote>", "</blockquote>"),
    "||": ("<span data-mx-spoiler>", "</span>"),
    "\n": ("<br>", "")
}

```

To build: `uv build` or any other [PEP517](https://peps.python.org/pep-0517/)-compliant tool
