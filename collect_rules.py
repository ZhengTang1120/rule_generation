import json
import csv
import re
from collections import defaultdict
import networkx as nx
from networkx.algorithms import community
from math import log


from itertools import combinations

import numpy as np

from termcolor import colored


tags = dict()
with open('tags.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        label = row[0]
        regexes = [i for i in row[1:] if i!='']
        tags[label] = "(" + ")|(".join(regexes) + ")"

def argmax(l):
    return max(enumerate(l), key=lambda x: x[1])[0]

def build_graph(d):
    edge_dict = defaultdict(dict)
    G = nx.Graph()
    tokens = ['ROOT'] + d['token']
    heads = d['stanford_head']
    deprel= d['stanford_deprel']
    G.add_nodes_from([i for i in range(len(tokens))])
    for i in range(1, len(tokens)):
        G.add_edge(heads[i-1], i)
        edge_dict[heads[i-1]][i] = deprel[i-1]
        edge_dict[i][heads[i-1]] = "<"+deprel[i-1]
    return G, edge_dict

def trigger_stats(candidates, origin, model_output):
    d = defaultdict(dict)
    l = 0
    c = 0
    assert(len(model_output)==len(origin))
    subjects = defaultdict(list)
    objects = defaultdict(list)
    lineid2rule = defaultdict(dict) 
    for i, item in enumerate(model_output):
        g, e = build_graph(origin[i])
        tokens = ['ROOT'] + origin[i]['token']
        postags = ['ROOT'] + origin[i]['stanford_pos']
        if item['predicted_label'] != 'no_relation':
            if len(item['predicted_tags']) != 0 and len(item['gold_tags']) == 0:
                c += 1
                subj = list(range(origin[i]['subj_start']+1, origin[i]['subj_end']+2))
                obj = list(range(origin[i]['obj_start']+1, origin[i]['obj_end']+2))
                triggers = [j+1 for j, w in enumerate(origin[i]['token']) if j in item['predicted_tags'] and j+1 not in subj and j+1 not in obj]
                trigger = ''
                prev = -1
                l += len(triggers)
                for j in triggers:
                    if "VB" in postags[j]:
                        tag = "VB*"
                    elif "NN" in postags[j]:
                        tag = "NN*"
                    else:
                        tag = postags[j]
                    if tag in d[item['predicted_label']]:
                        d[item['predicted_label']][tag] += 1
                    else:
                        d[item['predicted_label']][tag] = 1
                #     if prev == -1:
                #         trigger += '"%s"'%tokens[j]
                #     elif j - prev == 1:
                #         trigger += ' ' + '"%s"'%tokens[j]
                #     else:
                #         trigger += '(/.+/)*' + '"%s"'%tokens[j]
                #     prev = j
                # print (trigger)
    # print (l/c)
    # res = dict()
    # for x in d:
    #     res[x] = {k: v for k, v in sorted(d[x].items(), key=lambda item: item[1], reverse=True)[:5]}
    ans = defaultdict(int)
    for x in d:
        for l in d[x]:
            if d[x][l] >= 10:
                ans[l] += 1
    print (json.dumps({k: v for k, v in sorted(ans.items(), key=lambda item: item[1], reverse=True)}))

def rules_with_out_golds(candidates, origin, model_output):
    # In this case, we do not have access to the gold labels, so we are relying on predicted labels
    assert(len(model_output)==len(origin))
    subjects = defaultdict(list)
    objects = defaultdict(list)
    lineid2rule = defaultdict(dict) 
    for i, item in enumerate(model_output):
        g, e = build_graph(origin[i])
        tokens = ['ROOT'] + origin[i]['token']
        postags = ['ROOT'] + origin[i]['stanford_pos']
        if item['predicted_label'].startswith('per'):
            subj_type = 'PERSON'
        else:
            subj_type = 'ORGANIZATION'
        if item['predicted_label'] != 'no_relation' and subj_type == origin[i]['subj_type']:#== item['gold_label']:#
            if len(item['predicted_tags']) != 0 and len(item['gold_tags']) == 0:
                subj = list(range(origin[i]['subj_start']+1, origin[i]['subj_end']+2))
                obj = list(range(origin[i]['obj_start']+1, origin[i]['obj_end']+2))
                triggers = [j+1 for j, w in enumerate(origin[i]['token']) if j in item['predicted_tags'] and j+1 not in subj and j+1 not in obj]
                if triggers:
                    sp = []
                    op = []
                    trigger_head = triggers[argmax([g.degree[t] for t in triggers])]
                    # subj_head = subj[argmax([g.degree[s] for s in subj])]
                    # obj_head = obj[argmax([g.degree[o] for o in obj])]
                    # sp = nx.shortest_paths(g, source=trigger_head, target=subj_head)
                    # op = nx.shortest_paths(g, source=trigger_head, target=obj_head)
                    for t in triggers:
                        if re.match(tags[item['predicted_label']], postags[t]):
                            for s in subj:
                                temp1 = nx.shortest_path(g, t, s)
                                for o in obj:
                                    temp2 = nx.shortest_path(g, t, o)
                                    if len(temp1+temp2)<len(sp+op) or sp == []:
                                        sp = temp1
                                        op = temp2
                                        trigger_head = t
                    if origin[i]['subj_type'] not in subjects[item['predicted_label']]:
                        subjects[item['predicted_label']].append(origin[i]['subj_type'])
                    if origin[i]['obj_type'] not in objects[item['predicted_label']]:
                        objects[item['predicted_label']].append(origin[i]['obj_type']) 
                    trigger = ''
                    prev = -1
                    for j in triggers:
                        if prev == -1:
                            trigger += '"%s"'%tokens[j]
                        elif j - prev == 1:
                            trigger += ' ' + '"%s"'%tokens[j]
                        else:
                            trigger += '(/.+/)*' + '"%s"'%tokens[j]
                        prev = j
                        
                    l = [trigger, [postags[j] for j in triggers], [e[sp[j]][sp[j+1]] for j in range(len(sp)-1)], [e[op[j]][op[j+1]] for j in range(len(op)-1)]]
                    
                    if l not in candidates[item['predicted_label']] and len(triggers)<=3 and len(sp)!=0 and len(op)!=0:
                        candidates[item['predicted_label']] += [l]
                    if len(triggers)<=3 and len(sp)!=0 and len(op)!=0:
                        if candidates[item['predicted_label']].index(l) in lineid2rule[item['predicted_label']]:
                            lineid2rule[item['predicted_label']][candidates[item['predicted_label']].index(l)].append(i)
                        else:
                            lineid2rule[item['predicted_label']][candidates[item['predicted_label']].index(l)] = [i]

    return candidates, subjects, objects, lineid2rule

def rules_with_corrects(candidates, origin, model_output):
    # In this case, we have access to gold labels
    assert(len(model_output)==len(origin))
    subjects = defaultdict(set)
    objects = defaultdict(set)
    d = defaultdict(set)
    
    for i, item in enumerate(model_output):
        g, e = build_graph(origin[i])
        tokens = ['ROOT'] + origin[i]['token']
        postags = ['ROOT'] + origin[i]['stanford_pos']
        # if item['predicted_label'] != 'no_relation':
        #     ts = origin[i]['token']
        #     ts = [colored(w, "blue") if j in list(range(origin[i]['subj_start'], origin[i]['subj_end']+1)) else w for j, w in enumerate(ts)]
        #     ts = [colored(w, "yellow") if j in list(range(origin[i]['obj_start'], origin[i]['obj_end']+1)) else w for j, w in enumerate(ts)]
        #     ts = [colored(w, "red") if j in item['predicted_tags'] else w for j, w in enumerate(ts)]
        #     print (' '.join(ts))
        # continue
        if item['predicted_label'] == item['gold_label']:
            if len(item['predicted_tags']) != 0 and len(item['gold_tags']) == 0:
                subj = list(range(origin[i]['subj_start']+1, origin[i]['subj_end']+2))
                obj = list(range(origin[i]['obj_start']+1, origin[i]['obj_end']+2))
                triggers = [j+1 for j, w in enumerate(origin[i]['token']) if j in item['predicted_tags'] and j+1 not in subj and j+1 not in obj]
                if triggers:
                    sp = []
                    op = []
                    trigger_head = triggers[argmax([g.degree[t] for t in triggers])]
                    # subj_head = subj[argmax([g.degree[s] for s in subj])]
                    # obj_head = obj[argmax([g.degree[o] for o in obj])]
                    # sp = nx.shortest_paths(g, source=trigger_head, target=subj_head)
                    # op = nx.shortest_paths(g, source=trigger_head, target=obj_head)
                    for t in triggers:
                        if re.match(tags[item['gold_label']], postags[t]):
                            for s in subj:
                                temp1 = nx.shortest_path(g, t, s)
                                for o in obj:
                                    temp2 = nx.shortest_path(g, t, o)
                                    if len(temp1+temp2)<len(sp+op) or sp == []:
                                        sp = temp1
                                        op = temp2
                                        trigger_head = t

                    subjects[item['gold_label']].add(origin[i]['subj_type'])
                    objects[item['gold_label']].add(origin[i]['obj_type']) 
                    trigger = ''
                    prev = -1
                    for j in triggers:
                        if prev == -1:
                            trigger += '"%s"'%tokens[j]
                        elif j - prev == 1:
                            trigger += ' ' + '"%s"'%tokens[j]
                        else:
                            trigger += '(/.+/)*' + '"%s"'%tokens[j]
                        prev = j
                        
                    l = [trigger, [postags[j] for j in triggers], [e[sp[j]][sp[j+1]] for j in range(len(sp)-1)], [e[op[j]][op[j+1]] for j in range(len(op)-1)]]
                    if l not in candidates[item['gold_label']] and len(triggers)<=3 and len(sp)!=0 and len(op)!=0:
                        candidates[item['gold_label']] += [l]

    return candidates, subjects, objects

def save_rule_dict(candidates, subjects, objects, name):
    res = defaultdict(dict)    
    output = dict()
    total = 0
    for label in candidates:
        cands = candidates[label]
        label = label.replace('/', '_slash_')
        output[label] = defaultdict(list)
        for i, c in enumerate(cands):
            trigger = c[0]
            subj = c[2]
            obj = c[3]
            if len(subj)>0 and len(obj)>0:
                output[label][trigger].append({'subj':subj, 'obj':obj})
                total += 1
    for label in output:
        label2 = label.replace('_slash_', '/')
        count = 0
        for trigger in output[label]:
            for rule in output[label][trigger]:
                count += 1
    print ("Generated %d rules."%total)
    with open('rules_%s.json'%name, 'w') as f:
        f.write(json.dumps(output))


    sod = defaultdict(dict)
    with open('master.yml','w') as f:
        for label in subjects:
            count = 0
            for subj in subjects[label]:
                for obj in objects[label]:
                    subj = subj[0]+subj[1:].lower()
                    obj = obj[0]+obj[1:].lower()
                    sod[label][subj+obj] = count
                    f.write('''
  - import: grammars_%s/%s.yml
    vars:
      label: %s
      rulepriority: "3+"
      subject_type: SUBJ_%s
      object_type: OBJ_%s
      count: "%d"
  '''%(name, label.replace('/', '_slash_')+'_unit', label, subj, obj, count))
                    count += 1
    print (json.dumps(sod))

if __name__ == "__main__":

    model_output = json.load(open('output_tagging_01_test_best_model.json'))
    origin = json.load(open('/Users/zheng/Documents/GitHub/tacred_odin/src/main/resources/data/test.json'))

    candidates = defaultdict(list)

    trigger_stats(candidates, origin, model_output)

    # candidates, subjects, objects = rules_with_out_golds(candidates, origin, model_output)

    # save_rule_dict(candidates, subjects, objects, "rules_conll04_test2")






