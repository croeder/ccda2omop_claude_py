# Copyright 2025 Christophe Roeder. All rights reserved.

"""C-CDA XML parser using lxml with XPath."""

from pathlib import Path
from typing import Optional, Union

from lxml import etree

from .constants import (
    ENTRIES_REQUIRED_OIDS,
    KNOWN_SECTION_OIDS,
    OID_ALLERGIES,
    OID_ALLERGIES_ENTRIES_REQ,
    OID_ENCOUNTERS,
    OID_ENCOUNTERS_ENTRIES_REQ,
    OID_IMMUNIZATIONS,
    OID_IMMUNIZATIONS_ENTRIES_REQ,
    OID_MEDICAL_EQUIPMENT,
    OID_MEDICATIONS,
    OID_MEDICATIONS_ENTRIES_REQ,
    OID_PROBLEMS,
    OID_PROBLEMS_ENTRIES_REQ,
    OID_PROCEDURES,
    OID_PROCEDURES_ENTRIES_REQ,
    OID_RESULTS,
    OID_RESULTS_ENTRIES_REQ,
    OID_SOCIAL_HISTORY,
    OID_VITAL_SIGNS,
    OID_VITAL_SIGNS_ENTRIES_REQ,
)
from .hl7_time import parse_hl7_time
from .models import (
    Address,
    Allergy,
    Author,
    CodedValue,
    Custodian,
    Device,
    Document,
    EffectiveTime,
    Encounter,
    Immunization,
    LabResult,
    Medication,
    Name,
    Patient,
    Problem,
    Procedure,
    Quantity,
    ReferenceRange,
    SectionMetadata,
    SocialObservation,
    Telecom,
    VitalSign,
)


