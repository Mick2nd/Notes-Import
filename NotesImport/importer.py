'''
Created on 22.09.2021

@author: juergen@habelt-jena.de
'''
from zipfile import ZipFile
import json
import requests
from urllib import parse
from contextlib import contextmanager
import re

from logging_factory import LoggingFactory


class Importer(object):
    '''
    Responsible for importing a QNAP Notes Station archive
    '''
    REGEX_QUOTES = re.compile(r'(?<!\\)\\"')
    REGEX_UML = re.compile(r'%([a-zA-Z0-9][a-zA-Z0-9])%([a-zA-Z0-9][a-zA-Z0-9])')

    def __init__(self, refresh, archive, token, insertion):
        '''
        Constructor
        '''
        path = '.'                                                  # environ['PROJECT_LOC']
        self.logger = LoggingFactory(path).getLogger(self)

        self.refresh = refresh
        self.token = token
        self.qnap = Importer.Qnap(self, archive)
        self.joplin = Importer.Joplin(self, token, insertion)


    @contextmanager
    def exception_mgr(self):
        '''
        Context manager for exceptions
        '''
        try:
            yield self
            
        except BaseException as _:
            self.logger.exception('Exception during command execution')
        
        
    def import_it(self):
        '''
        Imports the archive
        - Extracts the relevant files from archive
        - Inserts them into Joplin by using the Joplin Data API 
        '''
        insertion_id = self.joplin._get_insertion_id()
        archive_structure = self.qnap._get_structure()
        self.logger.info(f'Inserting into: {self.joplin.insertion}')
        
        # self._probe(insertion_id)
        # return
        
        for book in archive_structure['notebooks']:                                             # all note books
            nb_name = book['nb_name']
            nb_data = self.joplin._put_folder(insertion_id, nb_name)                            # put it as folder
            nb_id = nb_data['id']
            self.logger.info(nb_name)
            self.refresh()                                                                      # refreshes the GUI
            
            for section in book['sec_list']:                                                    # all sections in note book
                sec_name = section['sec_name']
                sec_data = self.joplin._put_folder(nb_id, sec_name)                             # put it as folder
                sec_id = sec_data['id']
                self.logger.info(f'- {sec_name}')
                self.refresh()                                                                  # refreshes the GUI
            
                for note in section['note_list']:                                               # all notes in section
                    location = note['note_location']
                    note_file = self.qnap._get_note(location)
                    note_name = note_file['note_name']
                    note_content = note_file['content']
                    md = self._convert_note(location, note_content)                             # convert the content to mark down
                    resp = self.joplin._put_note(sec_id, note_name, md)                         # put the note
                    self.logger.info(f'-- {note_name}')
                    self.refresh()                                                              # refreshes the GUI
        
                    for tag in note_file['tag_list']:
                        self.joplin._put_tag(resp['id'], tag['tag_name'])
                        self.logger.info(f'--- tag: {tag["tag_name"]}')
                        self.refresh()                                                              # refreshes the GUI
        
        self.logger.info(f'Successfully imported QNAP Notes Archive: {self.qnap.archive}')
    
    
    def _probe(self, parent_id):
        '''
        Inserts a probe note
        '''
        # done:
        # 1/1/4    Identity Levi-Civita-Symbol
        # 2/1/1    Nächste Zeit
        # 1/1/1    Operator- und Matrixfunktionen
        # 2/4/5    Verkäufe ?
        # 2/4/1    Anschaffungen ?
        location = '1/4/2'          # Übersicht über Arbeiten zur Noethertheorie
        note_file = self.qnap._get_note(location)
        note_name = note_file['note_name']
        note_content = note_file['note_content']
        md = self._convert_note(location, note_content)
        resp = self.joplin._put_note(parent_id, note_name, md)
        
        for tag in note_file['tag_list']:
            self.joplin._put_tag(resp['id'], tag['tag_name'])
        
        self.logger.info('Probe successfully converted')
    
    
    class Qnap(object):
        '''
        Sub class responsible for QNAP archive extraction 
        '''
        
        def __init__(self, parent, archive):
            '''
            Constructor
            '''
            self.parent = parent
            self.archive = archive
        
        
        def _get_structure(self):
            '''
            Gets the structure file from the QNAP archive
            '''
            json_data = self._unzip('data.json')
            return json.loads(json_data.decode('utf-8'))
            
            
        def _get_note(self, location):
            '''
            Gets a note file from the QNAP archive (noteInfo.json)
            @param location: note location
            '''
            json_data = self._unzip(f'{location}/noteInfo.json')
            json_data = json_data.decode('utf-8')
            
            json_data = json_data.replace('\\\\', '~#~')                            # special handling for double backslashes
            if '~#~' in json_data:                                                  # must be handled in convert_note
                self.parent.logger.warning('There were double backslashes')

            return json.loads(json_data)        
            
            
        def _get_resource(self, location, kind, id_):
            '''
            Gets a resource file from the QNAP archive
            @param location: note location
            @param kind: kind of resource, maybe 'image' or 'attachment'
            @param id_: id of the resource, filename inside the archive
            '''
            return self._unzip(f'{location}/{kind}/{id_}')
        
        
        def _unzip(self, path):
            '''
            Un-zip a file from archive into memory
            '''
            zf = ZipFile(self.archive)
            data = zf.read(path)
            return data
    
    
    class Joplin(object):
        '''
        Sub class responsible for Joplin Data Api
        '''
        
        def __init__(self, parent, token, insertion):
            '''
            Constructor
            '''
            self.parent = parent
            self.token = token
            self.insertion = insertion
        
    
        def _get_insertion_id(self):
            '''
            Gets the Insertion Id with a GET request
            '''
            return self._search(self.insertion, 'folder')[0]['id']
            
        
        def _get_tag(self, name):
            '''
            Gets the tag with name with a GET request
            '''
            name = name.lower()
            return self._search(name, 'tag')
        
        
        def _get_resource(self, title):
            '''
            Gets the resource record(s) (json) with the given title
            '''
            lst = []
            query = { 'fields': 'id,size', 'token': self.token }
    
            for item in self._search(title, 'resource'):                            # here we get all resources with the given title
                url = f'http://localhost:41184/resources/{item["id"]}'
                resp = self._get(url, query)                                        # and we extract the required info (id, size)
                lst.append(resp)
                
            return lst
            
            
        def _put_folder(self, parent_id, title):
            '''
            Puts a folder (notebook) entry into Joplin with a POST request
            '''
            url = 'http://localhost:41184/folders'
            query = { 'token': self.token }
            data = { 'title': title, 'parent_id': parent_id }
            return self._post(url, query, data)
            
            
        def _put_note(self, parent_id, title, content):
            '''
            Puts a Mark-down note into Joplin with a POST request
            '''
            url = 'http://localhost:41184/notes'
            query = { 'token': self.token }
            data = { 'title': title, 'body': content, 'parent_id': parent_id }
            return self._post(url, query, data)
        
        
        def _put_resource(self, meta_data, content):
            '''
            Puts a resource into Joplin
            '''
            url = 'http://localhost:41184/resources'
            query = { 'token': self.token }
            return self._post_resource(url, query, meta_data, content)                  # then post it to joplin
            
        
        def _put_tag(self, note_id, name):
            '''
            Creates a tag and assigns it to the given id's note
            (Problem: does it duplicate existing tags?)
            '''
            json = self._get_tag(name)                                                  # look at existing tags
            query = { 'token': self.token }
    
            if len(json):
                json = json[0]                                                          # take the existing tag
            else:
                url = 'http://localhost:41184/tags'
                data = { 'title': name }
                json = self._post(url, query, data)                                     # create a new tag
    
            id_ = json.get('id')
            if id_:
                url = f'http://localhost:41184/tags/{id_}/notes'
                data = { 'id': note_id }
                return self._post(url, query, data)                                     # assign a note to it
            
            self.parent.logger.warning(f'No tag id acquired for tag {name}: {json}')
            return None
    
    
        def _search(self, identifier, kind):
            '''
            Searches for item(s) in Joplin database
            '''
            query = { 'query': identifier, 'type': kind, 'token': self.token }
            content = self._get('http://localhost:41184/search', query)
            return content['items']
            
        
        def _get(self, url, query):
            '''
            GET request
            '''
            query_str = parse.urlencode(query)
            query_str = self._decode_unicode(query_str)
            
            resp = requests.get(url + '?' + query_str)
            return resp.json()
        
        
        def _post(self, url, query, data):
            '''
            POST request
            '''    
            query_str = parse.urlencode(query)
            data_str = json.dumps(data)
            headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
            
            resp = requests.post(url + '?' + query_str, data = data_str, headers = headers)
            return resp.json()
        
        
        def _post_resource(self, url, query, meta_data, content):
            '''
            POST request for resources
            '''
            title = meta_data['title']
            resp = self._get_resource(title)
            for item in resp:                                                           # does the resource exist?
                if item['size'] == len(content):                                        # (title and size must agree)
                    self.parent.logger.debug(f'Existing resource detected: {title}')
                    return item
            
            query_str = parse.urlencode(query)
            meta_data_encoded = json.dumps(meta_data).encode('utf-8')
            data = (('props', (None, meta_data_encoded)), ('data', (title, content)))
            
            resp = requests.post(url + '?' + query_str, files = data)                   # otherwise add the resource
            return resp.json()
    
    
        def _decode_unicode(self, strg):
            '''
            Decodes a string with %xx%yy unicode code points
            '''
            return parse.unquote(strg)
    
        
    def _convert_note(self, location, content):
        '''
        Converts a QNAP Note in mark-down format
        @param location: location of the note
        @param content: the content of a note (raw)
        '''
        def convert_content(content, quotation = 0):
            '''
            Converts common content
            '''
            md = ''
            for item in content:
                item_md = ''
                if item['type'] == 'table':
                    item_md = convert_table(item)
                if item['type'] == 'paragraph':
                    item_md = convert_para(item)
                if item['type'] == 'heading':
                    item_md = convert_heading(item)
                if item['type'] == 'check_list':
                    item_md = convert_check_list(item)
                if item['type'] == 'bullet_list':
                    item_md = convert_list(item, '- ')
                if item['type'] == 'ordered_list':
                    item_md = convert_list(item, '1. ')
                if item['type'] == 'horizontal_rule':
                    item_md = '---\n'
                if item['type'] == 'blockquote':
                    item_md = convert_content(item['content'], quotation + 1)
                if item['type'] == 'code_block':
                    item_md = convert_code(item)
                    
                md += '>' * quotation + item_md + '\n'
        
            return md
            
            
        def convert_table(table):
            '''
            Converts a table
            '''
            divider = ['']
            first = True
            rows = []
            
            for row in table['content']:
                assert row['type'] == 'table_row'
                cells = ['']
                
                for cell in row['content']:
                    assert cell['type'] == 'table_cell'
                    for para in cell['content']:
                        cells.append(convert_para(para))
                        
                cells.append('')
                row_md = '|'.join(cells)
                rows.append(row_md)
                
                if first:
                    divider.extend(['-'] * len(row['content']))
                    divider.append('')
                    divider_md = '|'.join(divider)
                    rows.append(divider_md)
                    first = False
                    
            return '\n'.join(rows)
        
        
        def convert_heading(heading):
            '''
            Converts a heading
            '''
            assert heading['type'] == 'heading'
            level = heading['attrs']['level']
            txt = convert_text(heading['content'][0])
            return '#' * level + ' ' + txt
    
    
        def convert_check_list(check_list, level = 0):
            '''
            Converts a check list
            '''
            assert check_list['type'] == 'check_list'
            md = ''
            for item in check_list['content']:
                checked = 'x' if item['attrs']['checked'] else ' '
                txt = ''
                for para in item['content']:
                    txt += convert_para(para)
                    
                md += '\t' * level + f'- [{checked}] ' + txt + '\n'
                
            return md
    
    
        def convert_list(list_, pattern, level = 0):
            '''
            Converts a list (bullet or ordered)
            '''
            md = ''
            for item in list_['content']:
                for nested in item['content']:                              # assumed to be 1 item inside list_item
                    if nested['type'] == 'paragraph':
                        txt = convert_para(nested)
                        md += '\t' * level + pattern + txt + '\n'
                        
                    if nested['type'] == 'bullet_list':
                        md += convert_list(nested, '- ', level + 1)
                    if nested['type'] == 'ordered_list':
                        md += convert_list(nested, '1. ', level + 1)
                    if nested['type'] == 'check_list':
                        md += convert_check_list(nested, level + 1)
                        
            return md

            
        def convert_para(para):
            '''
            Converts a paragraph
            '''
            assert para['type'] == 'paragraph'
            md = ''
            for item in para.get('content', ''):
                if not item:
                    continue
                if item['type'] == 'text':
                    md += convert_text(item)
                if item['type'] == 'file':
                    md += convert_file(item)
                if item['type'] == 'image':
                    md += convert_file(item, 'image')
                if item['type'] == 'hard_break':
                    md += '<br/>'
            
            return md


        def convert_code(code):
            '''
            Converts a code block
            '''
            assert code['type'] == 'code_block'
            md = ''
            for item in code.get('content', ''):
                if not item:
                    continue
                if item['type'] == 'text':
                    md += convert_text(item)
            
            return '```\n' + md + '```'
        
        
        def convert_text(text):
            '''
            Converts text
            '''
            pure_text = text['text']
            marks = text.get('marks', [])
            marks_string = ''
            for mark in marks:
                if mark['type'] == 'em':
                    marks_string += '*'
                if mark['type'] == 'strong':
                    marks_string += '**'
                if mark['type'] == 'superscript':
                    marks_string += '^'
                if mark['type'] == 'subscript':
                    marks_string += '~'
                if mark['type'] == 'link':
                    href = mark['attrs']['href']
                    pure_text = f'[{pure_text}]({href})'
            
            return marks_string + pure_text + marks_string
        
        
        def convert_file(file, kind = 'attachment'):
            '''
            Converts a file entry and posts the file
            '''
            src = file['attrs']['src'].split('/')
            src = src[-1]
            title = file['attrs']['title']
            meta_data = { 'title': title }
            content = self.qnap._get_resource(location, kind, src)                      # first get the attachment from Qnap

            resp = self.joplin._put_resource(meta_data, content)            
            sign = '' if kind == 'attachment' else '!'
            
            return f'{sign}[{title}](:/{resp["id"]})'                                   # finally return the md
            

        #content = content.replace(r'\\"', '~#~').replace(r'\"', '"').replace('~#~', r'\"')
        #content = content.replace('\\\\', '~#~')
        #if '~#~' in content:
        #    self.logger.warning('There were double backslashes')
        content = content.replace(r'\"', '"')
        content = content.replace('~#~', '\\')                                          # can stem from Qnap._get_note
        content_data = json.loads(content)                                              # this is then a dictionary
        md = convert_content(content_data['content'])
    
        return md


if __name__ == '__main__':
    
    print('aaabaaa'.replace('ba', 'b'))