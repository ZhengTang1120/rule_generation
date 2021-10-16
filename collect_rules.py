import json
from collections import defaultdict
import networkx as nx
from networkx.algorithms import community
from math import log


from itertools import combinations

import numpy as np


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


def rules_with_out_golds(origin, model_output):
    # In this case, we do not have access to the gold labels, so we are relying on predicted labels
    assert(len(model_output)==len(origin))
    subjects = defaultdict(set)
    objects = defaultdict(set)
    d = defaultdict(set)
    candidates = defaultdict(list)
    for i, item in enumerate(model_output):
        g, e = build_graph(origin[i])
        tokens = ['ROOT'] + origin[i]['token']
        postags = ['ROOT'] + origin[i]['stanford_pos']
        
        if item['predicted_label'] != 'no_relation':#== item['gold_label']:#
            if sum(item['predicted_tags']) != 0 and sum(item['gold_tags']) == 0:
                subj = [i for i, w in enumerate(item['raw_words']) if item['subj'][i]==1]
                obj = [i for i, w in enumerate(item['raw_words']) if item['obj'][i]==1]
                triggers = [i for i, w in enumerate(item['raw_words']) if item['predicted_tags'][i] == 1 and item['subj'][i]!=1 and item['obj'][i]!=1 and i!=0]
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

                    subjects[item['predicted_label']].add(origin[i]['subj_type'])
                    objects[item['predicted_label']].add(origin[i]['obj_type']) 
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
                        candidates[item['gold_label']] += [l]

    return candidates

def rules_with_corrects(origin, model_output):
    # In this case, we have access to gold labels
    assert(len(model_output)==len(origin))
    subjects = defaultdict(set)
    objects = defaultdict(set)
    d = defaultdict(set)
    candidates = defaultdict(list)
    for i, item in enumerate(model_output):
        g, e = build_graph(origin[i])
        tokens = ['ROOT'] + origin[i]['token']
        postags = ['ROOT'] + origin[i]['stanford_pos']
        
        if item['predicted_label'] == item['gold_label']:
            if sum(item['predicted_tags']) != 0 and sum(item['gold_tags']) == 0:
                subj = [i for i, w in enumerate(item['raw_words']) if item['subj'][i]==1]
                obj = [i for i, w in enumerate(item['raw_words']) if item['obj'][i]==1]
                triggers = [i for i, w in enumerate(item['raw_words']) if item['predicted_tags'][i] == 1 and item['subj'][i]!=1 and item['obj'][i]!=1 and i!=0]
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

    return candidates

def save_rule_dict(candidates, saved_dir):
                
    output = dict()
    total = 0
    for label in candidates:
        cands = candidates[label]
        label = label.replace('/', '_slash_')
        output[label] = defaultdict(list)
        for c in cands:
            trigger = c[0]
            subj = c[2]
            obj = c[3]

            output[label][trigger].append({'subj':subj, 'obj':obj})
            total += 1
    # print (total)
    print (json.dumps(output))



    with open('master.yml','w') as f:
        for label in subjects:
            count = 0
            for subj in subjects[label]:
                for obj in objects[label]:
                    subj = subj[0]+subj[1:].lower()
                    obj = obj[0]+obj[1:].lower()
                    f.write('''
      - import: grammars_dev_pred/%s.yml
        vars:
          label: %s
          rulepriority: "3+"
          subject_type: SUBJ_%s
          object_type: OBJ_%s
          count: "%d"
      '''%(label.replace('/', '_slash_')+'_unit', label, subj, obj, count))
                    count += 1


if __name__ == "__main__":

    model_output = json.load(open('/Users/zheng/Documents/GitHub/tacred_odin/output_02_dev_best_model.json'))
    origin = json.load(open('/Users/zheng/Documents/GitHub/syn-GCN/tacred/data/json/dev.json'))

    




