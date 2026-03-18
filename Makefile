DOCTYPE = RTN
DOCNUMBER = 115
DOCNAME = $(DOCTYPE)-$(DOCNUMBER)
FLATDIR = forAAS
SUBDIRS = figures

tex = $(filter-out $(wildcard *aglossary.tex) , $(wildcard sections/*.tex) $(wildcard *.tex) )

GITVERSION := $(shell git log -1 --date=short --pretty=%h)
GITDATE := $(shell git log -1 --date=short --pretty=%ad)
GITSTATUS := $(shell git status --porcelain)
ifneq "$(GITSTATUS)" ""
	GITDIRTY = -dirty
endif

export TEXMFHOME ?= lsst-texmf/texmf

UV_RUN = uv run

$(DOCNAME).pdf: $(tex) local.bib authors.tex aglossary.tex parameters_static.tex
	latexmk -bibtex -xelatex -f $(DOCNAME)
	makeglossaries $(DOCNAME)
	latexmk -bibtex -xelatex -f $(DOCNAME)

authors.tex: authors.yaml
	$(UV_RUN) python $(TEXMFHOME)/../bin/db2authors.py > authors.tex

parameters_static.tex: data/static_parameters.yaml
	$(UV_RUN) python bin/dp2_parameters.py --static-only

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
	rm -f $(DOCNAME).gls
	rm -f $(DOCNAME).pdf
	rm -f meta.tex
	rm -f authors.tex
	rm -f $(FLATDIR)/*
	rm -f parameters_static.tex

.FORCE:

SCRIPTS_DIR = scripts
PYTHON_SCRIPTS = $(wildcard $(SCRIPTS_DIR)/*.py)

authors.txt: authors.yaml
	$(UV_RUN) python $(TEXMFHOME)/../bin/db2authors.py -m arxiv > authors.txt

authors.csv: authors.yaml
	$(UV_RUN) python $(TEXMFHOME)/../bin/db2authors.py -m aascsv > authors.csv

aglossary.tex: $(tex) myacronyms.txt
	$(UV_RUN) python $(TEXMFHOME)/../bin/generateAcronyms.py -n -t"Sci DM Gen" -g $(tex)

.PHONY: deps
deps:
	pip install uv
	uv pip install -r lsst-texmf/requirements.txt
	uv pip install -r requirements.txt

# these are called by the github action and it already installs all dependanceies
authors.yaml:
	python $(TEXMFHOME)/../bin/makeAuthorListsFromGoogle.py --builder --signup 4 -p 1CGxjpPuyNJ_gXRHTvkEF0qeI0XedQ-GQgbmyzWFLSUE "RTN-115!A2:E1000"

skip: .FORCE
	python $(TEXMFHOME)/../bin/makeAuthorListsFromGoogle.py --skip `cat skip.count` --builder --signup 4 -p 1CGxjpPuyNJ_gXRHTvkEF0qeI0XedQ-GQgbmyzWFLSUE "RTN-115!A2:E1000"

.PHONY: scripts
scripts:
	@echo "Running Python scripts..."
	@for script in $(PYTHON_SCRIPTS); do \
		$(UV_RUN) python $$script; \
	done
.PHONY: lander
lander:
	uv venv --clear lander
	. lander/bin/activate && \
	uv pip install --python lander/bin/python -r requirements-lander.txt && \
	lander --upload --pdf RTN-115.pdf --ltd-product rtn-115 --title "The Vera C. Rubin Observatory Data Preview 2" --handle "RTN-115" --lsstdoc "RTN-115.tex"
