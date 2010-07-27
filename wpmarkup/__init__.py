#!/usr/bin/env python
import re
try:
    from pygments import lexers, formatters, highlight
    PYGMENTS_INSTALLED = True
except ImportError:
    PYGMENTS_INSTALLED = False

"""
A simple WordPress markup.

"""
VERSION = "0.2.1"

class Markup:
    #   TODOl: add the l10n support
    # translators: opening tokeny quote
    opening_quote = '&#8220;'
    #translators: closing tokeny quote
    closing_quote = '&#8221;'

    cockney = [ "'tain't","'twere","'twas","'tis","'twill","'til","'bout","'nuff","'round","'cause"]
    cockneyreplace = [ "&#8217;tain&#8217;t","&#8217;twere","&#8217;twas","&#8217;tis","&#8217;twill","&#8217;til","&#8217;bout","&#8217;nuff","&#8217;round", "&#8217;cause" ]
    static_characters = [ '---', ' -- ', '--', ' - ', 'xn&#8211;', '...', '``', '\'s', '\'\'', ' (tm)' ]
    static_replacements = [ '&#8212;', ' &#8212; ', '&#8211;', ' &#8211; ', 'xn--', '&#8230;', opening_quote, '&#8217;s', closing_quote, ' &#8482;']
    static_dict = dict(zip(static_characters+cockney, static_replacements+cockneyreplace))
    static_regex = re.compile("(%s)" % "|".join(map(re.escape, static_dict.keys())))

    dynamic_characters = [ "'(\d\d(?:&#8217;|')?s)", '(\s|\A|")\'', '(\d+)"', "(\d+)'", "(\S)'([^'\s])", r'(\s|\A)"(?!\s)', '"(\s|\S|\Z)', "'([\s.]|\Z)", '(\d+)x(\d+)', r'&([^#])(?![a-zA-Z1-4]{1,8};)' ]

    dynamic_replacements = [ r'&#8217;\1', r'\1&#8216;', r'\1&#8243;', r'\1&#8242;', r'\1&#8217;\2', r'\1%s' % opening_quote , r'%s\1' % closing_quote, r'&#8217;\1', r'\1&#215;\2', r'&#038;\1' ]
    dynamic_regex = zip([ re.compile(x, re.DOTALL) for x in dynamic_characters ], dynamic_replacements)

    no_texturize_tags = ['pre', 'code', 'kbd', 'style', 'script', 'tt']
    no_texturize_shortcodes = ['code']
    token_regex = re.compile('(<.*?>|\[.*?\])', re.DOTALL)

    allblocks = '(?:table|thead|tfoot|caption|col|colgroup|tbody|tr|td|th|div|dl|dd|dt|ul|ol|li|pre|select|form|map|area|blockquote|address|math|style|input|p|h[1-6]|hr)'
    multiline_regexs = [
        [re.compile('<br />\s*?<br />', re.M), "\n\n"],
        [re.compile('(<%s[^>]*>)' % allblocks), r"\n\1"],
        [re.compile('(</%s\s*>)' % allblocks), r"\1\n\n"],
        [re.compile('(\r\n|\r)', re.M), "\n"],
        [re.compile('\s*<param([^>]*)>\s*', re.M), r"<param\1>"],
        [re.compile('\s*<embed>\s*', re.M), "<embed>"],
        [re.compile('\n\n+', re.M), "\n\n" ],
    ]
    newline_split_regex = re.compile("\n\s*\n")
    oneline_regexs = [
        [re.compile("<p>\s*</p>"), ''],
        [re.compile("<p>([^<]+)</(div|address|form)>"), r'<p>\1</p></2>'],
        [re.compile("<p>\s*(</?%s[^>]*>)\s*</p>" % allblocks), r'\1'],
        [re.compile("<p>(<li.+?)</p>"), r'\1'],
        [re.compile("<p><blockquote([^>]*)>", re.IGNORECASE), r'<blockquote\1><p>'],
        [re.compile("</blockquote></p>"), '</p></blockquote>'],
        [re.compile(r"<p>\s*(</?%s[^>]*>)" % allblocks), r'\1'],
        [re.compile("(</?%s[^>]*>)\s*</p>" % allblocks), r'\1'],
        # br = 1 start
        #[re.compile(r"<(script|style).*?</\1>"),
        #    lambda m: m.groups().replace("\n", "<WPPreserveNewline />") ],
        #[re.compile(r"(?<!<br />)\s*\n"), r'<br />\n'],
        #[re.compile(r"<WPPreserveNewline />"), r'\n'],
        # br = 1 end
        [re.compile("(</?%s[^>]*>)\s*<br />" % allblocks), r'\1'],
        [re.compile("<br />(\s*</?(?:p|li|div|dl|dd|dt|th|pre|td|ul|ol)[^>]*>)"), r'\1'],
        [re.compile("(<pre[^>]*>)(.*?)</pre>", re.I), 
            lambda m: "%s%s</pre>" % m.groups().replace('<br />', '') \
            .replace('<p>', '\n').replace('</p>', '') ],
        [re.compile("\n</p>$"), '</p>'],
    ]

    pyg_regex = re.compile(r'<code(.*?)>(.*?)</code>', re.DOTALL) 
   

    @staticmethod
    def render(raw):
        rendered = raw
        if PYGMENTS_INSTALLED:
            rendered = Markup.pygmentize(rendered)
        return Markup.wpautop(Markup.wptexturize(rendered))


    @staticmethod
    def wptexturize(raw):
        """
        >>> Markup.wptexturize(''''cause today's effort makes it worth tomorrow's "holiday"...''')
        '&#8217;cause today&#8217;s effort makes it worth tomorrow&#8217;s &#8220;holiday&#8221;&#8230;'

        >>> Markup.wptexturize('<pre>sadsadasd</code>"baba"</pre>')
        '<pre>sadsadasd</code>"baba"</pre>'
        """
        no_texturize_tags_stack = []
        no_texturize_shortcodes_stack = []
        output = []

        for token in Markup.token_regex.split(raw) :
            if len(token) and '<' != token[0] and '[' != token[0] \
                    and len(no_texturize_shortcodes_stack)  == 0 \
                    and len(no_texturize_tags_stack) ==  0: #If it's not a tag
                token = Markup.static_regex.sub(lambda mo: Markup.static_dict[mo.string[mo.start():mo.end()]], token) 
                for regex, repl in Markup.dynamic_regex:
                    token = regex.sub(repl, token)
            else:
                Markup.pushpop_element(token, no_texturize_tags_stack, Markup.no_texturize_tags, '<', '>');
                Markup.pushpop_element(token, no_texturize_shortcodes_stack, Markup.no_texturize_shortcodes, '[', ']');
            output.append(token)

        return "".join(output)
    

    @staticmethod
    def pushpop_element(text, stack, disabled_elements, opening = '<', closing = '>'): 
        o = re.escape(opening)
        c = re.escape(closing)

        for element in disabled_elements:
            if re.match(r'^%s%s\b' % (o, element), text):
                stack.append(element)
                break

            if re.match(r'^%s/%s%s' % (o, element, c), text):
                if len(stack):
                    last = stack.pop()
                # disable texturize until we find a closing tag of our type (e.g. <pre>)
                # even if there was invalid nesting before that
                # Example: in the case <pre>sadsadasd</code>"baba"</pre> "baba" won't be texturized
                    if last != element: stack.append(last)
                break


    @staticmethod
    def wpautop(pee, br = 1):
        if pee.strip() == '':
            return ''

        pee += '\n'

        for regex, repl in Markup.multiline_regexs:
            pee = regex.sub(repl, pee)

        pee = "".join( ["<p>%s</p>\n" % x.strip("\n") for x in Markup.newline_split_regex.split(pee) if x.strip() ])

        for regex, repl in Markup.oneline_regexs:
            pee = regex.sub(repl, pee)
        return pee

    @staticmethod
    def pygmentize(raw):

        ''' 
        Finds all <code class="python"></code> blocks in a text block and replaces it with 
        pygments-highlighted html semantics. It relies that you provide the format of the 
        input as class attribute.

        Inspiration:  http://www.djangosnippets.org/snippets/25/
        Updated by: Samualy Clay

        '''
        last_end = 0 
        rendered = '' 

        for match_obj in Markup.pyg_regex.finditer(raw): 
            code_class = match_obj.group(1) 
            code_string = match_obj.group(2) 
            if code_class.find('class') >= 0:
                language = re.split(r'"|\'', code_class)[1] 
                lexer = lexers.get_lexer_by_name(language) 
            else: 
                try: 
                    lexer = lexers.guess_lexer(str(code_string)) 
                except ValueError: 
                    lexer = lexers.PythonLexer() 
            pygmented_string = highlight(code_string, lexer, formatters.HtmlFormatter()) 
            rendered += raw[last_end:match_obj.start(0)] + pygmented_string 
            last_end = match_obj.end(0) 
        rendered += raw[last_end:] 
        return rendered


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        f = open(sys.argv[1], 'r')
        o = open(sys.argv[2], 'w')
        raw = f.read().decode("UTF-8")
        rendered = Markup.wpautop(Markup.pygmentize(raw))
        o.write(rendered.encode("UTF-8"))


