import copy
import json

from TerminologService.ValueSetResolver import get_term_codes_by_path, get_termcodes_from_onto_server, \
    get_term_codes_by_id
from model.UiDataModel import ValueDefinition, TermCode, AttributeDefinition, Unit

UI_PROFILES = set()


def del_none(dictionary):
    """
    Delete keys with the value ``None`` in a dictionary, recursively.

    This alters the input so you may wish to ``copy`` the dict first.
    """
    for key, value in list(dictionary.items()):
        if value is None:
            del dictionary[key]
        elif isinstance(value, dict):
            del_none(value)
        elif isinstance(value, list):
            if not value:
                del dictionary[key]
            for element in value:
                del_none(element.__dict__)
    return dictionary


def del_keys(dictionary, keys):
    result = copy.deepcopy(dictionary)
    for k in keys:
        result.pop(k, None)
    return result


class UIProfile(object):
    DO_NOT_SERIALIZE = []

    def __init__(self, name):
        self.name = name
        self.timeRestrictionAllowed = True
        self.valueDefinition = None
        self.attributeDefinitions = []

    def to_json(self):
        return json.dumps(self, default=lambda o: del_none(
            del_keys(o.__dict__, self.DO_NOT_SERIALIZE)), sort_keys=True, indent=4)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


def generate_concept_observation_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    value_definition = ValueDefinition("concept")
    if selectable_concepts := get_term_codes_by_path("Observation.value[x]", profile_data):
        value_definition.selectableConcepts = selectable_concepts
    else:
        print("ELSE ELSE ELSE")
        print(get_term_codes_by_path("Observation.value[x].coding", profile_data))
        value_definition.selectableConcepts = get_term_codes_by_path("Observation.value[x].coding", profile_data)
        print("selectable concepts = ", value_definition.selectableConcepts)
    ui_profile.valueDefinition = value_definition
    UI_PROFILES.add(ui_profile)
    return ui_profile

# def generate_uicc_observation_ui_profile(profile_data, _logical_element):
#     ui_profile = UIProfile("UICCStadium")
#     value_definition = ValueDefinition("concept")
#     selectable_concepts = get_term_codes_by_path("Observation.value[x]", profile_data)
#     value_definition.selectableConcepts = selectable_concepts
#     ui_profile.valueDefinition = value_definition
#     UI_PROFILES.add(ui_profile)
#     return ui_profile

#ich glaub die wird gar nicht verwendet
def generate_histologie_onco_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    ### TEST 03.08. OHNE VALUEDEFINITION --> das geht nicht durch den validator - Idee 2: get term code from another profile - canonical_url hier angeben
    #value_definition = ValueDefinition("concept")
    #value_definition.selectableConcepts = get_termcodes_from_onto_server('http://dktk.dkfz.de/fhir/onco/core/ValueSet/GradingVS')
    #print("selectable concepts = ", value_definition.selectableConcepts)
    #ui_profile.valueDefinition = value_definition
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_consent_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    for element in profile_data["snapshot"]["element"]:
        if element["id"] == "Consent.provision.code":
            if "binding" in element:
                value_set = element["binding"]["valueSet"]
                value_definition = ValueDefinition("concept")
                value_definition.selectableConcepts += get_termcodes_from_onto_server(value_set)
                ui_profile.valueDefinition = value_definition
                UI_PROFILES.add(ui_profile)
                return ui_profile
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_default_ui_profile(name, _logical_element):
    ui_profile = UIProfile(name)
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_diagnosis_covid_19_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    stage_code = TermCode("mii.abide", "stage", "Stadium")
    stage_attribute = AttributeDefinition(stage_code, "concept")
    stage_attribute.selectableConcepts = get_term_codes_by_path("Condition.stage.summary.coding", profile_data)
    ui_profile.attributeDefinitions.append(stage_attribute)
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_diagnostic_report_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    value_definition = ValueDefinition("concept")
    value_definition.selectableConcepts = get_term_codes_by_path("DiagnosticReport.conclusionCode", profile_data)
    ui_profile.valueDefinition = value_definition
    UI_PROFILES.add(ui_profile)
    return ui_profile


