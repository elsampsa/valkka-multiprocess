#!/bin/bash
## https://nbconvert.readthedocs.io/en/latest/removing_cells.html

if [ $# -lt 1 ]; then
    dirnames="example"
    # so, there should be:
    # - a directory called "example/" (for images the notebook might generate)
    # - "example.rst" that uses "example_nb.rst" (see below)
    # - the actual notebook "example_nb.ipynb"
    # - once you run this script, you'll get "example_nb.rst"
else
    dirnames=$@
fi

echo $dirnames
# exit 2

for dirname in $dirnames
do
    #cd $dirname
    # jupyter nbconvert --to rst $dirname"_nb.ipynb" \
    jupyter nbconvert --to rst --template tuto_rst $dirname"_nb.ipynb" \
    --TagRemovePreprocessor.enabled=True \
    --TagRemovePreprocessor.remove_cell_tags="['remove_cell']" \
    --TagRemovePreprocessor.remove_input_tags="['remove_input']" \
    --TemplateExporter.extra_template_basedirs="['./templates']"
    #cd ..
done
# --HighlightMagicsPreprocessor.enabled=True

# substitute ! in front of CLI commands with a space
for fname in *_nb.rst
do
    echo $fname
    sed -i -r "s/ \!/ /g" $fname
done

# we'd like to have these code blocks in the converted .rst files:
# for bash cells:
# .. code:: bash
# for bash output:
# .. code-block:: text
#
# The files in "templates/tuto_rst" will take care of that
# (the normal rst template is in "~/.local/share/jupyter/nbconvert/templates/rst/")
# for more info, see: https://nbconvert.readthedocs.io/en/latest/customizing.html#where-are-nbconvert-templates-installed
