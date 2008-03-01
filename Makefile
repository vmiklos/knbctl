VERSION = 0.1.0

doc: HEADER.html Changelog

HEADER.html: README
	ln -s README HEADER.txt
	asciidoc -a toc -a numbered -a sectids HEADER.txt
	rm HEADER.txt

Changelog: .git/refs/heads/master
	git log --no-merges |git name-rev --tags --stdin >Changelog

dist:
	git-archive --format=tar --prefix=knbctl-$(VERSION)/ HEAD > knbctl-$(VERSION).tar
	mkdir -p knbctl-$(VERSION)
	git log --no-merges |git name-rev --tags --stdin > knbctl-$(VERSION)/Changelog
	tar rf knbctl-$(VERSION).tar knbctl-$(VERSION)/Changelog
	rm -rf knbctl-$(VERSION)
	gzip -f -9 knbctl-$(VERSION).tar

release:
	git tag -l |grep -q $(VERSION) || git tag -a -m $(VERSION) $(VERSION)
	$(MAKE) dist
