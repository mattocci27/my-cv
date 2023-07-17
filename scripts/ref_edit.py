import re
import sys
author = sys.argv[1]

print(author)

input_filename = 'outputs/ref_output.md'
output_filename = 'outputs/ref_output_edit.md'

with open(input_filename, 'r', encoding = 'utf-8') as input_file:
    md_file = input_file.read()

# Remove single line breaks
md_file = re.sub(r'(?<!\n)\n(?!\n)', ' ', md_file)

refs = re.findall(r'<span class="csl-left-margin">(.*?)<\/span>.*?<span class="csl-right-inline">(.*?)<\/span>', md_file, re.MULTILINE | re.DOTALL)


formatted_refs = ''
for ref in refs:
    updated_ref = ref[1].replace(author, f'**{author}**')
    updated_ref = re.sub(r',\s*doi:\[(.*?)\]\((.*?)\)', r' [[doi]](\2)', updated_ref)
    formatted_refs += f'{ref[0]} {updated_ref}\n\n'

with open(output_filename, 'w') as output_file:
    output_file.write(formatted_refs)
