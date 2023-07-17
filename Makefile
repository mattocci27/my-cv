AUTHOR='Shikibu, M.'
LASTNAME=Shikibu
OUTPUT_PREFIX=outputs/$(LASTNAME)_CV

COMMON_DEPS = main.qmd sources/cv1.qmd outputs/ref_output_edit.md sources/cv2.qmd

.PHONY: all ref pdf docx md clean

all: pdf docx md

ref: outputs/ref_output_edit.md

pdf: $(OUTPUT_PREFIX).pdf

docx: $(OUTPUT_PREFIX).docx

md: $(OUTPUT_PREFIX).md

outputs/ref_output_edit.md: sources/ref.qmd sources/ref.bib scripts/ref_edit.py
	quarto render sources/ref.qmd --to=md
	mv sources/ref_output.md outputs/ref_output.md
	python scripts/ref_edit.py $(AUTHOR)

$(OUTPUT_PREFIX).pdf: $(COMMON_DEPS)
	quarto render main.qmd --to=pdf
	mv main.pdf $(OUTPUT_PREFIX).pdf
	mv main.tex outputs/$(LASTNAME)_CV.tex

$(OUTPUT_PREFIX).docx: $(COMMON_DEPS)
	quarto render main.qmd --to=docx
	mv main.docx $(OUTPUT_PREFIX).docx

$(OUTPUT_PREFIX).md: $(COMMON_DEPS)
	quarto render main.qmd --to=md
	mv main.md $(OUTPUT_PREFIX).md

clean:
	rm -f outputs/*.tuc \
	outputs/*.log \
	cont-en.*