# TODO
def generate_ethnic_group_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    value_definition = ValueDefinition("concept")
    value_definition.selectableConcepts += get_term_codes_by_path("Extension.value[x]", profile_data)
    ui_profile.valueDefinition = value_definition
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_gender_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    ui_profile.timeRestrictionAllowed = False
    gender_attribute_code = TermCode("mii.abide", "gender", "Geschlecht")
    gender_attribute = AttributeDefinition(gender_attribute_code, "concept")
    gender_attribute.optional = False
    gender_attribute.selectableConcepts = (get_term_codes_by_path("Patient.gender", profile_data))
    ui_profile.attributeDefinitions.append(gender_attribute)
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_history_of_travel_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    value_definition = ValueDefinition("concept")
    value_definition.selectableConcepts = get_term_codes_by_id("Observation.component:Country.value[x]", profile_data)
    ui_profile.valueDefinition = value_definition
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_quantity_observation_ui_profile(profile_data, logical_element):
    ui_profile = UIProfile(profile_data["name"])
    ui_profile.valueDefinition = get_value_definition(logical_element)
    UI_PROFILES.add(ui_profile)
    return ui_profile

## MAKE MY NEW UI PROFILE GENERATION SIMILAR TO SPECIMEN
def generate_primary_diagnosis_onco_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])  # = Primaerdiagnose - DEFAULT: TIME RESTRICTION ALLOWED
    
    # - erstmal raus weil ich nicht weiß wie bzw wo das ICD-O-3-T Zeug auf dem Ontoserver liegt - bei Lorenz ist es unter Specimen drin - wie mach ich das dann?
    #  AHH ich glaube hier fehlt mir dann das VALUESET!!! das CodeSystem ist ist ja eh vorhanden - ICD-O-3 - 
    # 1. Topographie
    # topography_attribute_code = TermCode("mii.abide", "bodySite", "ICD-O-3-T Topographie")  # weiß bei dem System hier nie was rein soll
    # topography_attribute = AttributeDefinition(attribute_code=topography_attribute_code, value_type="concept")
    # topography_attribute.selectableConcepts = get_term_codes_by_id("Condition.bodySite.coding.ICD-O-3-T", profile_data) # icd-o-3 bei Specimen -- dieses VS bei Primaerdiagnose https://simplifier.net/oncology/morphologieicdo3vs, siehe https://simplifier.net/oncology/primaerdiagnose
    # ui_profile.attributeDefinitions.append(topography_attribute)

    # 2. Seitenlokalisation ADT 
    body_site_adt_attribute_code = TermCode("mii.abide", "bodySite", "ADT-Seitenlokalisation")
    body_site_adt_attribute = AttributeDefinition(attribute_code=body_site_adt_attribute_code, value_type="concept")
    vs_body_site_adt = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/SeitenlokalisationVS"
    body_site_adt_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_body_site_adt)   #geht das so? und das vs legen wir dann auf server ab? kann ich das lokal testen und hier iwo ablegen zunächst? hier wär es: fhir-ontology-generator_BZKF\resources\core_data_sets\de.dktk.oncology#1.1.1\package\ValueSet-onco-core-ValueSet-SeitenlokalisationVS.json
    ui_profile.attributeDefinitions.append(body_site_adt_attribute)
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_tnm_onco_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    # TNM - T
    tnm_t_attribute_code = TermCode("mii.abide", "TNM-T", "TNM-T")
    tnm_t_attribute = AttributeDefinition(attribute_code=tnm_t_attribute_code, value_type="concept")
    vs_tnm_t = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/TNMTVS"
    tnm_t_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_tnm_t)
    ui_profile.attributeDefinitions.append(tnm_t_attribute)

    # TNM - N
    tnm_n_attribute_code = TermCode("mii.abide", "TNM-N", "TNM-N")
    tnm_n_attribute = AttributeDefinition(attribute_code=tnm_n_attribute_code, value_type="concept")
    vs_tnm_n = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/TNMNVS"
    tnm_n_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_tnm_n)
    ui_profile.attributeDefinitions.append(tnm_n_attribute)

    # TNM - M
    tnm_m_attribute_code = TermCode("mii.abide", "TNM-M", "TNM-M")
    tnm_m_attribute = AttributeDefinition(attribute_code=tnm_m_attribute_code, value_type="concept")
    vs_tnm_m = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/TNMMVS"
    tnm_m_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_tnm_m)
    ui_profile.attributeDefinitions.append(tnm_m_attribute)

    # UICC
    uicc_attribute_code = TermCode("mii.abide", "UICC", "UICC")
    uicc_attribute = AttributeDefinition(attribute_code=uicc_attribute_code, value_type="concept")
    vs_uicc = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/UiccstadiumVS"
    uicc_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_uicc)
    ui_profile.attributeDefinitions.append(uicc_attribute)

    UI_PROFILES.add(ui_profile)
    return ui_profile

