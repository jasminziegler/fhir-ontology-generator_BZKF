GECCO = "de.gecco 1.0.5"
GECCO_DIRECTORY = "de.gecco#1.0.5"
MII_CASE = "de.medizininformatikinitiative.kerndatensatz.fall 1.0.1"
MII_DIAGNOSE = "de.medizininformatikinitiative.kerndatensatz.diagnose 1.0.4"
MII_LAB = "de.medizininformatikinitiative.kerndatensatz.laborbefund 1.0.6"
MII_MEDICATION = "de.medizininformatikinitiative.kerndatensatz.medikation 1.0.10"
MII_PERSON = "de.medizininformatikinitiative.kerndatensatz.person 2.0.0-alpha2"
MII_PROCEDURE = "de.medizininformatikinitiative.kerndatensatz.prozedur 2.0.0-alpha1"
MII_SPECIMEN = "de.medizininformatikinitiative.kerndatensatz.biobank 0.9.0"
BBMRI = "bbmri.de"
DKTK = "de.dktk.oncology 1.1.1"
core_data_sets = [MII_DIAGNOSE, MII_LAB, MII_MEDICATION, MII_PERSON, MII_PROCEDURE, MII_SPECIMEN, DKTK] #, GECCO]

GECCO_DATA_SET = "resources/core_data_sets/de.gecco#1.0.5/package"
MII_MEDICATION_DATA_SET = "resources/core_data_sets/de.medizininformatikinitiative.kerndatensatz.medikation#1.0.10" \
                          "/package"
SPECIMEN_VS = "https://www.medizininformatik-initiative.de/fhir/abide/ValueSet/sct-specimen-type-napkon-sprec"

"""
    Date of birth requires date selection in the ui
    ResuscitationOrder Consent is not mappable for fhir search
    RespiratoryOutcome needs special handling its a condition but has a value in the verification status:
        Confirmed -> Patient dependent on ventilator 
        Refuted -> Patient not dependent on ventilator 
    Severity is handled within Symptoms
"""

IGNORE_LIST = ["Date of birth", "Severity", "OrganizationSammlungBiobank", "SubstanceAdditiv",
               "MedicationMedikation", "MedicationStatementMedikation", "ProbandIn", "Laborbefund", "Laboranforderung"]