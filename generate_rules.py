import json

train = json.load(open('rules_train.json'))
dev = json.load(open('rules_dev_pred.json'))

total = 0

for relation in dev:
    with open('%s_unit.yml'%relation, 'w') as f:
        count = 0
        for trigger in dev[relation]:
            rules = [r for r in dev[relation][trigger]]
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