def generate_onco_clinical_impression_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile("Verlauf (Follow-Up)")
    # Lokaler Tumorstatus
    local_tumorstatus_attribute_code = TermCode("mii.abide", "Lokaler Tumorstatus", "Lokaler Tumorstatus")
    local_tumorstatus_attribute = AttributeDefinition(attribute_code=local_tumorstatus_attribute_code, value_type="concept")
    vs_local_tumorstatus = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/VerlaufLokalerTumorstatusVS"
    local_tumorstatus_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_local_tumorstatus)
    ui_profile.attributeDefinitions.append(local_tumorstatus_attribute)
    # Gesamtbeurteilung Tumorstatus
    tumorstatus_attribute_code = TermCode("mii.abide", "Gesamtbeurteilung Tumorstatus", "Gesamtbeurteilung Tumorstatus")
    tumorstatus_attribute = AttributeDefinition(attribute_code=tumorstatus_attribute_code, value_type="concept")
    vs_tumorstatus = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/GesamtbeurteilungTumorstatusVS"
    tumorstatus_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_tumorstatus)
    ui_profile.attributeDefinitions.append(tumorstatus_attribute)
    UI_PROFILES.add(ui_profile)
    return ui_profile

def generate_onco_operation_ui_profile(profile_data, _logical_element):
    #print("profile_data[name] ", profile_data["name"])
    ui_profile = UIProfile("Operation")
    # OP-Intention - Pflichtfeld im ADT - GEHT FHIR SEARCH ÜBERHAUPT MIT EXTENSIONS
    op_intention_attribute_code = TermCode("mii.abide", "OP-Intention", "OP-Intention")
    op_intention_attribute = AttributeDefinition(attribute_code=op_intention_attribute_code, value_type="concept")
    vs_op_intention = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/OPIntentionVS"
    op_intention_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_op_intention)
    ui_profile.attributeDefinitions.append(op_intention_attribute)
    # OP Gesamtbeurteilung Residualstatus
    op_rs_attribute_code = TermCode("mii.abide", "Gesamtbeurteilung Residualstatus", "Gesamtbeurteilung Residualstatus")
    op_rs_attribute = AttributeDefinition(attribute_code=op_rs_attribute_code, value_type="concept")
    vs_op_rs = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/GesamtbeurteilungResidualstatusVS"
    op_rs_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_op_rs)
    ui_profile.attributeDefinitions.append(op_rs_attribute)
    # OP Lokale Beurteilung Residualstatus
    op_rs_local_attribute_code = TermCode("mii.abide", "Lokale Beurteilung Residualstatus", "Lokale Beurteilung Residualstatus")
    op_rs_local_attribute = AttributeDefinition(attribute_code=op_rs_local_attribute_code, value_type="concept")
    vs_op_rs_local = "http://dktk.dkfz.de/fhir/onco/core/ValueSet/LokaleBeurteilungResidualstatusVS"
    op_rs_local_attribute.selectableConcepts = get_termcodes_from_onto_server(vs_op_rs_local)
    ui_profile.attributeDefinitions.append(op_rs_local_attribute)
    UI_PROFILES.add(ui_profile)
    return ui_profile