class CCDAParser:
    """Parses C-CDA XML documents using lxml with XPath."""

    def parse_file(self, filepath: Union[str, Path]) -> Document:
        """
        Parse a C-CDA file and return a Document.

        Args:
            filepath: Path to the C-CDA XML file

        Returns:
            Parsed Document object
        """
        tree = etree.parse(str(filepath))
        root = tree.getroot()
        self._strip_namespaces(root)
        return self._parse_document(root)

    def parse_string(self, xml_data: Union[str, bytes]) -> Document:
        """
        Parse C-CDA XML data from string or bytes.

        Args:
            xml_data: C-CDA XML content as string or bytes

        Returns:
            Parsed Document object
        """
        if isinstance(xml_data, str):
            xml_data = xml_data.encode("utf-8")
        root = etree.fromstring(xml_data)
        self._strip_namespaces(root)
        return self._parse_document(root)

    def _strip_namespaces(self, root: etree._Element) -> None:
        """Strip all namespace prefixes from element tags for simpler XPath."""
        for elem in root.iter():
            if isinstance(elem.tag, str) and elem.tag.startswith("{"):
                elem.tag = elem.tag.split("}", 1)[1]

    def _parse_document(self, root: etree._Element) -> Document:
        """Parse the root element into a Document."""
        doc = Document(
            section_meta={},
            xml_root=root,
        )

        # Parse patient demographics
        doc.patient = self._parse_patient(root)

        # Parse author
        doc.author = self._parse_author(root)

        # Parse custodian
        doc.custodian = self._parse_custodian(root)

        # Find and parse each section by template OID
        sections = root.xpath("//component/section")
        for section in sections:
            template_oid = self._get_section_template_oid(section)

            if template_oid in (OID_ENCOUNTERS, OID_ENCOUNTERS_ENTRIES_REQ):
                doc.encounters = self._parse_encounters(section)
                doc.section_meta["Encounters"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_ENCOUNTERS_ENTRIES_REQ),
                )
            elif template_oid in (OID_PROBLEMS, OID_PROBLEMS_ENTRIES_REQ):
                doc.problems = self._parse_problems(section)
                doc.section_meta["Problems"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_PROBLEMS_ENTRIES_REQ),
                )
            elif template_oid in (OID_MEDICATIONS, OID_MEDICATIONS_ENTRIES_REQ):
                doc.medications = self._parse_medications(section)
                doc.section_meta["Medications"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_MEDICATIONS_ENTRIES_REQ),
                )
            elif template_oid in (OID_PROCEDURES, OID_PROCEDURES_ENTRIES_REQ):
                doc.procedures = self._parse_procedures(section)
                doc.section_meta["Procedures"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_PROCEDURES_ENTRIES_REQ),
                )
            elif template_oid in (OID_VITAL_SIGNS, OID_VITAL_SIGNS_ENTRIES_REQ):
                doc.vital_signs = self._parse_vital_signs(section)
                doc.section_meta["VitalSigns"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_VITAL_SIGNS_ENTRIES_REQ),
                )
            elif template_oid in (OID_RESULTS, OID_RESULTS_ENTRIES_REQ):
                doc.lab_results = self._parse_lab_results(section)
                doc.section_meta["LabResults"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_RESULTS_ENTRIES_REQ),
                )
            elif template_oid in (OID_ALLERGIES, OID_ALLERGIES_ENTRIES_REQ):
                doc.allergies = self._parse_allergies(section)
                doc.section_meta["Allergies"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_ALLERGIES_ENTRIES_REQ),
                )
            elif template_oid in (OID_IMMUNIZATIONS, OID_IMMUNIZATIONS_ENTRIES_REQ):
                doc.immunizations = self._parse_immunizations(section)
                doc.section_meta["Immunizations"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=(template_oid == OID_IMMUNIZATIONS_ENTRIES_REQ),
                )
            elif template_oid == OID_MEDICAL_EQUIPMENT:
                doc.devices = self._parse_devices(section)
                doc.section_meta["Devices"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=False,
                )
            elif template_oid == OID_SOCIAL_HISTORY:
                doc.observations = self._parse_social_history(section)
                doc.section_meta["Observations"] = SectionMetadata(
                    template_oid=template_oid,
                    entries_required=False,
                )

        return doc

    def _get_section_template_oid(self, section: etree._Element) -> str:
        """Extract the section template OID."""
        templates = section.findall("templateId")
        for t in templates:
            root_oid = t.get("root", "")
            if root_oid in KNOWN_SECTION_OIDS:
                return root_oid
        return ""

    # ============ Patient Parsing ============

    def _parse_patient(self, root: etree._Element) -> Patient:
        """Parse patient demographics."""
        p = Patient()

        # Patient ID
        id_elem = self._find_one(root, ".//recordTarget/patientRole/id")
        if id_elem is not None:
            ext = id_elem.get("extension", "")
            p.id = ext if ext else id_elem.get("root", "")

        # Name
        name_elem = self._find_one(
            root, ".//recordTarget/patientRole/patient/name"
        )
        if name_elem is not None:
            p.name = self._parse_name(name_elem)

        # Birth time
        bt_elem = self._find_one(
            root, ".//recordTarget/patientRole/patient/birthTime"
        )
        if bt_elem is not None:
            p.birth_time = parse_hl7_time(bt_elem.get("value", ""))

        # Gender
        gender_elem = self._find_one(
            root, ".//recordTarget/patientRole/patient/administrativeGenderCode"
        )
        if gender_elem is not None:
            p.gender = self._parse_code(gender_elem)

        # Race
        race_elem = self._find_one(
            root, ".//recordTarget/patientRole/patient/raceCode"
        )
        if race_elem is not None:
            p.race = self._parse_code(race_elem)

        # Ethnicity
        eth_elem = self._find_one(
            root, ".//recordTarget/patientRole/patient/ethnicGroupCode"
        )
        if eth_elem is not None:
            p.ethnicity = self._parse_code(eth_elem)

        # Address
        addr_elem = self._find_one(root, ".//recordTarget/patientRole/addr")
        if addr_elem is not None:
            p.address = self._parse_address(addr_elem)

        # Telecom
        telecom_elems = root.xpath(".//recordTarget/patientRole/telecom")
        for t in telecom_elems:
            p.telecom.append(
                Telecom(use=t.get("use", ""), value=t.get("value", ""))
            )

        # Marital status
        ms_elem = self._find_one(
            root, ".//recordTarget/patientRole/patient/maritalStatusCode"
        )
        if ms_elem is not None:
            p.marital_status = self._parse_code(ms_elem)

        # Language
        lang_elem = self._find_one(
            root,
            ".//recordTarget/patientRole/patient/languageCommunication/languageCode",
        )
        if lang_elem is not None:
            p.language = self._parse_code(lang_elem)

        return p

    def _parse_name(self, node: etree._Element) -> Name:
        """Parse a name element."""
        n = Name()

        given_elems = node.findall("given")
        given_names = [g.text or "" for g in given_elems if g.text]
        n.given = " ".join(given_names)

        family_elem = node.find("family")
        if family_elem is not None and family_elem.text:
            n.family = family_elem.text

        suffix_elem = node.find("suffix")
        if suffix_elem is not None and suffix_elem.text:
            n.suffix = suffix_elem.text

        prefix_elem = node.find("prefix")
        if prefix_elem is not None and prefix_elem.text:
            n.prefix = prefix_elem.text

        return n

    def _parse_address(self, node: etree._Element) -> Address:
        """Parse an address element."""
        a = Address()

        street_elems = node.findall("streetAddressLine")
        a.street_address = [s.text for s in street_elems if s.text]

        city_elem = node.find("city")
        if city_elem is not None and city_elem.text:
            a.city = city_elem.text

        state_elem = node.find("state")
        if state_elem is not None and state_elem.text:
            a.state = state_elem.text

        postal_elem = node.find("postalCode")
        if postal_elem is not None and postal_elem.text:
            a.postal_code = postal_elem.text

        country_elem = node.find("country")
        if country_elem is not None and country_elem.text:
            a.country = country_elem.text

        return a

    # ============ Author/Custodian Parsing ============

    def _parse_author(self, root: etree._Element) -> Author:
        """Parse document author."""
        a = Author()

        time_elem = self._find_one(root, ".//author/time")
        if time_elem is not None:
            a.time = parse_hl7_time(time_elem.get("value", ""))

        id_elem = self._find_one(root, ".//author/assignedAuthor/id")
        if id_elem is not None:
            a.id = id_elem.get("extension", "")

        name_elem = self._find_one(
            root, ".//author/assignedAuthor/assignedPerson/name"
        )
        if name_elem is not None:
            a.name = self._parse_name(name_elem)

        org_elem = self._find_one(
            root, ".//author/assignedAuthor/representedOrganization/name"
        )
        if org_elem is not None and org_elem.text:
            a.organization = org_elem.text

        return a

    def _parse_custodian(self, root: etree._Element) -> Custodian:
        """Parse document custodian."""
        c = Custodian()
        base = ".//custodian/assignedCustodian/representedCustodianOrganization"

        id_elem = self._find_one(root, f"{base}/id")
        if id_elem is not None:
            c.id = id_elem.get("extension", "")

        name_elem = self._find_one(root, f"{base}/name")
        if name_elem is not None and name_elem.text:
            c.name = name_elem.text

        addr_elem = self._find_one(root, f"{base}/addr")
        if addr_elem is not None:
            c.address = self._parse_address(addr_elem)

        tel_elem = self._find_one(root, f"{base}/telecom")
        if tel_elem is not None:
            c.telecom = Telecom(
                use=tel_elem.get("use", ""), value=tel_elem.get("value", "")
            )

        return c

    # ============ Section Parsers ============

    def _parse_encounters(self, section: etree._Element) -> list[Encounter]:
        """Parse encounters section."""
        encounters = []

        entries = section.xpath("entry/encounter")
        for enc in entries:
            if not self._should_include_entry(enc):
                continue

            encounter = Encounter(
                id=self._get_id(enc),
                code=self._parse_code(enc.find("code")),
                effective_time=self._parse_effective_time(
                    enc.find("effectiveTime")
                ),
            )

            # Performer
            performer_elem = self._find_one(
                enc, "performer/assignedEntity/assignedPerson/name"
            )
            if performer_elem is not None:
                n = self._parse_name(performer_elem)
                encounter.performer = f"{n.given} {n.family}".strip()

            # Location
            loc_elem = self._find_one(
                enc,
                "participant[@typeCode='LOC']/participantRole/playingEntity/name",
            )
            if loc_elem is not None and loc_elem.text:
                encounter.location = loc_elem.text

            encounters.append(encounter)

        return encounters

    def _parse_problems(self, section: etree._Element) -> list[Problem]:
        """Parse problems section."""
        problems = []

        observations = section.xpath("entry/act/entryRelationship/observation")
        for obs in observations:
            if not self._should_include_entry(obs):
                continue

            problem = Problem(
                id=self._get_id(obs),
                effective_time=self._parse_effective_time(
                    obs.find("effectiveTime")
                ),
                status=self._parse_code(obs.find("statusCode")),
            )

            # Problem code is typically in the value element
            val_elem = obs.find("value")
            if val_elem is not None and val_elem.get("code"):
                problem.code = self._parse_code(val_elem)
            else:
                problem.code = self._parse_code(obs.find("code"))

            problems.append(problem)

        return problems

    def _parse_medications(self, section: etree._Element) -> list[Medication]:
        """Parse medications section."""
        medications = []

        entries = section.xpath("entry/substanceAdministration")
        for sa in entries:
            if not self._should_include_entry(sa):
                continue

            med = Medication(
                id=self._get_id(sa),
                status=self._parse_code(sa.find("statusCode")),
                route_code=self._parse_code(sa.find("routeCode")),
                dose_quantity=self._parse_quantity(sa.find("doseQuantity")),
                rate_quantity=self._parse_quantity(sa.find("rateQuantity")),
            )

            # Drug code from consumable
            code_elem = self._find_one(
                sa, "consumable/manufacturedProduct/manufacturedMaterial/code"
            )
            if code_elem is not None:
                med.code = self._parse_code(code_elem)

            # Effective time
            eff_times = sa.findall("effectiveTime")
            for et in eff_times:
                if et.find("low") is not None or et.find("high") is not None:
                    med.effective_time = self._parse_effective_time(et)
                    break
                elif et.get("value"):
                    med.effective_time.value = parse_hl7_time(et.get("value", ""))

            # Days supply
            supply_elem = self._find_one(
                sa, "entryRelationship/supply/quantity"
            )
            if supply_elem is not None:
                try:
                    med.days_supply = int(supply_elem.get("value", "0"))
                except ValueError:
                    pass

            medications.append(med)

        return medications

    def _parse_procedures(self, section: etree._Element) -> list[Procedure]:
        """Parse procedures section."""
        procedures = []

        entries = section.xpath("entry/procedure")
        for proc in entries:
            if not self._should_include_entry(proc):
                continue

            procedure = Procedure(
                id=self._get_id(proc),
                code=self._parse_code(proc.find("code")),
                effective_time=self._parse_effective_time(
                    proc.find("effectiveTime")
                ),
                status=self._parse_code(proc.find("statusCode")),
                target_site=self._parse_code(proc.find("targetSiteCode")),
            )

            performer_elem = self._find_one(
                proc, "performer/assignedEntity/assignedPerson/name"
            )
            if performer_elem is not None:
                n = self._parse_name(performer_elem)
                procedure.performer = f"{n.given} {n.family}".strip()

            procedures.append(procedure)

        return procedures

    def _parse_vital_signs(self, section: etree._Element) -> list[VitalSign]:
        """Parse vital signs section."""
        vitals = []

        observations = section.xpath("entry/organizer/component/observation")
        for obs in observations:
            if not self._should_include_entry(obs):
                continue

            vital = VitalSign(
                id=self._get_id(obs),
                code=self._parse_code(obs.find("code")),
                interpretation=self._parse_code(obs.find("interpretationCode")),
            )

            et_elem = obs.find("effectiveTime")
            if et_elem is not None:
                vital.effective_time = parse_hl7_time(et_elem.get("value", ""))

            val_elem = obs.find("value")
            if val_elem is not None:
                try:
                    vital.value = float(val_elem.get("value", "0"))
                except ValueError:
                    pass
                vital.unit = val_elem.get("unit", "")

            vitals.append(vital)

        return vitals

    def _parse_lab_results(self, section: etree._Element) -> list[LabResult]:
        """Parse lab results section."""
        results = []

        observations = section.xpath("entry/organizer/component/observation")
        for obs in observations:
            if not self._should_include_entry(obs):
                continue

            result = LabResult(
                id=self._get_id(obs),
                code=self._parse_code(obs.find("code")),
                status=self._parse_code(obs.find("statusCode")),
                interpretation=self._parse_code(obs.find("interpretationCode")),
            )

            et_elem = obs.find("effectiveTime")
            if et_elem is not None:
                result.effective_time = parse_hl7_time(et_elem.get("value", ""))

            val_elem = obs.find("value")
            if val_elem is not None:
                try:
                    result.value = float(val_elem.get("value", "0"))
                except ValueError:
                    result.value_string = val_elem.get("value", "")
                result.unit = val_elem.get("unit", "")

            # Reference range
            rr_elem = self._find_one(obs, "referenceRange/observationRange")
            if rr_elem is not None:
                text_elem = rr_elem.find("text")
                if text_elem is not None and text_elem.text:
                    result.reference_range.text = text_elem.text
                low_elem = self._find_one(rr_elem, "value/low")
                if low_elem is not None:
                    try:
                        result.reference_range.low = float(
                            low_elem.get("value", "0")
                        )
                    except ValueError:
                        pass
                high_elem = self._find_one(rr_elem, "value/high")
                if high_elem is not None:
                    try:
                        result.reference_range.high = float(
                            high_elem.get("value", "0")
                        )
                    except ValueError:
                        pass

            results.append(result)

        return results

    def _parse_allergies(self, section: etree._Element) -> list[Allergy]:
        """Parse allergies section."""
        allergies = []

        observations = section.xpath("entry/act/entryRelationship/observation")
        for obs in observations:
            if not self._should_include_entry(obs):
                continue

            allergy = Allergy(
                id=self._get_id(obs),
                effective_time=self._parse_effective_time(
                    obs.find("effectiveTime")
                ),
                status=self._parse_code(obs.find("statusCode")),
            )

            # Substance from participant
            substance_elem = self._find_one(
                obs,
                "participant[@typeCode='CSM']/participantRole/playingEntity/code",
            )
            if substance_elem is not None:
                allergy.substance = self._parse_code(substance_elem)

            allergies.append(allergy)

        return allergies

    def _parse_immunizations(
        self, section: etree._Element
    ) -> list[Immunization]:
        """Parse immunizations section."""
        immunizations = []

        entries = section.xpath("entry/substanceAdministration")
        for sa in entries:
            if not self._should_include_entry(sa):
                continue

            imm = Immunization(
                id=self._get_id(sa),
                status=self._parse_code(sa.find("statusCode")),
                route_code=self._parse_code(sa.find("routeCode")),
                dose_quantity=self._parse_quantity(sa.find("doseQuantity")),
            )

            # Vaccine code
            code_elem = self._find_one(
                sa, "consumable/manufacturedProduct/manufacturedMaterial/code"
            )
            if code_elem is not None:
                imm.code = self._parse_code(code_elem)

            # Lot number
            lot_elem = self._find_one(
                sa,
                "consumable/manufacturedProduct/manufacturedMaterial/lotNumberText",
            )
            if lot_elem is not None and lot_elem.text:
                imm.lot_number = lot_elem.text

            # Effective time
            et_elem = sa.find("effectiveTime")
            if et_elem is not None:
                imm.effective_time = parse_hl7_time(et_elem.get("value", ""))

            immunizations.append(imm)

        return immunizations

    def _parse_devices(self, section: etree._Element) -> list[Device]:
        """Parse medical equipment section."""
        devices = []

        entries = section.xpath("entry/supply")
        for sup in entries:
            if not self._should_include_entry(sup):
                continue

            device = Device(
                id=self._get_id(sup),
                effective_time=self._parse_effective_time(
                    sup.find("effectiveTime")
                ),
                status=self._parse_code(sup.find("statusCode")),
            )

            # Device code from product or participant/playingDevice
            code_elem = self._find_one(
                sup, "product/manufacturedProduct/manufacturedMaterial/code"
            )
            if code_elem is not None and code_elem.get("code"):
                device.code = self._parse_code(code_elem)

            code_elem2 = self._find_one(
                sup, "participant/participantRole/playingDevice/code"
            )
            if code_elem2 is not None and code_elem2.get("code"):
                device.code = self._parse_code(code_elem2)

            # UDI from participant
            udi_elem = self._find_one(sup, "participant/participantRole/id")
            if udi_elem is not None:
                device.udi = udi_elem.get("extension", "")

            devices.append(device)

        return devices

    def _parse_social_history(
        self, section: etree._Element
    ) -> list[SocialObservation]:
        """Parse social history section."""
        observations = []

        entries = section.xpath("entry/observation")
        for obs in entries:
            if not self._should_include_entry(obs):
                continue

            social_obs = SocialObservation(
                id=self._get_id(obs),
                code=self._parse_code(obs.find("code")),
                effective_time=self._parse_effective_time(
                    obs.find("effectiveTime")
                ),
                status=self._parse_code(obs.find("statusCode")),
            )

            # Value can be coded or quantity
            val_elem = obs.find("value")
            if val_elem is not None:
                if val_elem.get("code"):
                    social_obs.value = self._parse_code(val_elem)
                elif val_elem.get("value"):
                    try:
                        social_obs.value_quantity = Quantity(
                            value=float(val_elem.get("value", "0")),
                            unit=val_elem.get("unit", ""),
                        )
                    except ValueError:
                        pass

            observations.append(social_obs)

        return observations

    # ============ Helper Functions ============

    def _should_include_entry(self, node: etree._Element) -> bool:
        """
        Check if an entry should be included based on moodCode and statusCode.

        Only includes entries that:
        - Have moodCode="EVN" (actual event) or no moodCode (defaults to EVN)
        - Have statusCode="completed" or "active" or no statusCode
        """
        return self._is_actual_event(node) and self._has_completed_status(node)

    def _is_actual_event(self, node: etree._Element) -> bool:
        """Check if an entry has moodCode='EVN' (event/actual occurrence)."""
        if node is None:
            return False
        mood_code = node.get("moodCode", "")
        # EVN = Event (actual occurrence)
        # Empty moodCode defaults to EVN for observations
        return mood_code in ("EVN", "")

    def _has_completed_status(self, node: etree._Element) -> bool:
        """Check if an entry has a status that indicates completion."""
        if node is None:
            return True
        status_node = node.find("statusCode")
        if status_node is None:
            return True
        status = status_node.get("code", "")
        return status in ("completed", "active", "")

    def _find_one(
        self, node: etree._Element, xpath: str
    ) -> Optional[etree._Element]:
        """Find a single element using XPath."""
        result = node.xpath(xpath)
        return result[0] if result else None

    def _get_id(self, node: etree._Element) -> str:
        """Extract the ID from an element's id child."""
        if node is None:
            return ""
        id_elem = node.find("id")
        if id_elem is not None:
            ext = id_elem.get("extension", "")
            return ext if ext else id_elem.get("root", "")
        return ""

    def _parse_code(self, node: Optional[etree._Element]) -> CodedValue:
        """Parse a CodedValue from an element with code attributes."""
        if node is None:
            return CodedValue()

        cv = CodedValue(
            code=node.get("code", ""),
            code_system=node.get("codeSystem", ""),
            code_system_name=node.get("codeSystemName", ""),
            display_name=node.get("displayName", ""),
        )

        ot_elem = node.find("originalText")
        if ot_elem is not None and ot_elem.text:
            cv.original_text = ot_elem.text

        return cv

    def _parse_effective_time(
        self, node: Optional[etree._Element]
    ) -> EffectiveTime:
        """Parse an EffectiveTime from an effectiveTime element."""
        if node is None:
            return EffectiveTime()

        et = EffectiveTime(value=parse_hl7_time(node.get("value", "")))

        low_elem = node.find("low")
        if low_elem is not None:
            et.low = parse_hl7_time(low_elem.get("value", ""))

        high_elem = node.find("high")
        if high_elem is not None:
            et.high = parse_hl7_time(high_elem.get("value", ""))

        return et

    def _parse_quantity(self, node: Optional[etree._Element]) -> Quantity:
        """Parse a Quantity from a quantity element."""
        if node is None:
            return Quantity()

        try:
            val = float(node.get("value", "0"))
        except ValueError:
            val = 0.0

        return Quantity(value=val, unit=node.get("unit", ""))
