#!/usr/bin/php

<?php

function wptexturize($text) {
	global $wp_cockneyreplace;
	$output = '';
	$curl = '';
	$textarr = preg_split('/(<.*>|\[.*\])/Us', $text, -1, PREG_SPLIT_DELIM_CAPTURE);
	$stop = count($textarr);
	
	/* translators: opening curly quote */
	$opening_quote = ('&#8220;');
	/* translators: closing curly quote */
	$closing_quote = ('&#8221;');
	
	$no_texturize_tags = array('pre', 'code', 'kbd', 'style', 'script', 'tt');
	$no_texturize_shortcodes = array('code');
	$no_texturize_tags_stack = array();
	$no_texturize_shortcodes_stack = array();

	// if a plugin has provided an autocorrect array, use it
		$cockney = array("'tain't","'twere","'twas","'tis","'twill","'til","'bout","'nuff","'round","'cause");
		$cockneyreplace = array("&#8217;tain&#8217;t","&#8217;twere","&#8217;twas","&#8217;tis","&#8217;twill","&#8217;til","&#8217;bout","&#8217;nuff","&#8217;round","&#8217;cause");

	$static_characters = array_merge(array('---', ' -- ', '--', ' - ', 'xn&#8211;', '...', '``', '\'s', '\'\'', ' (tm)'), $cockney);
	$static_replacements = array_merge(array('&#8212;', ' &#8212; ', '&#8211;', ' &#8211; ', 'xn--', '&#8230;', $opening_quote, '&#8217;s', $closing_quote, ' &#8482;'), $cockneyreplace);

	$dynamic_characters = array('/\'(\d\d(?:&#8217;|\')?s)/', '/(\s|\A|")\'/', '/(\d+)"/', '/(\d+)\'/', '/(\S)\'([^\'\s])/', '/(\s|\A)"(?!\s)/', '/"(\s|\S|\Z)/', '/\'([\s.]|\Z)/', '/(\d+)x(\d+)/');
    $dynamic_replacements = array('&#8217;$1','$1&#8216;', '$1&#8243;', '$1&#8242;', '$1&#8217;$2', '$1' . $opening_quote . '$2', $closing_quote . '$1', '&#8217;$1', '$1&#215;$2');

    for ( $i = 0; $i < $stop; $i++ ) {
        $curl = $textarr[$i];

        if ( !empty($curl) && '<' != $curl{0} && '[' != $curl{0}
                && empty($no_texturize_shortcodes_stack) && empty($no_texturize_tags_stack)) { // If it's not a tag
            // static strings
            $curl = str_replace($static_characters, $static_replacements, $curl);
            // regular expressions
            $curl = preg_replace($dynamic_characters, $dynamic_replacements, $curl);
        } else {
            wptexturize_pushpop_element($curl, $no_texturize_tags_stack, $no_texturize_tags, '<', '>');
            wptexturize_pushpop_element($curl, $no_texturize_shortcodes_stack, $no_texturize_shortcodes, '[', ']');
        }

        $curl = preg_replace('/&([^#])(?![a-zA-Z1-4]{1,8};)/', '&#038;$1', $curl);
        $output .= $curl;
    }

	return $output;
}

function wptexturize_pushpop_element($text, &$stack, $disabled_elements, $opening = '<', $closing = '>') {
	$o = preg_quote($opening, '/');
	$c = preg_quote($closing, '/');
	foreach($disabled_elements as $element) {
		if (preg_match('/^'.$o.$element.'\b/', $text)) array_push($stack, $element);
		if (preg_match('/^'.$o.'\/'.$element.$c.'/', $text)) {
			$last = array_pop($stack);
			// disable texturize until we find a closing tag of our type (e.g. <pre>)
			// even if there was invalid nesting before that
			// Example: in the case <pre>sadsadasd</code>"baba"</pre> "baba" won't be texturized
			if ($last != $element) array_push($stack, $last);
		}
	}
}

$handle = fopen("php://stdin", "r");
$text = fread($handle, 5000);
echo wptexturize($text);

?>
    
