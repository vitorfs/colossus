# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = Colossus
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help html spelling

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  spelling   to check for typos in documentation"

html:
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

spelling:
	$(SPHINXBUILD) -b spelling $(SOURCEDIR) $(BUILDDIR)/spelling $(SPHINXOPTS)
	@echo
	@echo "Check finished. Wrong words can be found in " \
		"$(BUILDDIR)/spelling/output.txt."
