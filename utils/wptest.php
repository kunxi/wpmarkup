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

/**
 * Accepts matches array from preg_replace_callback in wpautop() or a string.
 *
 * Ensures that the contents of a <<pre>>...<</pre>> HTML block are not
 * converted into paragraphs or line-breaks.
 *
 * @since 1.2.0
 *
 * @param array|string $matches The array or string
 * @return string The pre block without paragraph/line-break conversion.
 */
function clean_pre($matches) {
	if ( is_array($matches) )
		$text = $matches[1] . $matches[2] . "</pre>";
	else
		$text = $matches;

	$text = str_replace('<br />', '', $text);
	$text = str_replace('<p>', "\n", $text);
	$text = str_replace('</p>', '', $text);

	return $text;
}

/**
 * Replaces double line-breaks with paragraph elements.
 *
 * A group of regex replaces used to identify text formatted with newlines and
 * replace double line-breaks with HTML paragraph tags. The remaining
 * line-breaks after conversion become <<br />> tags, unless $br is set to '0'
 * or 'false'.
 *
 * @since 0.71
 *
 * @param string $pee The text which has to be formatted.
 * @param int|bool $br Optional. If set, this will convert all remaining line-breaks after paragraphing. Default true.
 * @return string Text which has been converted into correct paragraph tags.
 */
function wpautop($pee, $br = 1) {
	if ( trim($pee) === '' )
		return '';
	$pee = $pee . "\n"; // just to make things a little easier, pad the end
	$pee = preg_replace('|<br />\s*<br />|', "\n\n", $pee);
	// Space things out a little
	$allblocks = '(?:table|thead|tfoot|caption|col|colgroup|tbody|tr|td|th|div|dl|dd|dt|ul|ol|li|pre|select|form|map|area|blockquote|address|math|style|input|p|h[1-6]|hr)';
	$pee = preg_replace('!(<' . $allblocks . '[^>]*>)!', "\n$1", $pee);
	$pee = preg_replace('!(</' . $allblocks . '>)!', "$1\n\n", $pee);
	$pee = str_replace(array("\r\n", "\r"), "\n", $pee); // cross-platform newlines
	if ( strpos($pee, '<object') !== false ) {
		$pee = preg_replace('|\s*<param([^>]*)>\s*|', "<param$1>", $pee); // no pee inside object/embed
		$pee = preg_replace('|\s*</embed>\s*|', '</embed>', $pee);
	}
	$pee = preg_replace("/\n\n+/", "\n\n", $pee); // take care of duplicates
    // make paragraphs, including one at the end
	$pees = preg_split('/\n\s*\n/', $pee, -1, PREG_SPLIT_NO_EMPTY);
	$pee = '';
	foreach ( $pees as $tinkle )
        $pee .= '<p>' . trim($tinkle, "\n") . "</p>\n";
    
	$pee = preg_replace('|<p>\s*</p>|', '', $pee); // under certain strange conditions it could create a P of entirely whitespace
	$pee = preg_replace('!<p>([^<]+)</(div|address|form)>!', "<p>$1</p></$2>", $pee);
	$pee = preg_replace('!<p>\s*(</?' . $allblocks . '[^>]*>)\s*</p>!', "$1", $pee); // don't pee all over a tag
	$pee = preg_replace("|<p>(<li.+?)</p>|", "$1", $pee); // problem with nested lists
	$pee = preg_replace('|<p><blockquote([^>]*)>|i', "<blockquote$1><p>", $pee);
	$pee = str_replace('</blockquote></p>', '</p></blockquote>', $pee);
	$pee = preg_replace('!<p>\s*(</?' . $allblocks . '[^>]*>)!', "$1", $pee);
	$pee = preg_replace('!(</?' . $allblocks . '[^>]*>)\s*</p>!', "$1", $pee);
	if ($br) {
		$pee = preg_replace_callback('/<(script|style).*?<\/\\1>/s', create_function('$matches', 'return str_replace("\n", "<WPPreserveNewline />", $matches[0]);'), $pee);
		$pee = preg_replace('|(?<!<br />)\s*\n|', "<br />\n", $pee); // optionally make line breaks
		$pee = str_replace('<WPPreserveNewline />', "\n", $pee);
	}
	$pee = preg_replace('!(</?' . $allblocks . '[^>]*>)\s*<br />!', "$1", $pee);
	$pee = preg_replace('!<br />(\s*</?(?:p|li|div|dl|dd|dt|th|pre|td|ul|ol)[^>]*>)!', '$1', $pee);
	if (strpos($pee, '<pre') !== false)
		$pee = preg_replace_callback('!(<pre[^>]*>)(.*?)</pre>!is', 'clean_pre', $pee );
	$pee = preg_replace( "|\n</p>$|", '</p>', $pee );
    # $pee = preg_replace('/<p>\s*?(' . get_shortcode_regex() . ')\s*<\/p>/s', '$1', $pee); // don't auto-p wrap shortcodes that stand alone
  

	return $pee;
}

/**
 * Converts a number of characters from a string.
 *
 * Metadata tags <<title>> and <<category>> are removed, <<br>> and <<hr>> are
 * converted into correct XHTML and Unicode characters are converted to the
 * valid range.
 *
 * @since 0.71
 *
 * @param string $content String of characters to be converted.
 * @param string $deprecated Not used.
 * @return string Converted string.
 */
function convert_chars($content, $deprecated = '') {
	// Translation of invalid Unicode references range to valid range
	$wp_htmltranswinuni = array(
	'&#128;' => '&#8364;', // the Euro sign
	'&#129;' => '',
	'&#130;' => '&#8218;', // these are Windows CP1252 specific characters
	'&#131;' => '&#402;',  // they would look weird on non-Windows browsers
	'&#132;' => '&#8222;',
	'&#133;' => '&#8230;',
	'&#134;' => '&#8224;',
	'&#135;' => '&#8225;',
	'&#136;' => '&#710;',
	'&#137;' => '&#8240;',
	'&#138;' => '&#352;',
	'&#139;' => '&#8249;',
	'&#140;' => '&#338;',
	'&#141;' => '',
	'&#142;' => '&#382;',
	'&#143;' => '',
	'&#144;' => '',
	'&#145;' => '&#8216;',
	'&#146;' => '&#8217;',
	'&#147;' => '&#8220;',
	'&#148;' => '&#8221;',
	'&#149;' => '&#8226;',
	'&#150;' => '&#8211;',
	'&#151;' => '&#8212;',
	'&#152;' => '&#732;',
	'&#153;' => '&#8482;',
	'&#154;' => '&#353;',
	'&#155;' => '&#8250;',
	'&#156;' => '&#339;',
	'&#157;' => '',
	'&#158;' => '',
	'&#159;' => '&#376;'
	);

	// Remove metadata tags
	$content = preg_replace('/<title>(.+?)<\/title>/','',$content);
	$content = preg_replace('/<category>(.+?)<\/category>/','',$content);

	// Converts lone & characters into &#38; (a.k.a. &amp;)
	$content = preg_replace('/&([^#])(?![a-z1-4]{1,8};)/i', '&#038;$1', $content);

	// Fix Word pasting
	$content = strtr($content, $wp_htmltranswinuni);

	// Just a little XHTML help
	$content = str_replace('<br>', '<br />', $content);
	$content = str_replace('<hr>', '<hr />', $content);

	return $content;
}


$handle = fopen($argv[1], "r");
$text = fread($handle, 5000);
fclose($handle);

$handle = fopen($argv[2], "w");
fwrite($handle, wpautop(convert_chars(wptexturize($text))));
fclose($handle);
?>
