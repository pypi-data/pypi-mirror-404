from slidge_style_parser import format_for_matrix


def test_basic():
    test = "_underline_"
    formatted_body = "<em>underline</em>"
    assert(format_for_matrix(test) == formatted_body)

    test = "*bold*"
    formatted_body = "<strong>bold</strong>"
    assert(format_for_matrix(test) == formatted_body)

    test = "~strikethrough~"
    formatted_body = "<s>strikethrough</s>"
    assert(format_for_matrix(test) == formatted_body)

    test = "`code span`"
    formatted_body = "<code>code span</code>"
    assert(format_for_matrix(test) == formatted_body)

    test = """
```python
    def test_basic():
        test = "_underline_"
        formatted_body = "<em>underline</em>"
        assert(format_for_matrix(test) == formatted_body)
```
"""
    formatted_body = '<br><pre><code class="language-python">    def test_basic():\n        test = "_underline_"\n        formatted_body = "<em>underline</em>"\n        assert(format_for_matrix(test) == formatted_body)</code></pre><br>'
    assert(format_for_matrix(test) == formatted_body)

    test = "```\ncode block\n```"
    formatted_body = "<pre><code>code block</code></pre>"
    assert(format_for_matrix(test) == formatted_body)

    test = "||this message contains a spoiler||"
    formatted_body = "<span data-mx-spoiler>this message contains a spoiler</span>"
    assert(format_for_matrix(test) == formatted_body)

def test_basic_mention():
    test = "SavagePeanut _underline_"
    formatted_body = "<a href='https://matrix.to/#/@SavagePeanut:example.org'>SavagePeanut</a> <em>underline</em>"
    assert(format_for_matrix(test, [("@SavagePeanut:example.org", 0, 12)]) == formatted_body)

    test = "*bold* SavagePeanut"
    formatted_body = "<strong>bold</strong> <a href='https://matrix.to/#/@SavagePeanut:example.org'>SavagePeanut</a>"
    assert(format_for_matrix(test, [("@SavagePeanut:example.org", 7, 19)]) == formatted_body)

def test_empty():
    test = "__ ** ~~ ``"
    formatted_body = "__ ** ~~ ``"
    assert(format_for_matrix(test) == formatted_body)

    test = "```\n```"
    formatted_body = "```<br>```"
    assert(format_for_matrix(test) == formatted_body)

    test = "```python\n```"
    formatted_body = "```python<br>```"
    assert(format_for_matrix(test) == formatted_body)

    test = "_____"
    formatted_body = "_____"
    assert(format_for_matrix(test) == formatted_body)

def test_quotes():
    test = ">single"
    formatted_body = "<blockquote>single</blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">single arrow ->"
    formatted_body = "<blockquote>single arrow -&gt;</blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">single\n>grouped"
    formatted_body = "<blockquote>single<br>grouped</blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>double"
    formatted_body = "<blockquote><blockquote>double</blockquote></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>double\n>>double"
    formatted_body = "<blockquote><blockquote>double<br>double</blockquote></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>double\n&>not quote"
    formatted_body = "<blockquote><blockquote>double</blockquote></blockquote><br>&&gt;not quote"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>double\n>grouped single"
    formatted_body = "<blockquote><blockquote>double</blockquote><br>grouped single</blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>>tripple\n>single\n>>double"
    formatted_body = "<blockquote><blockquote><blockquote>tripple</blockquote></blockquote><br>single<br><blockquote>double</blockquote></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

