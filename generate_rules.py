import json

file = json.load(open('rules_train.json'))

total = 0

for relation in file:
    with open('%s_unit.yml'%relation, 'w') as f:
        count = 0
        for trigger in file[relation]:
            rules = [r for r in file[relation][trigger]]
            relation = relation.replace('/', '_slash_')
            for rule in rules:
                f.write('''
- name: ${label}_${count}_%d
  label: ${label}
  priority: ${rulepriority}
  pattern: |
    trigger =  %s
    subject: ${subject_type} = %s
    object: ${object_type} = %s\n'''%(count, trigger, ' '.join(rule['subj']), ' '.join(rule['obj'])))
                count += 1
                total += 1

print (total)
