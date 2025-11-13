AUTHOR := Katabuchi, M.
LASTNAME := Katabuchi
OUTPUT_PREFIX := outputs/$(LASTNAME)_CV
QUARTO ?= quarto
METADATA ?= sources/ref_metadata.yaml

COMMON_DEPS := main.qmd sources/cv1.qmd outputs/ref_output_edit.md sources/*

.PHONY: all ref pdf docx md clean

all: pdf docx md

ref: outputs/ref_output_edit.md

pdf: $(OUTPUT_PREFIX).pdf

docx: $(OUTPUT_PREFIX).docx

md: $(OUTPUT_PREFIX).md

outputs/ref_output_edit.md: sources/ref.qmd sources/ref.bib scripts/ref_edit.py $(METADATA)
	$(QUARTO) render sources/ref.qmd --to=md
	mv sources/ref_output.md outputs/ref_output.md
	python scripts/ref_edit.py -m $(METADATA) -a "$(AUTHOR)"

define render_main
	$(QUARTO) render main.qmd --to=$(1)
	mv main.$(1) $(OUTPUT_PREFIX).$(1)
endef

$(OUTPUT_PREFIX).pdf: $(COMMON_DEPS)
	$(call render_main,pdf)
	mv main.tex outputs/$(LASTNAME)_CV.tex

$(OUTPUT_PREFIX).docx: $(COMMON_DEPS)
	$(call render_main,docx)

$(OUTPUT_PREFIX).md: $(COMMON_DEPS)
	$(call render_main,md)

clean:
	rm -f outputs/*.tuc \
		outputs/*.log \
		cont-en.*
