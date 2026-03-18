DOCTYPE = RTN
DOCNUMBER = 115
DOCNAME = $(DOCTYPE)-$(DOCNUMBER)
FLATDIR = forAAS
SUBDIRS = figures

tex = $(filter-out $(wildcard *aglossary.tex) , $(wildcard *.tex))

GITVERSION := $(shell git log -1 --date=short --pretty=%h)
GITDATE := $(shell git log -1 --date=short --pretty=%ad)
GITSTATUS := $(shell git status --porcelain)
ifneq "$(GITSTATUS)" ""
	GITDIRTY = -dirty
endif

export TEXMFHOME ?= lsst-texmf/texmf

$(DOCNAME).pdf: $(tex) local.bib authors.tex aglossary.tex
	latexmk -bibtex -xelatex -f $(DOCNAME)
	makeglossaries $(DOCNAME)
	latexmk -bibtex -xelatex -f $(DOCNAME)

authors.tex:  authors.yaml
	python3 $(TEXMFHOME)/../bin/db2authors.py > authors.tex

flat:
	if [ ! -d $(FLATDIR) ]; then \
		mkdir $(FLATDIR) ; \
	fi
	latexpand --keep-comments -o $(FLATDIR)/$(DOCNAME).tex $(DOCNAME).tex
	@for dir in $(SUBDIRS); do \
		if [ -d "$$dir" ] && [ -n "$$(ls -A $$dir 2>/dev/null)" ]; then \
			cp $$dir/* $(FLATDIR); \
			echo "  ✓ Copied $$dir"; \
		fi; \
	done
	cp aas*.* $(FLATDIR)
	cp *.bib $(FLATDIR)
	cd $(FLATDIR) &&\
	latexmk -bibtex -xelatex -f $(DOCNAME) &&\
	makeglossaries $(DOCNAME) &&\
	latexmk -bibtex -xelatex -f $(DOCNAME) &&\
	latexmk -c &&\
	rm -f *.gls *.xdv *.glg *.glo *.ist *.bib &&\
	if [ -f README.rst ]; then rm README.txt; fi && \
	echo "Flat files in $(FLATDIR)."

.PHONY: clean
clean:
	latexmk -c
	rm -f $(DOCNAME).bbl
	rm -f $(DOCNAME).pdf
	rm -f meta.tex
	rm -f authors.tex
	rm -f $(FLATDIR)/*

.FORCE:

SCRIPTS_DIR=scripts
PYTHON_SCRIPTS=$(wildcard $(SCRIPTS_DIR)/*.py)

authors.txt:  authors.yaml
	python3 $(TEXMFHOME)/../bin/db2authors.py -m arxiv > authors.txt

authors.csv: authors.yaml
	python3 $(TEXMFHOME)/../bin/db2authors.py -m aascsv > authors.csv

aglossary.tex :$(tex) myacronyms.txt
	python3 $(TEXMFHOME)/../bin/generateAcronyms.py -t"Sci DM Gen" -g $(tex)

deps:
	pip install -r lsst-texmf/requirements.txt 

authors.yaml:
	python3 $(TEXMFHOME)/../bin/makeAuthorListsFromGoogle.py --builder --signup 4 -p 1CGxjpPuyNJ_gXRHTvkEF0qeI0XedQ-GQgbmyzWFLSUE "RTN-115!A2:E1000"

skip: .FORCE
	python3 $(TEXMFHOME)/../bin/makeAuthorListsFromGoogle.py --skip `cat skip.count` --builder --signup 4 -p 1CGxjpPuyNJ_gXRHTvkEF0qeI0XedQ-GQgbmyzWFLSUE "RTN-115!A2:E1000"
	
scripts:
	@echo "Running Python scripts..."
	@for script in $(PYTHON_SCRIPTS); do \
		python3 $$script; \
	done