""" def generate_onco_strahlenth_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile("Strahlentherapie") """
    


def generate_specimen_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    status_attribute_code = TermCode("mii.abide", "status", "Status")
    status_attribute_code = AttributeDefinition(attribute_code=status_attribute_code, value_type="concept")
    status_attribute_code.selectableConcepts = get_term_codes_by_path("Specimen.status", profile_data)
    ui_profile.attributeDefinitions.append(status_attribute_code)
    body_site_attribute_code = TermCode("mii.module_specimen", "Specimen.collection.bodySite", "Entnahmeort")
    body_site_attribute = AttributeDefinition(attribute_code=body_site_attribute_code, value_type="concept")
    body_site_attribute.selectableConcepts = get_term_codes_by_id("Specimen.collection.bodySite.coding:icd-o-3",
                                                                  profile_data)
    ui_profile.attributeDefinitions.append(body_site_attribute)
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_symptom_ui_profile(profile_data, _logical_element):
    ui_profile = UIProfile(profile_data["name"])
    severity_attribute_code = TermCode("mii.abide", "severity", "Schweregrad")
    severity_attribute = AttributeDefinition(severity_attribute_code, "concept")
    severity_attribute.optional = False
    # TODO: Refactor not hardcoded!
    severity_vs = "https://www.netzwerk-universitaetsmedizin.de/fhir/ValueSet/condition-severity"
    severity_attribute.selectableConcepts += get_termcodes_from_onto_server(severity_vs)
    ui_profile.attributeDefinitions.append(severity_attribute)
    UI_PROFILES.add(ui_profile)
    return ui_profile


def generate_top300_loinc_ui_profile(terminology_entry, element_id, element_tree):
    ui_profile = UIProfile(terminology_entry.display)
    ui_profile.valueDefinition = get_value_description_from_top_300_loinc(element_id, element_tree)
    UI_PROFILES.add(ui_profile)
    return ui_profile


def get_value_definition(element):
    value_definition = ValueDefinition("quantity")
    if element:
        if "extension" in element:
            for extension in element["extension"]:
                if extension["url"] == "http://hl7.org/fhir/StructureDefinition/elementdefinition-allowedUnits":
                    if "valueCodeableConcept" in extension:
                        value_codeable_concept = extension["valueCodeableConcept"]
                        if "coding" in value_codeable_concept:
                            for coding in value_codeable_concept["coding"]:
                                if coding["system"] == "http://unitsofmeasure.org/" or \
                                        coding["system"] == "http://unitsofmeasure.org":
                                    value_definition.allowedUnits.append(Unit(coding["code"], coding["code"]))
    return value_definition


def get_value_description_from_top_300_loinc(element_id, element_tree):
    value_definition = ValueDefinition("quantity")
    described_value_domain_id = ""
    for data_element in element_tree.xpath("/xmlns:export/xmlns:dataElement",
                                           namespaces={'xmlns': "http://schema.samply.de/mdr/common"}):
        if data_element.get("uuid") == element_id:
            for child in data_element:
                described_value_domain_id = child.text
    for described_value_domain in element_tree.xpath("/xmlns:export/xmlns:describedValueDomain",
                                                     namespaces={"xmlns": "http://schema.samply.de/mdr/common"}):
        if described_value_domain.get("uuid") == described_value_domain_id:
            for child in described_value_domain:
                if child.tag == "{http://schema.samply.de/mdr/common}unitOfMeasure":
                    if not child.text:
                        break
                    unit = Unit(child.text, child.text)
                    value_definition.allowedUnits.append(unit)
    return value_definition


def get_ui_profiles():
    return UI_PROFILES
