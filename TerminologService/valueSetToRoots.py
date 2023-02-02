import bisect
import requests
import locale
import os
import json
from requests_pkcs12 import get, post

from sortedcontainers import SortedSet

from model.UiDataModel import TermCode, TerminologyEntry

ONTOSERVER = os.environ.get('ONTOLOGY_SERVER_ADDRESS')
PKCS12_PW = os.environ.get('PKCS12_PW')
#locale.setlocale(locale.LC_ALL, 'de_DE')


def expand_value_set(url):
    term_codes = SortedSet()
    print("ONTOSERVER: ", ONTOSERVER)
    print("REQUEST STRING: ", ONTOSERVER + f"/ValueSet/$expand?url={url}")
    response = get(ONTOSERVER + f"/ValueSet/$expand?url={url}", pkcs12_filename='P:\Zertifikate\DFN\Jasmin_Ziegler_2022-09-22.p12', pkcs12_password=PKCS12_PW)
    #response = requests.get(ONTOSERVER + f"/ValueSet/$expand?url={url}", verify=True)  # add verify=False here if you are whitelisted and to not have a SSL certificate
    
    if response.status_code == 200:
        value_set_data = response.json()
        global_version = None
        for parameter in value_set_data["expansion"]["parameter"]:
            if parameter["name"] == "version":
                global_version = parameter["valueUri"].split("|")[-1]
        if "contains" not in value_set_data["expansion"]:
            print(f"{url} is empty")
            return term_codes
        for contains in value_set_data["expansion"]["contains"]:
            system = contains["system"]
            code = contains["code"]
            display = contains["display"]
            if "version" in contains:
                version = contains["version"]
            else:
                version = global_version
            # ONLY TAKE ONCOLOGICAL CODES HERE - this is hacky and not nice 
            # wieder ausgemacht, damit in Diagnose auch andere Diagnosen vorkommen
            # jetzt kamen alle Diagnosen auch in Primärdiagnose vor... da will ich natürlich nur die onkologischen
            if 'bfarm/icd-10-gm' in url:
                if "C" in code or "D0" in code or "D1" in code or "D2" in code or "D3" in code or "D4" in code:
                #if "C1" in code: #only test for C1 because it takes ages # - test for some
                    term_code = TermCode(system, code, display, version)
                    term_codes.add(term_code)
            else:
                term_code = TermCode(system, code, display, version)
                term_codes.add(term_code)
            # term_code = TermCode(system, code, display, version)
            # term_codes.add(term_code)
            #onco_icd_codes = ["C", "C61"]
            #if "C" in code or "D0" in code or "D1" in code or "D2" in code or "D3" in code or "D4" in code: # - test for some
                #print("code", code)
            
    print(len(term_codes))
    return term_codes


def create_vs_tree(canonical_url):    
    create_concept_map()
    vs = expand_value_set(canonical_url)
    #print(vs)
    vs_dict = {term_code.code: TerminologyEntry([term_code], leaf=True, selectable=True) for term_code in vs}
    #print(vs_dict)
    closure_map_data = get_closure_map(vs)
    #print("here is the closure_map_data: ", closure_map_data)
    if "group" in closure_map_data:
        for group in closure_map_data["group"]:
            subsumption_map = group["element"]
            subsumption_map = {item['code']: [target['code'] for target in item['target']] for item in subsumption_map}
            # remove non direct parents
            for code, parents in subsumption_map.items():
                if len(parents) == 0:
                    continue
                else:
                    direct_parents(parents, subsumption_map)
            for node, parents, in subsumption_map.items():
                for parent in parents:
                    bisect.insort(vs_dict[parent].children, vs_dict[node])
                    vs_dict[node].root = False
                    vs_dict[parent].leaf = False
    #das ist die lange liste 
    print("print what is returned here: ", sorted([term_code for term_code in vs_dict.values() if term_code.root]))
    return sorted([term_code for term_code in vs_dict.values() if term_code.root])