def test_code_blocks():
    test = "```\nhacker\ncode\n```"
    formatted_body = "<pre><code>hacker\ncode</code></pre>"
    assert(format_for_matrix(test) == formatted_body)

    test = "```python\nhacker code\n```"
    formatted_body = "<pre><code class=\"language-python\">hacker code</code></pre>"
    assert(format_for_matrix(test) == formatted_body)

    test = "```pythonaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\nhacker code\n```"
    formatted_body = "<pre><code class=\"language-pythonaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\">hacker code</code></pre>"
    assert(format_for_matrix(test) == formatted_body)

    test = "```python\nhacker code\n```\nnormal text"
    formatted_body = "<pre><code class=\"language-python\">hacker code</code></pre><br>normal text"
    assert(format_for_matrix(test) == formatted_body)

    test = "```python\nhacker code\n```\nnormal text\n```java\npublic static void main(String [])\n```"
    formatted_body = "<pre><code class=\"language-python\">hacker code</code></pre><br>normal text<br><pre><code class=\"language-java\">public static void main(String [])</code></pre>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">```java\n>why are you quoting a code block\n>```"
    formatted_body = "<blockquote><pre><code class=\"language-java\">why are you quoting a code block</code></pre></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>```\n>>double quote code block\n>single quote not in code block\nnormal text"
    formatted_body = "<blockquote><blockquote><pre><code>double quote code block</code></pre></blockquote><br>single quote not in code block</blockquote><br>normal text"
    assert(format_for_matrix(test) == formatted_body)

    test = ">```\n>please stop trying to break my parser ;-;"
    formatted_body = "<blockquote><pre><code>please stop trying to break my parser ;-;</code></pre></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>```\n>>>>double quote code block\n>single quote not in code block\nnormal text"
    formatted_body = "<blockquote><blockquote><pre><code>>>double quote code block</code></pre></blockquote><br>single quote not in code block</blockquote><br>normal text"
    assert(format_for_matrix(test) == formatted_body)

    test = "_```_ignored\ninvalid code block\n```"
    formatted_body = "<em>```</em>ignored<br>invalid code block<br>```"
    assert(format_for_matrix(test) == formatted_body)


def test_escaped():
    test = "\\_no underline_"
    formatted_body = "_no underline_"
    assert(format_for_matrix(test) == formatted_body)

    test = "\\\\_no underline_"
    formatted_body = "\\_no underline_"
    assert(format_for_matrix(test) == formatted_body)

    test = ">>>tripple\n\\>none\n>>double"
    formatted_body = "<blockquote><blockquote><blockquote>tripple</blockquote></blockquote></blockquote><br>>none<br><blockquote><blockquote>double</blockquote></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

def test_nested():
    test = "`*~_code span_~*`"
    formatted_body = "<code>*~_code span_~*</code>"
    assert(format_for_matrix(test) == formatted_body)

    test = "*_~`code span`~_*"
    formatted_body = "<strong><em><s><code>code span</code></s></em></strong>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">*_~`code span`~_*"
    formatted_body = "<blockquote><strong><em><s><code>code span</code></s></em></strong></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = "*bold star >*< star bold*"
    formatted_body = "<strong>bold star &gt;*&lt; star bold</strong>"
    assert(format_for_matrix(test) == formatted_body)

    test = "*_bold*_"
    formatted_body = "<strong>_bold</strong>_"
    assert(format_for_matrix(test) == formatted_body)

    test = "__underlined__"
    formatted_body = "<em><em>underlined</em></em>"
    assert(format_for_matrix(test) == formatted_body)

def test_no_changes():
    test = ""
    formatted_body = ""
    assert(format_for_matrix(test) == formatted_body)

    test = "~~ empty `````` styles **"
    formatted_body = "~~ empty `````` styles **"
    assert(format_for_matrix(test) == formatted_body)

    test = "this is not an empty string"
    formatted_body = "this is not an empty string"
    assert(format_for_matrix(test) == formatted_body)

    test = "arrow ->"
    formatted_body = "arrow -&gt;"
    assert(format_for_matrix(test) == formatted_body)

    test = " > no quote"
    formatted_body = " &gt; no quote"
    assert(format_for_matrix(test) == formatted_body)

    test = "_not underlined"
    formatted_body = "_not underlined"
    assert(format_for_matrix(test) == formatted_body)

    test = "|not a spoiler|"
    formatted_body = "|not a spoiler|"
    assert(format_for_matrix(test) == formatted_body)

    test = "||\nalso\nnot\na\nspoiler||"
    formatted_body = "||<br>also<br>not<br>a<br>spoiler||"
    assert(format_for_matrix(test) == formatted_body)

    test = "`no code\nblock here`"
    formatted_body = "`no code<br>block here`"
    assert(format_for_matrix(test) == formatted_body)

    test = "invalid ```\ncode block\n```"
    formatted_body = "invalid ```<br>code block<br>```"
    assert(format_for_matrix(test) == formatted_body)

    test = "```\ncode block\ninvalid```"
    formatted_body = "```<br>code block<br>invalid```"
    assert(format_for_matrix(test) == formatted_body)

    test = "```\ncode block\n```invalid"
    formatted_body = "```<br>code block<br>```invalid"
    assert(format_for_matrix(test) == formatted_body)

