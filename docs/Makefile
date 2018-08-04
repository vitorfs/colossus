# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = Colossus
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  spelling   to check for typos in documentation"


spelling:
	$(SPHINXBUILD) -b spelling $(SOURCEDIR) $(BUILDDIR)/spelling $(SPHINXOPTS)
	@echo
	@echo "Check finished. Wrong words can be found in " \
		"$(BUILDDIR)/spelling/output.txt."
