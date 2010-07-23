#!/usr/bin/env python

import sys, subprocess
sys.path.append('..') # hack to use the latest wpmarkup.
import wpmarkup

def Usage():
    print "%s raw " % __file__

def main():
    if len(sys.argv) == 1:
        Usage()
        sys.exit()
    print "wpmarkup v %s" % wpmarkup.VERSION

    for fn in sys.argv[1:]:
        print "WordPress rendering %s " % fn
        subprocess.call(["./wptest.php", fn, "%s.wordpress" % fn])
        print "wpmarkup rendering %s " % fn
        fin = open(fn, "r")
        text = wpmarkup.Markup.render(fin.read())
        fout = open("%s.wpmarkup" % fn, "w")
        fout.write(text)
        fin.close()
        fout.close()
        ret = subprocess.call(['diff', '-q',  "%s.wordpress" % fn, "%s.wpmarkup" % fn])
        if ret == 0:
            print "  same."
        else:
            print "  DIFFRENT!" 

if __name__ == "__main__":
    main()




