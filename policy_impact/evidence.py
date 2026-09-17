"""Immutable registered-text evidence. Valid references are not proof of a claim."""
from dataclasses import dataclass
from datetime import date
import hashlib
import json
import re
from types import MappingProxyType


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', value):
        raise ValueError('identifier must be 1–128 safe ASCII characters, starting with a letter or digit')


def _date(value):
    if value is None:
        return
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('date must be YYYY-MM-DD or explicitly unknown (None)')
    date.fromisoformat(value)


@dataclass(frozen=True)
class SourceRevision:
    document_id: str
    revision_id: str
    role: str
    text: str
    provenance: str
    published_on: str | None = None
    effective_on: str | None = None

    def __post_init__(self):
        _identifier(self.document_id)
        _identifier(self.revision_id)
        if self.role not in ('policy', 'procedure'):
            raise ValueError('role must be policy or procedure')
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError('source text must be nonempty')
        if not isinstance(self.provenance, str) or not self.provenance.strip():
            raise ValueError('provenance must be explicit')
        _date(self.published_on)
        _date(self.effective_on)
        # Preserve content exactly: no whitespace, newline or Unicode normalization.
        try:
            self.text.encode('utf-8')
            self.provenance.encode('utf-8')
        except UnicodeEncodeError as error:
            raise ValueError('source must be valid UTF-8 encodable text') from error

    @property
    def content_sha256(self):
        return hashlib.sha256(self.text.encode('utf-8')).hexdigest()

    @property
    def fingerprint(self):
        """Bind evidence to content AND metadata, including unknown dates."""
        payload = dict(schema_version=1, document_id=self.document_id, revision_id=self.revision_id,
                       role=self.role, content_sha256=self.content_sha256, provenance=self.provenance,
                       published_on=self.published_on, effective_on=self.effective_on)
        serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class EvidenceRef:
    document_id: str
    revision_id: str
    source_fingerprint: str
    start: int
    end: int
    quote: str

    def __post_init__(self):
        _identifier(self.document_id)
        _identifier(self.revision_id)
        if not isinstance(self.source_fingerprint, str) or not re.fullmatch(r'[a-f0-9]{64}', self.source_fingerprint):
            raise ValueError('fingerprint must be a lowercase SHA-256 hex digest')
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start < self.end:
            raise ValueError('span must be nonempty, nonnegative integer offsets [start, end)')
        if not isinstance(self.quote, str) or not self.quote.strip():
            raise ValueError('quote must be nonempty text')


class Corpus:
    """Read-only snapshot, indexed by explicit document/revision pair. No disk or network reads."""

    def __init__(self, revisions):
        sources = {}
        for source in revisions:
            if not isinstance(source, SourceRevision):
                raise ValueError('corpus entries must be SourceRevision instances')
            key = (source.document_id, source.revision_id)
            if key in sources:
                raise ValueError('duplicate document/revision identity')
            sources[key] = source
        if not sources:
            raise ValueError('corpus must contain at least one source')
        self._sources = MappingProxyType(sources)

    def get(self, document_id, revision_id):
        _identifier(document_id)
        _identifier(revision_id)
        try:
            return self._sources[(document_id, revision_id)]
        except KeyError as error:
            raise ValueError('unknown document/revision identity') from error

    def cite(self, document_id, revision_id, start, end):
        source = self.get(document_id, revision_id)
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source.text):
            raise ValueError('span is outside source text')
        reference = EvidenceRef(document_id, revision_id, source.fingerprint, start, end, source.text[start:end])
        self.verify(reference)
        return reference

    def verify(self, reference):
        if not isinstance(reference, EvidenceRef):
            raise ValueError('expected EvidenceRef')
        source = self.get(reference.document_id, reference.revision_id)
        if reference.source_fingerprint != source.fingerprint:
            raise ValueError('source fingerprint mismatch')
        if reference.end > len(source.text):
            raise ValueError('span is outside source text')
        if source.text[reference.start:reference.end] != reference.quote:
            raise ValueError('quote does not exactly match registered source text')
        return reference.quote
