import errno
import json
import os
import shutil
from os import path
from jsonschema import validate

from FHIRProfileConfiguration import *
from model.MappingDataModel import generate_map
from model.UiDataModel import TerminologyEntry, TermCode
from geccoToUIProfiles import create_terminology_definition_for, get_gecco_categories, IGNORE_CATEGORIES, \
    MAIN_CATEGORIES, IGNORE_LIST, \
    get_specimen, get_consent, resolve_terminology_entry_profile, get_ui_profiles
from model.termCodeTree import to_term_code_node


# FIXME:
def mkdir_if_not_exists(directory):
    if not path.isdir(f"./{directory}"):
        try:
            os.system(f"mkdir {directory}")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

# die muss geändert werden
def download_core_data_set_mii():
    def add_observation_lab_from_mii_to_gecco():
        os.system(f"fhir install {MII_LAB} --here")
        # TODO not hardcoded
        shutil.copy(f"{MII_LAB}/package/"
                    "Profile-ObservationLab.json", f"{GECCO_DIRECTORY}/package/Profile-ObservationLab.json")

    mkdir_if_not_exists("core_data_sets")
    for dataset in core_data_sets:
        mkdir_if_not_exists("core_data_sets")
        saved_path = os.getcwd()
        os.chdir("resources/core_data_sets")
        os.system(f"fhir install {dataset} --here")
        if dataset == GECCO:
            add_observation_lab_from_mii_to_gecco()
        os.chdir(saved_path)


def generate_snapshots():
    data_set_folders = [f.path for f in os.scandir("resources/core_data_sets") if f.is_dir()]
    saved_path = os.getcwd()
    for folder in data_set_folders:
        os.chdir(f"{folder}/package")
        #os.chdir(f"{folder}\\package")
        os.system(f"fhir install hl7.fhir.r4.core")
        for file in [f for f in os.listdir('.') if
                     os.path.isfile(f) and is_structured_definition(f) and "-snapshot" not in f]:
            os.system(f"fhir push {file}")
            os.system(f"fhir snapshot")
            os.system(f"fhir save {file[:-5]}-snapshot.json")
        os.chdir(saved_path)


def is_structured_definition(file):
    with open(file, encoding="UTF-8") as json_file:
        json_data = json.load(json_file)
        if json_data.get("resourceType") == "StructureDefinition":
            return True
        return False


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


def generate_ui_profiles(entries):
    gecco_term_code = [TermCode("num.codex", "GECCO", "GECCO")]
    gecco = TerminologyEntry(gecco_term_code, "CategoryEntry", leaf=False, selectable=False)
    gecco.display = "GECCO"
    for category in entries:
        if category in IGNORE_CATEGORIES:
            continue
        if category.display in MAIN_CATEGORIES:
            f = open("ui-profiles/" + category.display.replace("/ ", "") + ".json", 'w', encoding="utf-8")
            f.write(category.to_json())
            f.close()
            validate_ui_profile(category.display.replace("/ ", ""))
        else:
            gecco.children.append(category)
    f = open("ui-profiles/" + gecco.display + ".json", 'w', encoding="utf-8")
    f.write(gecco.to_json())
    f.close()
    validate_ui_profile(gecco.display)


def validate_ui_profile(profile_name):
    f = open("ui-profiles/" + profile_name + ".json", 'r')
    validate(instance=json.load(f), schema=json.load(open("resources/schema/ui-profile-schema.json")))


def generate_result_folder():
    mkdir_if_not_exists("mapping")
    mkdir_if_not_exists("csv")
    mkdir_if_not_exists("ui-profiles")


def remove_resource_name(name_with_resource_name):
    # order matters here!
    print("name_with_resource_name: ", name_with_resource_name)
    resource_names = ["ProfilePatient", "Profile", "LogicalModel", "Condition", "DiagnosticReport", "Observation",
                      "ServiceRequest", "Extension", "ResearchSubject", "Procedure"]
    for resource_name in resource_names:
        name_with_resource_name = name_with_resource_name.replace(resource_name, "")
    return name_with_resource_name


def generate_core_data_set():
    core_data_set_modules = []
    for data_set in core_data_sets:
        if data_set != GECCO:
            module_name = data_set.split(' ')[0].split(".")[-1].capitalize()
            module_code = TermCode("mii.abide", module_name, module_name)
            module_category_entry = TerminologyEntry([module_code], "Category", selectable=False, leaf=False)
            data_set = data_set.replace(" ", "#")
            # for snapshot in [f"resources\\core_data_sets\\{data_set}\\package\\{f.name}" for f in
            #                  os.scandir(f"resources/core_data_sets\\{data_set}\\package") if
            #                  not f.is_dir() and "-snapshot" in f.name]:
            for snapshot in [f"resources/core_data_sets/{data_set}/package/{f.name}" for f in
                             os.scandir(f"resources/core_data_sets/{data_set}/package") if
                             not f.is_dir() and "-snapshot" in f.name]:
                with open(snapshot, encoding="UTF-8") as json_file:
                    json_data = json.load(json_file)
                    # Care parentheses matter here!
                    if (kind := json_data.get("kind")) and (kind == "logical"):
                        continue
                    if resource_type := json_data.get("type"):
                        if resource_type == "Bundle":
                            continue
                        elif resource_type == "Extension":
                            continue
                    module_element_name = remove_resource_name(json_data.get("name"))
                    if module_element_name in IGNORE_LIST:
                        continue
                    module_element_code = TermCode("mii.abide", module_element_name, module_element_name)
                    module_element_entry = TerminologyEntry([module_element_code], "Category", selectable=False,
                                                            leaf=False)
                    # resolve_terminology_entry_profile(module_element_entry,
                    #                                   data_set=f"resources\\core_data_sets\\{data_set}\\package")
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


if __name__ == '__main__':
    # einzeln laufen lassen 

    # SCHRITT 0 - done
    #generate_result_folder()


    # ----Time consuming: Only execute initially or on changes----
    #- download dktk stuff here instead of mii core dataset
    #download_core_data_set_mii()    #rename this later

   
    # SCHRITT 1
    #generate_snapshots() #auskommentiert, weil es sehr lange dauert
    # -------------------------------------------------------------
    
    # SCHRITT 2
    core_data_category_entries = generate_core_data_set()

    # category_entries = create_terminology_definition_for(get_gecco_categories())
    # # TODO: ones the specimen and consent profiles are declared use them instead!
    # category_entries.append(get_specimen())
    # category_entries.append(get_consent())
    # generate_ui_profiles(category_entries)

    # SCHRITT 3, 4, 5
    #for profile in get_ui_profiles():
    #    print(profile.to_json())
    #category_entries += core_data_category_entries
    generate_term_code_mapping(core_data_category_entries)
    generate_term_code_tree(core_data_category_entries)

    # remove this category_entries variable to only work with core data without gecco
    # category_entries += core_data_category_entries
    # generate_term_code_mapping(category_entries)
    # generate_term_code_tree(category_entries)

    # to_csv(category_entries)
