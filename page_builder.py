import os

from sugar.datastore import datastore

tfile = open('templates', 'r')
templates = tfile.read()
tfile.close()

def fill_out_template(template, content):
  template = templates.split('#!%s\n' % template)[1].split('\n!#')[0]
  for x in content.keys():
    template = template.replace('{%s}' % x, content[x])
  return template
  
def build_journal():
  objects_starred, no = datastore.find({'keep': '1'})
  print objects_starred, no

  objects = [{'file': 'a', 'name': 'No Te Va Gustar - A las nueve', 'icon': 'audio-x-generic.svg'}, 
             {'file': 'b', 'name': 'Perla jugando con el gato BOB', 'icon': 'image.svg'}]
             
  objects_html = ''
  for o in objects:
    objects_html += '%s' % fill_out_template('object', o)
    
  print fill_out_template('index', {'nick': 'Agus', 'objects': objects_html})
  
build_journal()