def create_concept_map():
    body = {
        "resourceType": "Parameters",
        "parameter": [{
            "name": "name",
            "valueString": "closure-test"
        }]
    }
    headers = {"Content-type": "application/fhir+json"}
    #requests.post(ONTOSERVER + "/$closure", json=body, headers=headers, verify=True)  # add verify=False here if you are whitelisted and do not have a SSL certificate
    post(ONTOSERVER + "/$closure", json=body, headers=headers, pkcs12_filename='P:\Zertifikate\DFN\Jasmin_Ziegler_2022-09-22.p12', pkcs12_password=PKCS12_PW)

def get_closure_map(term_codes):
    body = {"resourceType": "Parameters",
            "parameter": [{"name": "name", "valueString": "closure-test"}]}
    for term_code in term_codes:
        #print("TERMCODE: ", term_code)
        body["parameter"].append({"name": "concept",
                                  "valueCoding": {
                                      "system": f"{term_code.system}",
                                      "code": f"{term_code.code}",
                                      "display": f"{term_code.display}",
                                      "version": f"{term_code.version}"
                                  }})
        #print("BODY: ", body) #- this takes ages if many term codes
    headers = {"Content-type": "application/fhir+json"}
    request_string = ONTOSERVER + "/$closure"
    print("request_string: ", request_string) 
    #pkcs12_filename='P:\Zertifikate\DFN\Jasmin_Ziegler_2022-09-22.p12', pkcs12_password='JasminZ1')
    #response = requests.post(request_string, json=body, headers=headers, verify=True, cert=('P:\Zertifikate\DFN\myCert.crt', 'P:\Zertifikate\DFN\myKey.key')) #'P:\Zertifikate\DFN\cert-12172714172390989908652289883.pem') #'/p/Zertifikate/DFN/cert-12172714172390989908652289883.pem' # add verify=False if you are whitelistes and do not have a SSL certificate
    #use requests_pkcs12 package
    response = post(request_string, json=body, headers=headers, pkcs12_filename='P:\Zertifikate\DFN\Jasmin_Ziegler_2022-09-22.p12', pkcs12_password=PKCS12_PW)
    if response.status_code == 200:
        print("success - closure response status code 200")
        closure_response = response.json()
        #with open("ui-profiles/closure-response-test.json", "w") as outfile:
        #    json.dump(closure_response, outfile)
    else:
        raise Exception(response.content)
    return closure_response


def direct_parents(parents, input_map):
    parents_copy = parents.copy()
    for parent in parents_copy:
        if parent in input_map:
            parent_parents = input_map[parent]
            for elem in parents_copy:
                if elem in parent_parents and elem in parents:
                    parents.remove(elem)


def value_set_json_to_term_code_set(response):
    term_codes = SortedSet()
    if response.status_code == 200:
        value_set_data = response.json()
        if "expansion" in value_set_data and "contains" in value_set_data["expansion"]:
            for contains in value_set_data["expansion"]["contains"]:
                system = contains["system"]
                code = contains["code"]
                display = contains["display"]
                version = None
                if "version" in contains:
                    version = contains["version"]
                term_code = TermCode(system, code, display, version)
                term_codes.add(term_code)
    return term_codes

# if __name__ == "__main__":    
#     create_concept_map()
#     term_code_c91_5 = TermCode("http://fhir.de/CodeSystem/bfarm/icd-10-gm", "C91.5", "Adulte(s) T-Zell-Lymphom/Leukämie (HTLV-1-assoziiert)", "2022")
#     term_code_c91_51 = TermCode("http://fhir.de/CodeSystem/bfarm/icd-10-gm", "C91.51", "Adulte(s) T-Zell-Lymphom/Leukämie (HTLV-1-assoziiert) : In kompletter Remission", "2022")
#     print(get_closure_map([term_code_c91_5, term_code_c91_51]))
    