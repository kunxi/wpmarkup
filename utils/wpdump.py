#!/usr/bin/env python

def Usage():
    print "%s wordpress_exported.xml" % __file__


def dump_post(exported_data):
    from xml.etree import ElementTree as ET
    tree = ET.parse(exported_data)
    qnames = {
            "wp": "http://wordpress.org/export/1.0/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "content": "http://purl.org/rss/1.0/modules/content/",
            "excerpt": "http://wordpress.org/export/1.0/excerpt/",
    }

    for post in tree.findall("channel/item" % qnames):
        slug = post.find("{%(wp)s}post_name" % qnames).text
        body =  post.find("{%(content)s}encoded" % qnames).text.encode("utf-8")
        print "Dump post %s" % slug
        #import pdb; pdb.set_trace()
        f = open(slug, "wb")
        f.write(body)
        f.close()



if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        Usage()
        sys.exit(1)

    dump_post(sys.argv[1])

