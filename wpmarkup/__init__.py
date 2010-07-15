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

    dynamic_characters = [ "'(\d\d(?:&#8217;|')?s)", '(\s|\A|")\'', '(\d+)"', "(\d+)'", "(\S)'([^'\s])", '(\s|\A)"(?!\s)', '"(\s|\S|\Z)', "'([\s.]|\Z)", '(\d+)x(\d+)', "(<.*>|[.*])" ]
    dynamic_replacements = [ r'&#8217;\1',r'\1&#8216;', r'\1&#8243;', r'\1&#8242;', r'\1&#8217;\2', r'\1%s' % opening_quote , r'%s\1' % closing_quote, r'&#8217;\1', r'\1&#215;\2', r'&#038;\1' ]
    dynamic_regex = zip([ re.compile(x, re.DOTALL) for x in dynamic_characters ], dynamic_replacements)

    no_texturize_tags = ['pre', 'code', 'kbd', 'style', 'script', 'tt']
    no_texturize_shortcodes = ['code']
    token_regex = re.compile('(<.*?>|\[.*?\])', re.DOTALL)

    @staticmethod
    def render(raw):
        """
        >>> Markup.render(''''cause today's effort makes it worth tomorrow's "holiday"...''')
        '&#8217;cause today&#8217;s effort makes it worth tomorrow&#8217;s &#8220;holiday&#8221;&#8230;'

        >>> Markup.render('<pre>sadsadasd</code>"baba"</pre>')
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()

