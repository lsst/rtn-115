DOCTYPE = RTN
DOCNUMBER = 115
DOCNAME = $(DOCTYPE)-$(DOCNUMBER)

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

.PHONY: clean
clean:
	latexmk -c
	rm -f $(DOCNAME).bbl
	rm -f $(DOCNAME).pdf
	rm -f meta.tex
	rm -f authors.tex

.FORCE:



SCRIPTS_DIR=scripts
PYTHON_SCRIPTS=$(wildcard $(SCRIPTS_DIR)/*.py)

authors.txt:  authors.txt
	python3 $(TEXMFHOME)/../bin/db2authors.py -m arxiv > authors.txt

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
