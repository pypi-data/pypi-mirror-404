from slidge_style_parser import format_for_telegram

def test_basic():
    test = "_underline_"
    formatted_body = "underline"
    styles = [('italics', 0, 9, '')]
    assert(format_for_telegram(test) == (formatted_body, styles))

    test = "*bold*"
    formatted_body = "bold"
    styles = [('bold', 0, 4, '')]
    assert(format_for_telegram(test) == (formatted_body, styles))

    test = "~strikethrough~"
    formatted_body = "strikethrough"
    styles = [('strikethrough', 0, 13, '')]
    assert(format_for_telegram(test) == (formatted_body, styles))

    test = "`code span`"
    formatted_body = "code span"
    styles = [('code', 0, 9, '')]
    assert(format_for_telegram(test) == (formatted_body, styles))

    test = """
```python
    def test_basic():
        test = "_underline_"
        formatted_body = "underline"
        assert(format_for_telegram(test)[0] == formatted_body)
```
"""
    formatted_body = '\n    def test_basic():\n        test = "_underline_"\n        formatted_body = "underline"\n        assert(format_for_telegram(test)[0] == formatted_body)\n'
    styles = [('pre', 1, 150, 'python')]
    assert(format_for_telegram(test) == (formatted_body, styles))

    test = "```\ncode block\n```"
    formatted_body = "code block"
    styles = [('pre', 0, 10, '')]
    assert(format_for_telegram(test) == (formatted_body, styles))

    test = "||this message contains a spoiler||"
    formatted_body = "this message contains a spoiler"
    styles = [('spoiler', 0, 31, '')]
    assert(format_for_telegram(test) == (formatted_body, styles))

    test = "❤️💓💕💖💗 ||💙💚💛💜🖤|| 💝💞💟❣️"
    formatted_body = "❤️💓💕💖💗 💙💚💛💜🖤 💝💞💟❣️"
    styles = [('spoiler', 11, 10, '')]
    assert(format_for_telegram(test) == (formatted_body, styles))

def test_basic_mention():
    test = "SavagePeanut _underline_"
    formatted_body = "SavagePeanut underline"
    styles = [('mention', 0, 12, ''), ('italics', 13, 9, '')]
    assert(format_for_telegram(test, [("SavagePeanut", 0, 12)]) == (formatted_body, styles))

    test = "*bold* SavagePeanut"
    formatted_body = "bold SavagePeanut"
    styles = [('bold', 0, 4, ''), ('mention', 5, 12, '')]
    assert(format_for_telegram(test, [("SavagePeanut", 7, 19)]) == (formatted_body, styles))

def test_quotes():
    test = ">single"
    formatted_body = ">single"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">single arrow ->"
    formatted_body = ">single arrow ->"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">single\n>grouped"
    formatted_body = ">single\n>grouped"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>double"
    formatted_body = ">>double"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>double\n>>double"
    formatted_body = ">>double\n>>double"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>double\n&>not quote"
    formatted_body = ">>double\n&>not quote"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>double\n>grouped single"
    formatted_body = ">>double\n>grouped single"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>>tripple\n>single\n>>double"
    formatted_body = ">>>tripple\n>single\n>>double"
    assert(format_for_telegram(test)[0] == formatted_body)

