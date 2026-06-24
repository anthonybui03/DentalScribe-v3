"""Dental note templates — built-in + user-defined custom templates."""
import json
from dataclasses import dataclass, asdict
from typing import Optional
from app.core.config import templates_path


@dataclass
class NoteTemplate:
    name: str
    llm_instruction: str
    skeleton: str
    builtin: bool = False


_BUILTINS: list[NoteTemplate] = [
    NoteTemplate(
        name="Hygiene Recall",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into a professional Hygiene Recall note. Include clearly labeled "
            "sections: Subjective, Oral Hygiene Assessment, Periodontal Assessment, "
            "Radiographs, Assessment, Plan, and end with a Provider Review reminder. "
            "Use concise clinical language. Do not fabricate findings."
        ),
        skeleton=(
            "Subjective:\n\nOral Hygiene Assessment:\n\nPeriodontal Assessment:\n\n"
            "Radiographs:\n\nAssessment:\n\nPlan:\n\n"
            "Provider Review: Required before chart entry.\n"
        ),
    ),
    NoteTemplate(
        name="Limited Exam",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into a professional Limited Exam note with sections: "
            "Chief Complaint, Clinical Findings, Assessment, Plan. "
            "End with a Provider Review reminder. Be concise and clinically accurate."
        ),
        skeleton=(
            "Chief Complaint:\n\nClinical Findings:\n\nAssessment:\n\nPlan:\n\n"
            "Provider Review: Required before chart entry.\n"
        ),
    ),
    NoteTemplate(
        name="Comprehensive Exam",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into a Comprehensive Exam note. Include: Medical History Update, "
            "Chief Complaint, Extra-oral Exam, Intra-oral Exam, Periodontal Assessment, "
            "Radiographic Findings, Diagnosis, Treatment Plan. "
            "End with a Provider Review reminder."
        ),
        skeleton=(
            "Medical History Update:\n\nChief Complaint:\n\nExtra-oral Exam:\n\n"
            "Intra-oral Exam:\n\nPeriodontal Assessment:\n\nRadiographic Findings:\n\n"
            "Diagnosis:\n\nTreatment Plan:\n\n"
            "Provider Review: Required before chart entry.\n"
        ),
    ),
    NoteTemplate(
        name="Pediatric Restorative",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into a Pediatric Restorative note. Include: Subjective, "
            "Behavior (Frankl scale if mentioned), Anesthesia, Treatment Completed, "
            "Post-op Instructions, Parent/Guardian Informed. "
            "End with a Provider Review reminder."
        ),
        skeleton=(
            "Subjective:\n\nBehavior:\n\nAnesthesia:\n\nTreatment Completed:\n\n"
            "Post-op Instructions:\n\nParent/Guardian Informed:\n\n"
            "Provider Review: Required before chart entry.\n"
        ),
    ),
    NoteTemplate(
        name="Extraction",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into an Extraction note. Include: Tooth/Teeth, Indication, "
            "Anesthesia (type, amount, lot/exp if stated), Procedure, Hemostasis, "
            "Complications (if any — state 'None' if not mentioned), "
            "Post-op Instructions Given, Follow-up. "
            "End with a Provider Review reminder."
        ),
        skeleton=(
            "Tooth/Teeth:\n\nIndication:\n\nAnesthesia:\n\nProcedure:\n\n"
            "Hemostasis:\n\nComplications:\n\nPost-op Instructions Given:\n\n"
            "Follow-up:\n\nProvider Review: Required before chart entry.\n"
        ),
    ),
    NoteTemplate(
        name="Fluoride / SDF",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into a Fluoride or Silver Diamine Fluoride (SDF) application note. "
            "Include: Teeth Treated, Material Applied, Concentration/Strength, "
            "Patient or Guardian Consent Obtained, Post-op Instructions. "
            "End with a Provider Review reminder."
        ),
        skeleton=(
            "Teeth Treated:\n\nMaterial Applied:\n\nConcentration/Strength:\n\n"
            "Patient/Guardian Consent:\n\nPost-op Instructions:\n\n"
            "Provider Review: Required before chart entry.\n"
        ),
    ),
    NoteTemplate(
        name="Referral Letter",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into a professional dental referral letter. Include: Today's Date, "
            "Referring Provider Name/Practice, Patient Name (if stated), "
            "Reason for Referral, Relevant Clinical Summary, Requested Treatment or "
            "Evaluation, and a closing thank-you. Use formal letter format."
        ),
        skeleton=(
            "Date:\n\nDear Dr. ___,\n\nRe: Patient: ___\n\n"
            "Reason for Referral:\n\nClinical Summary:\n\n"
            "Requested Treatment/Evaluation:\n\n"
            "Thank you for seeing this patient. Please feel free to contact our office "
            "with any questions.\n\nSincerely,\n___\n\n"
            "Provider Review: Required before chart entry.\n"
        ),
    ),
    NoteTemplate(
        name="Custom / Freeform",
        builtin=True,
        llm_instruction=(
            "You are a dental clinical documentation assistant. Convert the following "
            "dictation into a clean, well-organized dental clinical note. "
            "Use appropriate section headings based on the content. "
            "Be concise, clinically accurate, and end with a Provider Review reminder."
        ),
        skeleton=(
            "Subjective:\n\nObjective:\n\nAssessment:\n\nPlan:\n\n"
            "Provider Review: Required before chart entry.\n"
        ),
    ),
]


class TemplateRegistry:
    """Single instance manages all templates — builtins + user-defined."""

    def __init__(self) -> None:
        self._templates: dict[str, NoteTemplate] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._templates = {t.name: t for t in _BUILTINS}
        path = templates_path()
        if path.exists():
            try:
                for item in json.loads(path.read_text(encoding="utf-8")):
                    t = NoteTemplate(
                        name=item["name"],
                        llm_instruction=item.get("llm_instruction", ""),
                        skeleton=item.get("skeleton", ""),
                        builtin=False,
                    )
                    self._templates[t.name] = t
            except Exception as e:
                print(f"[templates] load error: {e}")
        self._loaded = True

    def all(self) -> dict[str, NoteTemplate]:
        self._ensure_loaded()
        return dict(self._templates)

    def names(self) -> list[str]:
        self._ensure_loaded()
        return list(self._templates)

    def get(self, name: str) -> NoteTemplate:
        self._ensure_loaded()
        return self._templates.get(name) or self._templates.get("Custom / Freeform") or _BUILTINS[-1]

    def save_custom(self, name: str, skeleton: str, llm_instruction: str = "") -> None:
        self._ensure_loaded()
        if not llm_instruction:
            llm_instruction = (
                "You are a dental clinical documentation assistant. Convert the following "
                "dictation into a professional dental chart note using the provided template."
            )
        self._templates[name] = NoteTemplate(
            name=name, llm_instruction=llm_instruction,
            skeleton=skeleton, builtin=False,
        )
        self._persist()

    def delete_custom(self, name: str) -> bool:
        self._ensure_loaded()
        t = self._templates.get(name)
        if not t or t.builtin:
            return False
        del self._templates[name]
        self._persist()
        return True

    def _persist(self) -> None:
        custom = [
            {"name": t.name, "llm_instruction": t.llm_instruction, "skeleton": t.skeleton}
            for t in self._templates.values() if not t.builtin
        ]
        templates_path().write_text(json.dumps(custom, indent=2), encoding="utf-8")


registry = TemplateRegistry()