def test_assorted():
    test = "\n"
    formatted_body = "<br>"
    assert(format_for_matrix(test) == formatted_body)

    test = "at the ||end||"
    formatted_body = "at the <span data-mx-spoiler>end</span>"
    assert(format_for_matrix(test) == formatted_body)

    test = "in the ~middle~ here"
    formatted_body = "in the <s>middle</s> here"
    assert(format_for_matrix(test) == formatted_body)

    test = "_underline_ *bold* ~strikethrough~ >not quote ||spoiler||\n>quote\nnothing\nnothing\n>>>>another quote with ||~_*```four```*_~||"
    formatted_body = "<em>underline</em> <strong>bold</strong> <s>strikethrough</s> &gt;not quote <span data-mx-spoiler>spoiler</span><br><blockquote>quote</blockquote><br>nothing<br>nothing<br><blockquote><blockquote><blockquote><blockquote>another quote with <span data-mx-spoiler><s><em><strong>```four```</strong></em></s></span></blockquote></blockquote></blockquote></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = "```\nhacker\ncode\n```\n\n```\nhacker\ncode\n```"
    formatted_body = "<pre><code>hacker\ncode</code></pre><br><br><pre><code>hacker\ncode</code></pre>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">```\n>do be do be dooo ba do be do be do ba\n>>>"
    formatted_body = "<blockquote><pre><code>do be do be dooo ba do be do be do ba\n>></code></pre></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = "\n\n>```\n>do be do be dooo ba do be do be do ba\na\n\n\naoeu\n"
    formatted_body = "<br><br><blockquote><pre><code>do be do be dooo ba do be do be do ba</code></pre></blockquote><br>a<br><br><br>aoeu<br>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">```\n>do be do be dooo ba do be do be do ba\n>\n>\n>aoeu"
    formatted_body = "<blockquote><pre><code>do be do be dooo ba do be do be do ba\n\n\naoeu</code></pre></blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = ">```\n>code block\n>```invalid end\n"
    formatted_body = "<blockquote><pre><code>code block\n```invalid end</code></pre></blockquote><br>"
    assert(format_for_matrix(test) == formatted_body)

    test = "invalid ```\ncode block\n*bold*\n```"
    formatted_body = "invalid ```<br>code block<br><strong>bold</strong><br>```"
    assert(format_for_matrix(test) == formatted_body)

def test_weird_utf8():
    test = "❤️💓💕💖💗 ||💙💚💛💜🖤|| 💝💞💟❣️"
    formatted_body = "❤️💓💕💖💗 <span data-mx-spoiler>💙💚💛💜🖤</span> 💝💞💟❣️"
    assert(format_for_matrix(test) == formatted_body)

    test = "👨‍👩‍👧‍👧 _underline_👩‍👩‍👦‍👧"
    formatted_body = "👨‍👩‍👧‍👧 <em>underline</em>👩‍👩‍👦‍👧"
    assert(format_for_matrix(test) == formatted_body)

    test = "\u202eRight to left"
    formatted_body = "\u202eRight to left"
    assert(format_for_matrix(test) == formatted_body)

    test = ">\u202eRight to left quote?"
    formatted_body = "<blockquote>\u202eRight to left quote?</blockquote>"
    assert(format_for_matrix(test) == formatted_body)

    test = "_Invisible\u200bseparator_"
    formatted_body = "<em>Invisible\u200bseparator</em>"
    assert(format_for_matrix(test) == formatted_body)

    test = "~\u200b~"
    formatted_body = "<s>\u200b</s>"
    assert(format_for_matrix(test) == formatted_body)

    test = "<element>"
    formatted_body = "&lt;element&gt;"
    assert(format_for_matrix(test) == formatted_body)

    test = "< element >"
    formatted_body = "&lt; element &gt;"
    assert(format_for_matrix(test) == formatted_body)

    test = "< element>"
    formatted_body = "&lt; element&gt;"
    assert(format_for_matrix(test) == formatted_body)

    test = "<element >"
    formatted_body = "&lt;element &gt;"
    assert(format_for_matrix(test) == formatted_body)

    test = "<element> malicious script </element>"
    formatted_body = "&lt;element&gt; malicious script &lt;/element&gt;"
    assert(format_for_matrix(test) == formatted_body)
