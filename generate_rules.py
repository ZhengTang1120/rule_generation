import json

file = json.load(open('rules_conll04_test.json'))
good_rules = json.load(open('conll04_rules_w_prec_greater_60.json'))
# rule_entity_map = {"org:founded_by": {"0": ["Organization", "Person"]}, "org:alternate_names": {"0": ["Organization", "Organization"], "1": ["Organization", "Misc"]}, "per:children": {"0": ["Person", "Person"]}, "per:title": {"0": ["Person", "Title"]}, "per:siblings": {"0": ["Person", "Person"]}, "per:age": {"0": ["Person", "Number"], "1": ["Person", "Duration"]}, "per:cities_of_residence": {"0": ["Person", "City"], "1": ["Person", "Location"]}, "per:employee_of": {"0": ["Person", "Organization"]}, "per:stateorprovinces_of_residence": {"0": ["Person", "State_or_province"], "1": ["Person", "Location"]}, "per:countries_of_residence": {"0": ["Person", "Country"], "1": ["Person", "Nationality"], "2": ["Person", "Location"]}, "org:top_members/employees": {"0": ["Organization", "Person"]}, "org:members": {"0": ["Organization", "Organization"], "1": ["Organization", "Country"]}, "org:country_of_headquarters": {"0": ["Organization", "Country"], "1": ["Organization", "Location"]}, "per:spouse": {"0": ["Person", "Person"]}, "org:number_of_employees/members": {"0": ["Organization", "Number"]}, "org:parents": {"0": ["Organization", "Organization"]}, "org:subsidiaries": {"0": ["Organization", "Organization"], "1": ["Organization", "Location"]}, "per:origin": {"0": ["Person", "Country"], "1": ["Person", "Nationality"]}, "per:date_of_death": {"0": ["Person", "Date"]}, "org:website": {"0": ["Organization", "Url"]}, "org:shareholders": {"0": ["Organization", "Person"], "1": ["Organization", "Organization"]}, "per:alternate_names": {"0": ["Person", "Person"], "1": ["Person", "Misc"]}, "per:parents": {"0": ["Person", "Person"]}, "per:schools_attended": {"0": ["Person", "Organization"]}, "org:city_of_headquarters": {"0": ["Organization", "City"], "1": ["Organization", "Location"]}, "per:cause_of_death": {"0": ["Person", "Cause_of_death"]}, "org:stateorprovince_of_headquarters": {"0": ["Organization", "State_or_province"], "1": ["Organization", "Location"]}, "per:city_of_death": {"0": ["Person", "City"], "1": ["Person", "Location"]}, "per:stateorprovince_of_death": {"0": ["Person", "State_or_province"], "1": ["Person", "Location"]}, "org:founded": {"0": ["Organization", "Date"]}, "per:country_of_birth": {"0": ["Person", "Country"]}, "per:religion": {"0": ["Person", "Religion"]}, "per:date_of_birth": {"0": ["Person", "Date"]}, "per:other_family": {"0": ["Person", "Person"]}, "per:city_of_birth": {"0": ["Person", "City"], "1": ["Person", "Location"]}, "org:political/religious_affiliation": {"0": ["Organization", "Religion"], "1": ["Organization", "Ideology"]}, "per:charges": {"0": ["Person", "Criminal_charge"]}, "per:stateorprovince_of_birth": {"0": ["Person", "State_or_province"]}, "org:member_of": {"0": ["Organization", "Organization"]}, "org:dissolved": {"0": ["Organization", "Date"]}}
rule_entity_map = {"Work_For": {"0": ["Person", "Organization"]}, "Located_In": {"0": ["Location", "Location"]}, "Live_In": {"0": ["Person", "Location"]}, "Kill": {"0": ["Person", "Person"]}, "OrgBased_In": {"0": ["Organization", "Location"]}}
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
                if good_rules==None or count in good_rules[relation.replace('_slash_', '/')][current_rules[0]]:
                    f.write('''
- name: ${label}_${count}_%d
  label: ${label}
  priority: ${rulepriority}
  pattern: |
    trigger =  %s
    subject: ${subject_type} = %s
    object: ${object_type} = %s\n'''%(count, trigger, ' '.join(rule['subj']), ' '.join(rule['obj'])))
                    total += 1
                if good_rules and len(current_rules)>1:
                    for c in current_rules[1:]:
                        if count in good_rules[relation.replace('_slash_', '/')][c]:
                            f.write('''
- name: ${label}_%s_%d
  label: ${label}
  priority: ${rulepriority}
  pattern: |
    trigger =  %s
    subject: %s = %s
    object: %s = %s\n'''%(c, count, trigger, rule_entity_map[relation.replace('_slash_', '/')][c][0], ' '.join(rule['subj']), rule_entity_map[relation.replace('_slash_', '/')][c][1], ' '.join(rule['obj'])))
                            total += 1
                count += 1

print (total)