def test_code_blocks():
    test = "```\nhacker\ncode\n```"
    formatted_body = "hacker\ncode"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "```python\nhacker code\n```"
    formatted_body = "hacker code"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "```pythonaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\nhacker code\n```"
    formatted_body = "hacker code"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "```python\nhacker code\n```\nnormal text"
    formatted_body = "hacker code\nnormal text"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "```python\nhacker code\n```\nnormal text\n```java\npublic static void main(String [])\n```"
    formatted_body = "hacker code\nnormal text\npublic static void main(String [])"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">```java\n>why are you quoting a code block\n>```"
    formatted_body = ">why are you quoting a code block"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>```\n>>double quote code block\n>single quote not in code block\nnormal text"
    formatted_body = ">>double quote code block\n>single quote not in code block\nnormal text"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">```\n>please stop trying to break my parser ;-;"
    formatted_body = ">please stop trying to break my parser ;-;"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>```\n>>>>double quote code block\n>single quote not in code block\nnormal text"
    formatted_body = ">>>>double quote code block\n>single quote not in code block\nnormal text"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "_```_ignored\ninvalid code block\n```"
    formatted_body = "```ignored\ninvalid code block\n```"
    assert(format_for_telegram(test)[0] == formatted_body)


def test_escaped():
    test = "\\_no underline_"
    formatted_body = "_no underline_"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "\\\\_no underline_"
    formatted_body = "\\_no underline_"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">>>tripple\n\\>none\n>>double"
    formatted_body = ">>>tripple\n>none\n>>double"
    assert(format_for_telegram(test)[0] == formatted_body)

def test_nested():
    test = "`*~_code span_~*`"
    formatted_body = "*~_code span_~*"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "*_~`code span`~_*"
    formatted_body = "code span"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">*_~`code span`~_*"
    formatted_body = ">code span"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "*bold star >*< star bold*"
    formatted_body = "bold star >*< star bold"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "*_bold*_"
    formatted_body = "_bold_"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "__underlined__"
    formatted_body = "underlined"
    assert(format_for_telegram(test)[0] == formatted_body)

def test_no_changes():
    test = ""
    formatted_body = ""
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "~~ empty `````` styles **"
    formatted_body = "~~ empty `````` styles **"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "this is not an empty string"
    formatted_body = "this is not an empty string"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "arrow ->"
    formatted_body = "arrow ->"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = " > no quote"
    formatted_body = " > no quote"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "_not underlined"
    formatted_body = "_not underlined"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "|not a spoiler|"
    formatted_body = "|not a spoiler|"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "||\nalso\nnot\na\nspoiler||"
    formatted_body = "||\nalso\nnot\na\nspoiler||"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "`no code\nblock here`"
    formatted_body = "`no code\nblock here`"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "invalid ```\ncode block\n```"
    formatted_body = "invalid ```\ncode block\n```"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "```\ncode block\ninvalid```"
    formatted_body = "```\ncode block\ninvalid```"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "```\ncode block\n```invalid"
    formatted_body = "```\ncode block\n```invalid"
    assert(format_for_telegram(test)[0] == formatted_body)

def test_assorted():
    test = "\n"
    formatted_body = "\n"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "at the ||end||"
    formatted_body = "at the end"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "in the ~middle~ here"
    formatted_body = "in the middle here"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "_underline_ *bold* ~strikethrough~ >not quote ||spoiler||\n>quote\nnothing\nnothing\n>>>>another quote with ||~_*```four```*_~||"
    formatted_body = "underline bold strikethrough >not quote spoiler\n>quote\nnothing\nnothing\n>>>>another quote with ```four```"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">```\n>do be do be dooo ba do be do be do ba\n>>>"
    formatted_body = ">do be do be dooo ba do be do be do ba\n>>"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "\n\n>```\n>do be do be dooo ba do be do be do ba\na\n\n\naoeu\n"
    formatted_body = "\n\n>do be do be dooo ba do be do be do ba\na\n\n\naoeu\n"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">```\n>do be do be dooo ba do be do be do ba\n>\n>\n>aoeu"
    formatted_body = ">do be do be dooo ba do be do be do ba\n\n\naoeu"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">```\n>code block\n>```invalid end\n"
    formatted_body = ">code block\n```invalid end\n"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "invalid ```\ncode block\n*bold*\n```"
    formatted_body = "invalid ```\ncode block\nbold\n```"
    assert(format_for_telegram(test)[0] == formatted_body)

def test_weird_utf8():
    test = "❤️💓💕💖💗 ||💙💚💛💜🖤|| 💝💞💟❣️"
    formatted_body = "❤️💓💕💖💗 💙💚💛💜🖤 💝💞💟❣️"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "👨‍👩‍👧‍👧 _underline_👩‍👩‍👦‍👧"
    formatted_body = "👨‍👩‍👧‍👧 underline👩‍👩‍👦‍👧"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "\u202eRight to left"
    formatted_body = "\u202eRight to left"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = ">\u202eRight to left quote?"
    formatted_body = ">\u202eRight to left quote?"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "_Invisible\u200bseparator_"
    formatted_body = "Invisible\u200bseparator"
    assert(format_for_telegram(test)[0] == formatted_body)

    test = "~\u200b~"
    formatted_body = "\u200b"
    assert(format_for_telegram(test)[0] == formatted_body)
