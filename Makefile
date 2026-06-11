HTML := csp/ced.html csa/ced.html

all: $(HTML)

%/ced.html: %/ced.xml ced-to-html.xsl
	xsltproc ced-to-html.xsl $< > $@

clean:
	rm -f $(HTML)

.PHONY: all clean
