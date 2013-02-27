import os, sys

if len(sys.argv) <= 1:
  raise SystemExit(__doc__)

for input in sys.argv[1:]:
  if not input.endswith('.svg'):
      print 'skipping "%s": it is not an svg file' % input
      continue

  output = input.replace('.svg', '.png')
  # Convert using inkscape
  if os.system('inkscape --export-png="%s"  --file="%s"' % (output, input)) != 0:
    print 'inkscape png conversion fails'
    sys.exit(1)

