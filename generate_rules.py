import json

file = json.load(open('rules_test_no_filter_new.json'))
good_rules = None#json.load(open('rules_w_prec_greater_60_new.json'))

total = 0

for relation in file:
    # if relation.replace('_slash_', '/') not in good_rules:
    #     print ("remove: ", relation)
    if good_rules and relation.replace('_slash_', '/') not in good_rules:
        # print (file[relation])
        continue
    if good_rules:
        current_rules = sorted(good_rules[relation.replace('_slash_', '/')], key=lambda k: len(good_rules[relation.replace('_slash_', '/')][k]), reverse=True)
        if len(current_rules)>1:
            print (relation, current_rules)
    with open('%s_unit.yml'%relation, 'w') as f:
        count = 0
        for trigger in file[relation]:
            rules = [r for r in file[relation][trigger]]
            relation = relation.replace('/', '_slash_')
    
            for rule in rules:
                # if good_rules==None or count in good_rules[relation.replace('_slash_', '/')][current_rules[0]]:
                try:
                    f.write('''
- name: ${label}_${count}_%d
  label: ${label}
  priority: ${rulepriority}
  pattern: |
    trigger =  %s
    subject: ${subject_type} = %s
    object: ${object_type} = %s\n'''%(count, trigger, ' '.join(rule['subj']), ' '.join(rule['obj'])))
                    total += 1
                except UnicodeEncodeError:
                    pass
                if good_rules and len(current_rules)>1:
                    for c in current_rules[1:]:
                        if count in good_rules[relation.replace('_slash_', '/')][c]:
                            f.write('''
- name: ${label}_%s_%d
  label: ${label}
  priority: ${rulepriority}
  pattern: |
    trigger =  %s
    subject: ${subject_type} = %s
    object: ${object_type} = %s\n'''%(c, count, trigger, ' '.join(rule['subj']), ' '.join(rule['obj'])))
                            total += 1
                count += 1

print (total)
