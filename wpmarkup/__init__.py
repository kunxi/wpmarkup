#!/usr/bin/env python
import re
"""
A simple WordPress markup.

"""

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

    dynamic_characters = [ "'(\d\d(?:&#8217;|')?s)", '(\s|\A|")\'', '(\d+)"', "(\d+)'", "(\S)'([^'\s])", '(\s|\A)"(?!\s)', '"(\s|\S|\Z)', "'([\s.]|\Z)", '(\d+)x(\d+)', '&([^#])(?![a-zA-Z1-4]{1,8};)' ]
    dynamic_replacements = [ '&#8217;\1', '\1&#8216;', '\1&#8243;', '\1&#8242;', '\1&#8217;\2', '\1%s' % opening_quote , '%s\1' % closing_quote, '&#8217;\1', '\1&#215;\2', '&#038;\1' ]
    dynamic_regex = zip([ re.compile(x, re.DOTALL) for x in dynamic_characters ], dynamic_replacements)

    no_texturize_tags = ['pre', 'code', 'kbd', 'style', 'script', 'tt']
    no_texturize_shortcodes = ['code']
    token_regex = re.compile('(<.*?>|\[.*?\])', re.DOTALL)

    allblocks = '(?:table|thead|tfoot|caption|col|colgroup|tbody|tr|td|th|div|dl|dd|dt|ul|ol|li|pre|select|form|map|area|blockquote|address|math|style|input|p|h[1-6]|hr)'
    multiline_regexs = [
        [re.compile('<br />\s*?<br />', re.M), "\n\n"],
        [re.compile('<%s[^>]*>' % allblocks), "\n\1"],
        [re.compile('</%s\s*>' % allblocks), "\n\n\1"],
        [re.compile('(\r\n|\r)', re.M), "\n"],
        [re.compile('\s*<param([^>]*)>\s*', re.M), "<param\1>"],
        [re.compile('\s*<embed>\s*', re.M), "<embed>"],
        [re.compile('\n\n+', re.M), "\n\n" ],
    ]
    newline_split_regex = re.compile("\n\s*\n")
    oneline_regexs = [
        [re.compile("<p>\s*</p>"), ''],
        [re.compile("<p>([^<]+)</(div|address|form)>"), '<p>\1</p></2>'],
        [re.compile("<p>\s*(</?%s[^>]*>)\s*</p>" % allblocks), '\1'],
        [re.compile("<p>(<li.+?)</p>"), '\1'],
        [re.compile("<p><blockquote([^>]*)>", re.IGNORECASE), '<blockquote\1><p>'],
        [re.compile("</blockquote></p>"), '</p></blockquote>'],
        [re.compile("<p>\s*(</?%s'[^>]*>)" % allblocks), '\1'],
        [re.compile("(</?%s[^>]*>)\s*</p>" % allblocks), '\1'],
        # split to oneline2_regex if we want to support br=1
        [re.compile("(</?%s[^>]*>)\s*<br />" % allblocks), '\1'],
        [re.compile("<br />(\s*</?(?:p|li|div|dl|dd|dt|th|pre|td|ul|ol)[^>]*>)"), '\1'],
        [re.compile("(<pre[^>]*>)(.*?)</pre>", re.I), 
            lambda m: "%s%s</pre>" % match.groups().replace('<br />', '') \
            .replace('<p>', '\n').replace('</p>', '') ],
        [re.compile("\n</p>$"), '</p>'],
    ]

    @staticmethod
    def render(raw):
        return Markup.wpautop(Markup.wptexturize(raw))


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

        pee = "".join( ["<p>%s</p>\n" % x.strip() for x in Markup.newline_split_regex.split(pee) if x.strip() != ''])

        for regex, repl in Markup.oneline_regexs:
            pee = regex.sub(repl, pee)
        return pee


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        f = open(sys.argv[1], 'r')
        o = open(sys.argv[2], 'w')
        raw = f.read()
        o.write(Markup.render(raw))


