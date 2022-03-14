# snapshots usw hab ich hier jetzt schon mal erstellt, es geht los ab generate_core_data_set()
from tokenize import Name
from model.UiDataModel import TerminologyEntry, TermCode
import os
import json
from geccoToUIProfiles import create_terminology_definition_for, get_gecco_categories, IGNORE_CATEGORIES, \
    MAIN_CATEGORIES, IGNORE_LIST, \
    get_specimen, get_consent, resolve_terminology_entry_profile, get_ui_profiles

# Name aus der package.json aus jedem Profil - bzw im Ordnernamen ohne #
DKTK = "de.dktk.oncology 1.1.1"
core_data_sets = [DKTK] # only process dktk folder in resources/core_data_sets


def generate_core_data_set():
    core_data_set_modules = []
    print("core_data_sets: ", core_data_sets)
    for data_set in core_data_sets:
        print("data_set: ", data_set)
        module_name = data_set.split(' ')[0].split(".")[-1].capitalize()
        print("module_name extracted from filename: ", module_name)
        module_code = TermCode("mii.abide", module_name, module_name)       # System?? was anderes? was wird daduch beeinfluss
        module_category_entry = TerminologyEntry([module_code], "Category", selectable=False,  leaf=False)
        data_set = data_set.replace(" ", "#")
        print("data_set = ", data_set)
        #test all available elements in dktk folder
        for snapshot in [f"resources/core_data_sets/{data_set}/package/{f.name}" for f in
                    os.scandir(f"resources/core_data_sets/{data_set}/package/") if
                    not f.is_dir() and "-snapshot" in f.name]:
            with open(snapshot, encoding="UTF-8") as json_file:
                json_data = json.load(json_file)
                if (kind := json_data.get("kind")) and (kind == "logical"):
                        print("kind == logical, Json url: %s", json_data.get("url"))
                        continue
                if resource_type := json_data.get("type"):
                    if resource_type == "Bundle": 
                        print("resourcetype == Bundle, Json url: %s", json_data.get("url"))
                        continue
                    elif resource_type == "Extension":
                        print("resourcetype == Extension, Json url: %s", json_data.get("url"))
                        continue
                name = json_data.get("name")
                print("from function: " + __name__ , "name: ", name)
                # das hier erstmal weglassen, kp was das soll
                # module_element_name = remove_resource_name(json_data.get("name"))
                # if module_element_name in IGNORE_LIST:
                #     continue
                module_element_code = TermCode("mii.abide", name, name)
                #module_element_code = TermCode("mii.abide", module_element_name, module_element_name)
                module_element_entry = TerminologyEntry([module_element_code], "Category", selectable=False,
                                                        leaf=False)
                resolve_terminology_entry_profile(module_element_entry,
                data_set=f"resources/core_data_sets/{data_set}/package")


generate_core_data_set()

def do_nothing(_profile_data, _terminology_entry, _element):
    pass

def print_cornercase(_profile_data, _terminology_entry, _element):
    print("corner_case")

#maybe I have different corner cases or none at all
corner_cases = {
    "Age": print_cornercase, #translate_age,
    "BloodPressure": print_cornercase, #translate_blood_pressure,
    "DependenceOnVentilator": print_cornercase, #translate_dependency_on_ventilator,
    "DoNotResuscitateOrder": print_cornercase, #translate_resuscitation,
    "EthnicGroup": print_cornercase #translate_ethnic_group,
}

non_corner_cases = {
    
}