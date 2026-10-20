#!/usr/bin/env python3
"""Independent table-byte/typed-row/metadata comparison, V1.0."""
from collections import Counter
from decimal import Decimal
from defusedxml import ElementTree as ET
from hashlib import sha256
from itertools import zip_longest
from pathlib import Path
import json, sys, importlib.metadata

def tag(e): return e.tag.rsplit('}',1)[-1]
def encode(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',',':')).encode('utf-8')
def elem(e):
    return (tag(e), sorted(e.attrib.items()), (e.text or '').strip(), [elem(c) for c in e])

def tokenize(text,field):
    value='' if text is None else text
    dtype=field['type']
    sentinel=field['null']
    if sentinel is not None and (value == sentinel if dtype in ('char','unicodeChar') else value.strip()==sentinel.strip()):
        return ('null_declared',)
    if value=='': return ('empty',)
    if dtype in ('char','unicodeChar'): return ('char',value)
    value=value.strip()
    if not value: return ('empty',)
    if dtype in ('short','int','long','unsignedByte'): return ('int',str(int(value)))
    if dtype in ('float','double'):
        x=Decimal(value)
        return ('number',str(x.normalize()))
    raise ValueError('Unhandled type: '+str(dtype))

def snapshot(path):
    root=ET.parse(path).getroot()
    tables=[e for e in root.iter() if tag(e)=='TABLE']
    if len(tables)!=1: raise ValueError('Expected one TABLE')
    tab=tables[0]
    field_nodes=[e for e in tab if tag(e)=='FIELD']
    fields=[]
    for f in field_nodes:
        vals=[e.get('null') for e in f if tag(e)=='VALUES']
        fields.append({'name':f.get('name'),'type':f.get('datatype'),
                       'null':vals[0] if vals else None,'full':elem(f)})
    if len(fields)!=25: raise ValueError('Unexpected number of fields')
    data_nodes=[e for e in tab.iter() if tag(e)=='TABLEDATA']
    if len(data_nodes)!=1: raise ValueError('Expected TABLEDATA encoding')
    byid={};ordered_ids=[];rows=[];nulls=Counter();h=sha256();raw=sha256()
    h.update(b'STAR-VOTABLE-TABLEDATA-TYPED-V1\n')
    h.update(encode([f['full'] for f in fields])+b'\n')
    agc_index=[i for i,f in enumerate(fields) if f['name']=='AGC']
    if len(agc_index)!=1: raise ValueError('No unique AGC field')
    for line,tr in enumerate(data_nodes[0]):
        if tag(tr)!='TR': continue
        cells=[e.text for e in tr if tag(e)=='TD']
        if len(cells)!=len(fields): raise ValueError('Bad width at row '+str(line))
        canon=[tokenize(v,f) for v,f in zip(cells,fields)]
        for i,v in enumerate(canon):
            if v[0].startswith('null') or v[0]=='empty': nulls[fields[i]['name']+':'+v[0]]+=1
        key=cells[agc_index[0]]
        if not key or key in byid: raise ValueError('Missing or duplicate AGC '+str(key))
        rowhash=sha256(encode(canon)).hexdigest()
        byid[key]=rowhash
        ordered_ids.append(key)
        rows.append(rowhash)
        h.update(encode(canon)+b'\n')
        raw.update(encode(cells)+b'\n')
    metadata=[]
    def metadata_walk(e,path=''):
        if tag(e)=='TABLEDATA': return
        cur=path+'/'+tag(e)
        metadata.append((cur,sorted(e.attrib.items()),(e.text or '').strip()))
        for index,child in enumerate(e): metadata_walk(child,cur+'/'+str(index))
    metadata_walk(root)
    return {'path':str(path),'source_sha256':sha256(path.read_bytes()).hexdigest(),
        'typed_table_digest':h.hexdigest(),'raw_cells_digest':raw.hexdigest(),
        'metadata_digest':sha256(encode(metadata)).hexdigest(),
        'fields':[f['full'] for f in fields], 'field_names':[f['name'] for f in fields],
        'row_count':len(rows),'row_hashes':rows,'by_agc':byid,
        'agc_order':ordered_ids,'null_counts':dict(sorted(nulls.items())),'metadata':metadata}

def main(left,right):
    a,b=snapshot(Path(left)),snapshot(Path(right))
    changes=[{'row_1based':i,'frozen_row_sha256':x,'live_row_sha256':y}
             for i,(x,y) in enumerate(zip_longest(a['row_hashes'],b['row_hashes']),1) if x!=y]
    keyed=[k for k in sorted(set(a['by_agc'])|set(b['by_agc'])) if a['by_agc'].get(k)!=b['by_agc'].get(k)]
    md=[{'position':i,'frozen':x,'live':y}
        for i,(x,y) in enumerate(zip_longest(a['metadata'],b['metadata'])) if x!=y]
    report={'method':'STAR-VOTABLE-TABLEDATA-TYPED-V1','python':sys.version.split()[0],
            'defusedxml':importlib.metadata.version('defusedxml'),
            'comparator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'input_frozen_sha256':a['source_sha256'],'input_live_sha256':b['source_sha256'],
            'frozen_typed_sha256':a['typed_table_digest'],'live_typed_sha256':b['typed_table_digest'],
            'frozen_cell_lexical_sha256':a['raw_cells_digest'],'live_cell_lexical_sha256':b['raw_cells_digest'],
            'rows':[a['row_count'],b['row_count']],
            'field_metadata_equal':a['fields']==b['fields'],
            'row_order_equal':a['agc_order']==b['agc_order'],
            'typed_ordered_rows_equal':a['typed_table_digest']==b['typed_table_digest'],
            'keyed_row_differences':len(keyed),'first_keyed_differences':keyed[:15],
            'ordered_row_differences':len(changes),'first_ordered_differences':changes[:12],
            'nulls_equal':a['null_counts']==b['null_counts'],'nulls_frozen':a['null_counts'],'nulls_live':b['null_counts'],
            'metadata_nodes_differ':len(md),'first_metadata_differences':md[:30],
            'metadata_digests':[a['metadata_digest'],b['metadata_digest']]}
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__': main(*sys.argv[1:])
