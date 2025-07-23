"""
Module: render
Renders results to CLI table or CSV/JSON/Markdown/Postman files.
"""
from tabulate import tabulate
import csv
import json

FIELDS = ['endpoint','method','confidence','module','controller',
          'params','detailed_params','reason','line','locations']

def render_cli(results):
    headers = [h.replace('_',' ').title() for h in FIELDS]
    rows = [
        [
            r['endpoint'],
            r['method'] if isinstance(r['method'],str) else ",".join(r['method']),
            f"{r['confidence']}%",
            r['module'],
            r['controller'],
            ",".join(r['params']),
            ",".join(r['detailed_params']),
            r['reason'],
            r['line'],
            r['locations'],
        ] for r in results
    ]
    print(tabulate(rows, headers=headers, tablefmt='github'))

def render_file(results, path, fmt):
    if fmt == 'csv':
        with open(path,'w',newline='') as f:
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            for r in results:
                writer.writerow([
                    r['endpoint'],
                    r['method'] if isinstance(r['method'],str) else ",".join(r['method']),
                    r['confidence'],
                    r['module'],
                    r['controller'],
                    "|".join(r['params']),
                    "|".join(r['detailed_params']),
                    r['reason'],
                    r['line'],
                    r['locations'],
                ])
    elif fmt == 'json':
        ordered = [{k:r.get(k) for k in FIELDS} for r in results]
        with open(path,'w') as f:
            json.dump(ordered,f,indent=2)
    elif fmt == 'markdown':
        rows = [
            [
                r['endpoint'],
                r['method'] if isinstance(r['method'],str) else ",".join(r['method']),
                f"{r['confidence']}%",
                r['module'],
                r['controller'],
                ",".join(r['params']),
                ",".join(r['detailed_params']),
                r['reason'],
                r['line'],
                r['locations'],
            ] for r in results
        ]
        md = tabulate(rows, headers=headers, tablefmt='github')
        with open(path,'w') as f:
            f.write(md)
    elif fmt == 'postman':
        items = []
        for r in results:
            methods = [r['method']] if isinstance(r['method'],str) else r['method']
            for m in methods:
                items.append({
                    "name": r['endpoint'],
                    "request":{
                        "method":m,
                        "header":[],
                        "url":{
                            "raw":"{{baseUrl}}"+r['endpoint'],
                            "host":["{{baseUrl}}"],
                            "path":r['endpoint'].strip('/').split('/')
                        },
                        "description":r['locations']
                    }
                })
        collection = {
            "info":{
                "name":"Discovered Endpoints",
                "schema":"https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item":items
        }
        with open(path,'w') as f:
            json.dump(collection,f,indent=2)