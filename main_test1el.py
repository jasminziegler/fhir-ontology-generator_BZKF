# snapshots usw hab ich hier jetzt schon mal erstellt, es geht los ab generate_core_data_set()
from tokenize import Name
from model.UiDataModel import TerminologyEntry, TermCode
import errno
import os
from os import path
import json
from jsonschema import validate

from model.MappingDataModel import generate_map
from geccoToUIProfiles import create_terminology_definition_for, get_gecco_categories, IGNORE_CATEGORIES, \
    MAIN_CATEGORIES, IGNORE_LIST, \
    get_specimen, get_consent, resolve_terminology_entry_profile, get_ui_profiles
from model.termCodeTree import to_term_code_node

# Name aus der package.json aus jedem Profil - bzw im Ordnernamen ohne #
DKTK = "de.dktk.oncology 1.1.1"
core_data_sets = [DKTK] # only process dktk folder in resources/core_data_sets


# FIXME:
def mkdir_if_not_exists(directory):
    if not path.isdir(f"./{directory}"):
        try:
            os.system(f"mkdir {directory}")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def generate_result_folder():
    mkdir_if_not_exists("mapping")
    mkdir_if_not_exists("csv")
    mkdir_if_not_exists("ui-profiles")


def validate_ui_profile(profile_name):
    f = open("ui-profiles/" + profile_name + ".json", 'r')
    validate(instance=json.load(f), schema=json.load(open("resources/schema/ui-profile-schema.json")))


# HIER MUSS ICH NOCHMAL RAN - wie wird das term-code-mapping-schema.json erstellt?
def generate_term_code_mapping(entries):
    map_entries = generate_map(entries)
    map_entries_file = open("mapping/" + "codex-term-code-mapping.json", 'w')
    map_entries_file.write(map_entries.to_json())
    map_entries_file.close()
    map_entries_file = open("mapping/" + "codex-term-code-mapping.json", 'r')
    validate(instance=json.load(map_entries_file), schema=json.load(open(
        "resources/schema/term-code-mapping-schema.json")))


def generate_term_code_tree(entries):
    term_code_tree = to_term_code_node(entries)
    term_code_file = open("mapping/" + "codex-code-tree.json", 'w')
    term_code_file.write(term_code_tree.to_json())
    term_code_file.close()
    term_code_file = open("mapping/" + "codex-code-tree.json", 'r')
    validate(instance=json.load(term_code_file), schema=json.load(open("resources/schema/codex-code-tree-schema.json")))

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
                if module_category_entry.display == module_element_entry.display:
                        # Resolves issue like : -- Prozedure                 --Prozedure
                        #                           -- Prozedure     --->      -- BILDGEBENDE DIAGNOSTIK
                        #                              -- BILDGEBENDE DIAGNOSTIK
                        module_category_entry.children += module_element_entry.children
                else:
                    module_category_entry.children.append(module_element_entry)
        f = open("ui-profiles/" + module_category_entry.display + ".json", 'w', encoding="utf-8")
        f.write(module_category_entry.to_json())
        f.close()
        validate_ui_profile(module_category_entry.display)
        core_data_set_modules.append(module_category_entry)
    return core_data_set_modules

#einzeln laufen lassen

# Schritt 0
#generate_result_folder()

# Schritt 1
# hier fehlt dann noch später 
# download_core_data_set_mii + download_dktk stuff
# generate_snapshots()

# Schritt 2
core_data_category_entries = generate_core_data_set()

# SCHRITT 3, 4, 5
for profile in get_ui_profiles():
   print(profile.to_json())
generate_term_code_mapping(core_data_category_entries)
generate_term_code_tree(core_data_category_entries)

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