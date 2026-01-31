from __future__ import annotations 

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal 
from enum import Enum 
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator
)


metamodel_version = "None"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )
    pass




class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'matrix_eval',
     'default_range': 'string',
     'description': 'A template for extracting and evaluating information about '
                    'data resources for the MATRIX knowledge graph project. This '
                    'template enables systematic scoring of data sources across '
                    'multiple dimensions including domain coverage, source scope, '
                    'utility for drug-disease modeling, and data quality/noise '
                    'levels. The evaluation framework supports evidence-based '
                    'selection and prioritization of knowledge graph data sources '
                    'for drug repurposing applications.',
     'id': 'http://w3id.org/ontogpt/matrix_eval',
     'imports': ['linkml:types', 'core'],
     'keywords': ['knowledge graph',
                  'data evaluation',
                  'drug repurposing',
                  'data quality',
                  'resource assessment',
                  'MATRIX'],
     'license': 'https://creativecommons.org/publicdomain/zero/1.0/',
     'name': 'matrix_eval',
     'prefixes': {'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'matrix_eval': {'prefix_prefix': 'matrix_eval',
                                  'prefix_reference': 'http://w3id.org/ontogpt/matrix_eval/'},
                  'rdf': {'prefix_prefix': 'rdf',
                          'prefix_reference': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}},
     'source_file': 'src/ontogpt/templates/matrix_eval.yaml',
     'title': 'MATRIX Data Source Evaluation Template'} )

class NullDataOptions(str, Enum):
    UNSPECIFIED_METHOD_OF_ADMINISTRATION = "UNSPECIFIED_METHOD_OF_ADMINISTRATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_MENTIONED = "NOT_MENTIONED"


class SourceType(str, Enum):
    """
    Categories of data sources.
    """
    database = "database"
    """
    A structured database or knowledge base
    """
    literature_corpus = "literature corpus"
    """
    A collection of scientific publications or text documents
    """
    ontology = "ontology"
    """
    A formal ontology or controlled vocabulary
    """
    experimental_dataset = "experimental dataset"
    """
    A dataset from experimental studies
    """
    clinical_resource = "clinical resource"
    """
    A resource derived from clinical data or trials
    """
    computational_prediction = "computational prediction"
    """
    A resource based on computational predictions or modeling
    """
    integrated_resource = "integrated resource"
    """
    A resource integrating multiple data types or sources
    """


class DescriptorRichness(str, Enum):
    """
    Assessment levels for the richness of entity and relationship descriptors.
    """
    sparse = "sparse"
    """
    Minimal metadata; few or no confidence scores, evidence types, or mechanistic details; basic entity identifiers only.
    """
    moderate = "moderate"
    """
    Some metadata present; may include basic confidence scores or evidence types; limited mechanistic or contextual information.
    """
    rich = "rich"
    """
    Extensive metadata including confidence scores, evidence types, mechanistic details, effect directions, and clinical context; enables sophisticated querying and multi-hop reasoning.
    """


class CurationLevel(str, Enum):
    """
    Level of human curation and quality control applied to a data source.
    """
    manual = "manual"
    """
    Fully manually curated by domain experts with rigorous quality control.
    """
    semi_automated = "semi-automated"
    """
    Combination of automated extraction and manual review or validation.
    """
    automated = "automated"
    """
    Primarily automated extraction or prediction with minimal manual review.
    """
    mixed = "mixed"
    """
    Variable curation levels across different portions of the resource.
    """


class FilteringLevel(str, Enum):
    """
    Level of filtering or post-processing required to use a data source.
    """
    minimal = "minimal"
    """
    Ready to use with little or no filtering; high quality and consistency.
    """
    moderate = "moderate"
    """
    Some filtering or refinement needed; data requires modest post-processing.
    """
    heavy = "heavy"
    """
    Extensive filtering required; substantial post-processing needed to extract high-quality subset.
    """


class DomainCoverageScore(str, Enum):
    """
    Score for domain coverage dimension assessing entity types, relation types, and descriptor richness.
    """
    number_1 = "1"
    """
    Low: Single entity type, sparse/generic relations, few descriptors.
    """
    number_2 = "2"
    """
    Medium: At least two entities, one consistent relation, usable descriptors.
    """
    number_3 = "3"
    """
    High: Three+ entities, multiple relations, rich descriptors enabling multi-hop paths.
    """


class SourceScopeScore(str, Enum):
    """
    Score for source scope dimension assessing disease/organism coverage, scale, and modality breadth.
    """
    number_1 = "1"
    """
    Low: Niche scope, small scale (<10k edges), single modality/therapeutic area.
    """
    number_2 = "2"
    """
    Medium: Multi-disease/organism, mid-scale (10k-100k+ edges), some modality breadth.
    """
    number_3 = "3"
    """
    High: Broad, cross-disease, large-scale (100k-1M+ edges), multiple relation subtypes and modalities.
    """


class UtilityScore(str, Enum):
    """
    Score for utility in drug-disease modeling dimension assessing direct edge types, ID mapping, direction/effect, and clinical context.
    """
    number_1 = "1"
    """
    Low: Indirect context only; edges sparse, weak, or poorly mapped; no clear D-T/T-D/D-D/AE.
    """
    number_2 = "2"
    """
    Medium: At least one direct edge family; IDs align reasonably; some direction/effect or clinical context present.
    """
    number_3 = "3"
    """
    High: Multiple strong edge families; clear direction/effect with evidence; consistent clinical context and clean mappings.
    """


class NoisePenalty(str, Enum):
    """
    Penalty deduction for data quality and noise levels.
    """
    number_0 = "0"
    """
    Low Noise: Well-curated, ≥85% precision; mechanistic/functional edges; clean, actionable data with no irrelevant edges.
    """
    _1 = "-1"
    """
    Moderate Noise: Substantial fraction of edges generic/ambiguous; precision 70-85%; confidence scoring present but data needs refinement.
    """
    _2 = "-2"
    """
    High Noise: Majority of edges are text-mined/generic with <70% precision; many irrelevant or unscored edges; heavy filtering needed.
    """



class ExtractionResult(ConfiguredBaseModel):
    """
    A result of extracting knowledge on text
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/core'})

    input_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'input_id', 'domain_of': ['ExtractionResult']} })
    input_title: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'input_title', 'domain_of': ['ExtractionResult']} })
    input_text: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'input_text', 'domain_of': ['ExtractionResult']} })
    raw_completion_output: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'raw_completion_output', 'domain_of': ['ExtractionResult']} })
    prompt: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'prompt', 'domain_of': ['ExtractionResult']} })
    extracted_object: Optional[Any] = Field(default=None, description="""The complex objects extracted from the text""", json_schema_extra = { "linkml_meta": {'alias': 'extracted_object', 'domain_of': ['ExtractionResult']} })
    named_entities: Optional[list[Any]] = Field(default=None, description="""Named entities extracted from the text""", json_schema_extra = { "linkml_meta": {'alias': 'named_entities', 'domain_of': ['ExtractionResult']} })


class NamedEntity(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'abstract': True, 'from_schema': 'http://w3id.org/ontogpt/core'})

    id: str = Field(default=..., description="""A unique identifier for the named entity""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['this is populated during the grounding and normalization step'],
         'domain_of': ['NamedEntity', 'Publication']} })
    label: Optional[str] = Field(default=None, description="""The label (name) of the named thing""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'aliases': ['name'],
         'annotations': {'owl': {'tag': 'owl',
                                 'value': 'AnnotationProperty, AnnotationAssertion'}},
         'domain_of': ['NamedEntity'],
         'slot_uri': 'rdfs:label'} })
    original_spans: Optional[list[str]] = Field(default=None, description="""The coordinates of the original text span from which the named entity was extracted, inclusive. For example, \"10:25\" means the span starting from the 10th character and ending with the 25th character. The first character in the text has index 0. Newlines are treated as single characters. Multivalued as there may be multiple spans for a single text.""", json_schema_extra = { "linkml_meta": {'alias': 'original_spans',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['This is determined during grounding and normalization',
                      'But is based on the full input text'],
         'domain_of': ['NamedEntity']} })

    @field_validator('original_spans')
    def pattern_original_spans(cls, v):
        pattern=re.compile(r"^\d+:\d+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid original_spans format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid original_spans format: {v}"
            raise ValueError(err_msg)
        return v


class CompoundExpression(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'abstract': True, 'from_schema': 'http://w3id.org/ontogpt/core'})

    pass


class Triple(CompoundExpression):
    """
    Abstract parent for Relation Extraction tasks
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'abstract': True, 'from_schema': 'http://w3id.org/ontogpt/core'})

    subject: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'subject', 'domain_of': ['Triple']} })
    predicate: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'predicate', 'domain_of': ['Triple']} })
    object: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'object', 'domain_of': ['Triple']} })
    qualifier: Optional[str] = Field(default=None, description="""A qualifier for the statements, e.g. \"NOT\" for negation""", json_schema_extra = { "linkml_meta": {'alias': 'qualifier', 'domain_of': ['Triple']} })
    subject_qualifier: Optional[str] = Field(default=None, description="""An optional qualifier or modifier for the subject of the statement, e.g. \"high dose\" or \"intravenously administered\"""", json_schema_extra = { "linkml_meta": {'alias': 'subject_qualifier', 'domain_of': ['Triple']} })
    object_qualifier: Optional[str] = Field(default=None, description="""An optional qualifier or modifier for the object of the statement, e.g. \"severe\" or \"with additional complications\"""", json_schema_extra = { "linkml_meta": {'alias': 'object_qualifier', 'domain_of': ['Triple']} })


class TextWithTriples(ConfiguredBaseModel):
    """
    A text containing one or more relations of the Triple type.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/core'})

    publication: Optional[Publication] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'publication',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'domain_of': ['TextWithTriples', 'TextWithEntity']} })
    triples: Optional[list[Triple]] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'triples', 'domain_of': ['TextWithTriples']} })


class TextWithEntity(ConfiguredBaseModel):
    """
    A text containing one or more instances of a single type of entity.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/core'})

    publication: Optional[Publication] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'publication',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'domain_of': ['TextWithTriples', 'TextWithEntity']} })
    entities: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'entities', 'domain_of': ['TextWithEntity']} })


class RelationshipType(NamedEntity):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/core',
         'id_prefixes': ['RO', 'biolink']})

    id: str = Field(default=..., description="""A unique identifier for the named entity""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['this is populated during the grounding and normalization step'],
         'domain_of': ['NamedEntity', 'Publication']} })
    label: Optional[str] = Field(default=None, description="""The label (name) of the named thing""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'aliases': ['name'],
         'annotations': {'owl': {'tag': 'owl',
                                 'value': 'AnnotationProperty, AnnotationAssertion'}},
         'domain_of': ['NamedEntity'],
         'slot_uri': 'rdfs:label'} })
    original_spans: Optional[list[str]] = Field(default=None, description="""The coordinates of the original text span from which the named entity was extracted, inclusive. For example, \"10:25\" means the span starting from the 10th character and ending with the 25th character. The first character in the text has index 0. Newlines are treated as single characters. Multivalued as there may be multiple spans for a single text.""", json_schema_extra = { "linkml_meta": {'alias': 'original_spans',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['This is determined during grounding and normalization',
                      'But is based on the full input text'],
         'domain_of': ['NamedEntity']} })

    @field_validator('original_spans')
    def pattern_original_spans(cls, v):
        pattern=re.compile(r"^\d+:\d+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid original_spans format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid original_spans format: {v}"
            raise ValueError(err_msg)
        return v


class Publication(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/core'})

    id: Optional[str] = Field(default=None, description="""The publication identifier""", json_schema_extra = { "linkml_meta": {'alias': 'id', 'domain_of': ['NamedEntity', 'Publication']} })
    title: Optional[str] = Field(default=None, description="""The title of the publication""", json_schema_extra = { "linkml_meta": {'alias': 'title', 'domain_of': ['Publication']} })
    abstract: Optional[str] = Field(default=None, description="""The abstract of the publication""", json_schema_extra = { "linkml_meta": {'alias': 'abstract', 'domain_of': ['Publication']} })
    combined_text: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'combined_text', 'domain_of': ['Publication']} })
    full_text: Optional[str] = Field(default=None, description="""The full text of the publication""", json_schema_extra = { "linkml_meta": {'alias': 'full_text', 'domain_of': ['Publication']} })


class AnnotatorResult(ConfiguredBaseModel):
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/core'})

    subject_text: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'subject_text', 'domain_of': ['AnnotatorResult']} })
    object_id: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'object_id', 'domain_of': ['AnnotatorResult']} })
    object_text: Optional[str] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'object_text', 'domain_of': ['AnnotatorResult']} })


class DataSourceEvaluation(ConfiguredBaseModel):
    """
    A comprehensive evaluation of a data source for inclusion in the MATRIX knowledge graph. This includes metadata about the source, detailed assessments across multiple scoring dimensions, and final computed scores.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/matrix_eval', 'tree_root': True})

    source_name: str = Field(default=..., description="""The full name of the data source being evaluated, including version number if applicable.""", json_schema_extra = { "linkml_meta": {'alias': 'source_name',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'The complete name of the data source, '
                                             'database, or resource, including any '
                                             'version information (e.g., "DrugBank '
                                             'v5.1.9", "STRING v12.0").'}},
         'domain_of': ['DataSourceEvaluation']} })
    source_type: Optional[SourceType] = Field(default=None, description="""The category or type of data source. This must be one of the  following: database, literature corpus, ontology, experimental dataset. If unclear, choose \"database\".""", json_schema_extra = { "linkml_meta": {'alias': 'source_type',
         'annotations': {'prompt.example': {'tag': 'prompt.example',
                                            'value': 'database, literature corpus, '
                                                     'ontology, experimental dataset'}},
         'domain_of': ['DataSourceEvaluation']} })
    url: Optional[str] = Field(default=None, description="""The primary web location where the data source can be accessed or information about it can be found.""", json_schema_extra = { "linkml_meta": {'alias': 'url',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'The URL or web address where the data '
                                             'source is available or described.'}},
         'domain_of': ['DataSourceEvaluation']} })
    publications: Optional[list[str]] = Field(default=None, description="""Semicolon-separated list of key publications describing or citing this data source, including DOIs or PubMed IDs where available.""", json_schema_extra = { "linkml_meta": {'alias': 'publications',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'domain_of': ['DataSourceEvaluation']} })
    description: Optional[str] = Field(default=None, description="""A brief textual description of the data source, its purpose, and its general content.""", json_schema_extra = { "linkml_meta": {'alias': 'description',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'A concise summary of what the data '
                                             'source contains and what it was designed '
                                             'for.'}},
         'domain_of': ['DataSourceEvaluation']} })
    entity_types: Optional[list[str]] = Field(default=None, description="""Semicolon-separated list of the types of biological or chemical entities covered in the data source. Common types include genes, proteins, drugs, diseases, pathways, phenotypes, targets, compounds.""", json_schema_extra = { "linkml_meta": {'alias': 'entity_types',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'List all major entity types present '
                                             '(e.g., genes, drugs, diseases, proteins, '
                                             'pathways, phenotypes, compounds, '
                                             'targets) in a semicolon-separated '
                                             'list.'}},
         'domain_of': ['DataSourceEvaluation']} })
    relation_types: Optional[list[str]] = Field(default=None, description="""Semicolon-separated list of the types of relationships or edges connecting entities in this source. Examples include drug-target, gene-disease, protein-protein interaction, pathway membership, drug-adverse effect.""", json_schema_extra = { "linkml_meta": {'alias': 'relation_types',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'List all major relationship types (e.g., '
                                             'drug-target, gene-disease, drug-drug '
                                             'interaction, protein-protein '
                                             'interaction, indication) in a '
                                             'semicolon-separated list.'}},
         'domain_of': ['DataSourceEvaluation']} })
    descriptor_richness: Optional[str] = Field(default=None, description="""Assessment of the quality and depth of annotations, metadata, and descriptive attributes associated with entities and relations. This includes confidence scores, evidence types, mechanistic details, and contextual information.""", json_schema_extra = { "linkml_meta": {'alias': 'descriptor_richness',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Describe the richness of metadata: Are '
                                             'there confidence scores? Evidence types? '
                                             'Mechanistic details? Effect directions? '
                                             'Clinical context?'}},
         'domain_of': ['DataSourceEvaluation']} })
    descriptor_richness_category: Optional[DescriptorRichness] = Field(default=None, description="""Assessment of the quality and depth of annotations, metadata, and descriptive attributes associated with entities and relations. This includes confidence scores, evidence types, mechanistic details, and contextual information.""", json_schema_extra = { "linkml_meta": {'alias': 'descriptor_richness_category',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Provide one of the following categories '
                                             'for descriptor richness: sparse, '
                                             'moderate, or rich. Do not include any '
                                             'other text for this field.'}},
         'domain_of': ['DataSourceEvaluation']} })
    disease_coverage: Optional[str] = Field(default=None, description="""Description of the breadth of disease coverage, including number of diseases, therapeutic areas represented, and whether coverage is focused on specific conditions or broadly cross-disease.""", json_schema_extra = { "linkml_meta": {'alias': 'disease_coverage',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Describe disease coverage: single '
                                             'disease, specific therapeutic area, '
                                             'multiple diseases, or comprehensive '
                                             'cross-disease coverage. Include '
                                             'approximate numbers if available.'}},
         'domain_of': ['DataSourceEvaluation']} })
    organism_coverage: Optional[str] = Field(default=None, description="""Description of which organisms or species are covered by the data source (e.g., human-only, human and model organisms, multi-species).""", json_schema_extra = { "linkml_meta": {'alias': 'organism_coverage',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Which organisms are covered? Human-only, '
                                             'specific model organisms, or '
                                             'multi-species?'}},
         'domain_of': ['DataSourceEvaluation']} })
    scale: Optional[str] = Field(default=None, description="""The approximate scale of the data source in terms of number of entities, edges/relationships, or records. Provide specific numbers where possible.""", json_schema_extra = { "linkml_meta": {'alias': 'scale',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Approximate scale: How many entities? '
                                             'How many edges/relationships? Use terms '
                                             'like "<10k edges", "10k-100k edges", '
                                             '"100k-1M edges", ">1M edges" if exact '
                                             "numbers aren't available."}},
         'domain_of': ['DataSourceEvaluation']} })
    modality_breadth: Optional[str] = Field(default=None, description="""Description of the diversity of data modalities, experimental methods, or evidence types represented (e.g., single assay type, multiple experimental techniques, diverse evidence including clinical and experimental).""", json_schema_extra = { "linkml_meta": {'alias': 'modality_breadth',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'What modalities or evidence types are '
                                             'included? Single modality (e.g., only '
                                             'text mining), or multiple modalities '
                                             '(e.g., experimental, clinical trials, '
                                             'literature, omics)?'}},
         'domain_of': ['DataSourceEvaluation']} })
    drug_disease_edge_types: Optional[list[str]] = Field(default=None, description="""Semicolon-separated list of specific drug-disease related edge families present. Include Drug-Target (D-T), Target-Disease (T-D), Drug-Disease (D-D), Drug-Adverse Effect (D-AE), and any other relevant drug repurposing edge types.""", json_schema_extra = { "linkml_meta": {'alias': 'drug_disease_edge_types',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'List specific edge types relevant to '
                                             'drug repurposing: Drug-Target, '
                                             'Target-Disease, Drug-Disease, '
                                             'Drug-Adverse Effect, Drug-Pathway, or '
                                             'others. If none are directly present, '
                                             'state "indirect only".'}},
         'domain_of': ['DataSourceEvaluation']} })
    identifier_mapping_quality: Optional[str] = Field(default=None, description="""Assessment of how well entity identifiers in this source align with standard ontologies and identifiers used in MATRIX. Include information about ID systems used and mapping challenges.""", json_schema_extra = { "linkml_meta": {'alias': 'identifier_mapping_quality',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'What identifier systems are used? Do '
                                             'they map cleanly to standard ontologies '
                                             '(e.g., Ensembl, DrugBank, MONDO)? Are '
                                             'mappings readily available or is '
                                             'significant ID reconciliation '
                                             'required?'}},
         'domain_of': ['DataSourceEvaluation']} })
    direction_and_effect: Optional[str] = Field(default=None, description="""Description of whether relationships include directionality (e.g., drug inhibits target vs. drug affects target) and effect information (e.g., activation, inhibition, increase, decrease).""", json_schema_extra = { "linkml_meta": {'alias': 'direction_and_effect',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Are relationships directional? Is effect '
                                             'information included (e.g., inhibition, '
                                             'activation)? Or are relationships '
                                             'generic and undirected?'}},
         'domain_of': ['DataSourceEvaluation']} })
    clinical_context: Optional[str] = Field(default=None, description="""Description of clinical context information available, such as indication status, clinical trial phases, efficacy data, or real-world evidence.""", json_schema_extra = { "linkml_meta": {'alias': 'clinical_context',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Is clinical context provided? E.g., FDA '
                                             'approval status, clinical trial phases, '
                                             'efficacy outcomes, dosing information? '
                                             'Or is the data purely '
                                             'mechanistic/preclinical?'}},
         'domain_of': ['DataSourceEvaluation']} })
    curation_level: Optional[str] = Field(default=None, description="""Description of the level of human curation, expert review, or quality control applied to the data.""", json_schema_extra = { "linkml_meta": {'alias': 'curation_level',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Is the data manually curated by experts, '
                                             'automatically extracted, or a mixture? '
                                             'What quality control processes are '
                                             'applied?'}},
         'domain_of': ['DataSourceEvaluation']} })
    curation_level_category: Optional[CurationLevel] = Field(default=None, description="""Description of the level of human curation, expert review, or quality control applied to the data.""", json_schema_extra = { "linkml_meta": {'alias': 'curation_level_category',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Provide one of the following categories '
                                             'for curation level: manual, '
                                             'semi-automated, automated, or mixed. Do '
                                             'not include any other text for this '
                                             'field.'}},
         'domain_of': ['DataSourceEvaluation']} })
    precision_estimate: Optional[str] = Field(default=None, description="""Estimated precision or accuracy of the data, if known. This may be reported in publications or documentation, or can be qualitatively assessed based on curation methods.""", json_schema_extra = { "linkml_meta": {'alias': 'precision_estimate',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'If available, what is the reported or '
                                             'estimated precision/accuracy? Use terms '
                                             'like "<70%", "70-85%", "≥85%" or '
                                             '"high/medium/low" if quantitative '
                                             "estimates aren't available."}},
         'domain_of': ['DataSourceEvaluation']} })
    noise_sources: Optional[list[str]] = Field(default=None, description="""Semicolon-separated list of potential sources of noise, errors, or low-quality data in this resource. Examples include text mining errors, ambiguous entity resolution, outdated information, generic relationships, unscored edges.""", json_schema_extra = { "linkml_meta": {'alias': 'noise_sources',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'What are the main sources of noise or '
                                             'data quality issues? E.g., text mining '
                                             'errors, ambiguous entities, lack of '
                                             'confidence scores, generic '
                                             'relationships, outdated data.'}},
         'domain_of': ['DataSourceEvaluation']} })
    filtering_needed: Optional[str] = Field(default=None, description="""Description of what level of filtering, cleaning, or post-processing would be required to use this data source effectively.""", json_schema_extra = { "linkml_meta": {'alias': 'filtering_needed',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'How much filtering or cleaning is '
                                             'needed? Minimal (ready to use), moderate '
                                             '(some refinement needed), or heavy '
                                             '(extensive filtering required)?'}},
         'domain_of': ['DataSourceEvaluation']} })
    filtering_needed_category: Optional[FilteringLevel] = Field(default=None, description="""Description of what level of filtering, cleaning, or post-processing would be required to use this data source effectively.""", json_schema_extra = { "linkml_meta": {'alias': 'filtering_needed_category',
         'annotations': {'prompt': {'tag': 'prompt',
                                    'value': 'Provide one of the following categories '
                                             'for filtering level: minimal, moderate, '
                                             'or heavy. Do not include any other text '
                                             'for this field.'}},
         'domain_of': ['DataSourceEvaluation']} })
    domain_coverage_score: DomainCoverageScore = Field(default=..., description="""Computed score for domain coverage based on entity types, relation types, and descriptor richness. Score 1 (Low): Single entity type, sparse/generic relations, few descriptors. Score 2 (Medium): At least two entities, one consistent relation, usable descriptors. Score 3 (High): Three+ entities, multiple relations, rich descriptors enabling multi-hop paths. A resource concerning only a single entity type (e.g., only proteins or  only drugs) should always be scored as 1. This value must be either 1, 2, or 3 with no added punctuation or text.""", json_schema_extra = { "linkml_meta": {'alias': 'domain_coverage_score', 'domain_of': ['DataSourceEvaluation']} })
    source_scope_score: SourceScopeScore = Field(default=..., description="""Computed score for source scope based on disease/organism coverage, scale, and modality breadth. Score 1 (Low): Niche scope, small scale (<10k edges), single modality/therapeutic area. Score 2 (Medium): Multi-disease/organism, mid-scale (10k-100k+ edges), some modality breadth. Score 3 (High): Broad, cross-disease, large-scale (100k-1M+ edges), multiple relation subtypes and modalities. This value must be either 1, 2, or 3 with no added punctuation or text.""", json_schema_extra = { "linkml_meta": {'alias': 'source_scope_score', 'domain_of': ['DataSourceEvaluation']} })
    utility_score: UtilityScore = Field(default=..., description="""Computed score for utility in drug-disease modeling based on direct edge types, ID mapping quality, direction/effect information, and clinical context. Score 1 (Low): Indirect context only; edges sparse, weak, or poorly mapped; no clear D-T/T-D/D-D/AE. Score 2 (Medium): At least one direct edge family; IDs align reasonably; some direction/effect or clinical context present. Score 3 (High): Multiple strong edge families; clear direction/effect with evidence; consistent clinical context and clean mappings. This value must be either 1, 2, or 3 with no added punctuation or text.""", json_schema_extra = { "linkml_meta": {'alias': 'utility_score', 'domain_of': ['DataSourceEvaluation']} })
    noise_penalty: NoisePenalty = Field(default=..., description="""Computed noise penalty based on curation level, precision, and filtering requirements. Deduct 0 (Low Noise): Well-curated, ≥85% precision; mechanistic/functional edges; clean, actionable data with no irrelevant edges. Deduct -1 (Moderate Noise): Substantial fraction of edges generic/ambiguous; precision 70-85%; confidence scoring present but data needs refinement. Deduct -2 (High Noise): Majority of edges are text-mined/generic with <70% precision; many irrelevant or unscored edges; heavy filtering needed. This value must be either 0, -1, or -2 with no added punctuation or text.""", json_schema_extra = { "linkml_meta": {'alias': 'noise_penalty', 'domain_of': ['DataSourceEvaluation']} })
    final_score: Optional[int] = Field(default=None, description="""The final computed score for this data source, calculated as domain_coverage_score + source_scope_score + utility_score + noise_penalty. This provides an overall assessment of source value for MATRIX.""", json_schema_extra = { "linkml_meta": {'alias': 'final_score',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'domain_of': ['DataSourceEvaluation']} })
    recommendation: Optional[str] = Field(default=None, description="""Overall recommendation for this data source (e.g., \"high priority\", \"include with filtering\", \"deprioritize\", \"exclude\"). This should be based on the final score and qualitative considerations.""", json_schema_extra = { "linkml_meta": {'alias': 'recommendation', 'domain_of': ['DataSourceEvaluation']} })


class EntityType(NamedEntity):
    """
    A type of biological or chemical entity represented in a data source.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'annotations': {'annotators': {'tag': 'annotators',
                                        'value': 'sqlite:obo:biolink'}},
         'from_schema': 'http://w3id.org/ontogpt/matrix_eval'})

    id: str = Field(default=..., description="""A unique identifier for the named entity""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['this is populated during the grounding and normalization step'],
         'domain_of': ['NamedEntity', 'Publication']} })
    label: Optional[str] = Field(default=None, description="""The label (name) of the named thing""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'aliases': ['name'],
         'annotations': {'owl': {'tag': 'owl',
                                 'value': 'AnnotationProperty, AnnotationAssertion'}},
         'domain_of': ['NamedEntity'],
         'slot_uri': 'rdfs:label'} })
    original_spans: Optional[list[str]] = Field(default=None, description="""The coordinates of the original text span from which the named entity was extracted, inclusive. For example, \"10:25\" means the span starting from the 10th character and ending with the 25th character. The first character in the text has index 0. Newlines are treated as single characters. Multivalued as there may be multiple spans for a single text.""", json_schema_extra = { "linkml_meta": {'alias': 'original_spans',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['This is determined during grounding and normalization',
                      'But is based on the full input text'],
         'domain_of': ['NamedEntity']} })

    @field_validator('original_spans')
    def pattern_original_spans(cls, v):
        pattern=re.compile(r"^\d+:\d+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid original_spans format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid original_spans format: {v}"
            raise ValueError(err_msg)
        return v


class RelationType(NamedEntity):
    """
    A type of relationship or edge connecting entities in a data source.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'annotations': {'annotators': {'tag': 'annotators',
                                        'value': 'sqlite:obo:biolink, sqlite:obo:ro'}},
         'from_schema': 'http://w3id.org/ontogpt/matrix_eval'})

    id: str = Field(default=..., description="""A unique identifier for the named entity""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['this is populated during the grounding and normalization step'],
         'domain_of': ['NamedEntity', 'Publication']} })
    label: Optional[str] = Field(default=None, description="""The label (name) of the named thing""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'aliases': ['name'],
         'annotations': {'owl': {'tag': 'owl',
                                 'value': 'AnnotationProperty, AnnotationAssertion'}},
         'domain_of': ['NamedEntity'],
         'slot_uri': 'rdfs:label'} })
    original_spans: Optional[list[str]] = Field(default=None, description="""The coordinates of the original text span from which the named entity was extracted, inclusive. For example, \"10:25\" means the span starting from the 10th character and ending with the 25th character. The first character in the text has index 0. Newlines are treated as single characters. Multivalued as there may be multiple spans for a single text.""", json_schema_extra = { "linkml_meta": {'alias': 'original_spans',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['This is determined during grounding and normalization',
                      'But is based on the full input text'],
         'domain_of': ['NamedEntity']} })

    @field_validator('original_spans')
    def pattern_original_spans(cls, v):
        pattern=re.compile(r"^\d+:\d+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid original_spans format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid original_spans format: {v}"
            raise ValueError(err_msg)
        return v


class DrugDiseaseEdgeType(NamedEntity):
    """
    A specific type of relationship relevant to drug-disease modeling and drug repurposing applications.
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'from_schema': 'http://w3id.org/ontogpt/matrix_eval'})

    id: str = Field(default=..., description="""A unique identifier for the named entity""", json_schema_extra = { "linkml_meta": {'alias': 'id',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['this is populated during the grounding and normalization step'],
         'domain_of': ['NamedEntity', 'Publication']} })
    label: Optional[str] = Field(default=None, description="""The label (name) of the named thing""", json_schema_extra = { "linkml_meta": {'alias': 'label',
         'aliases': ['name'],
         'annotations': {'owl': {'tag': 'owl',
                                 'value': 'AnnotationProperty, AnnotationAssertion'}},
         'domain_of': ['NamedEntity'],
         'slot_uri': 'rdfs:label'} })
    original_spans: Optional[list[str]] = Field(default=None, description="""The coordinates of the original text span from which the named entity was extracted, inclusive. For example, \"10:25\" means the span starting from the 10th character and ending with the 25th character. The first character in the text has index 0. Newlines are treated as single characters. Multivalued as there may be multiple spans for a single text.""", json_schema_extra = { "linkml_meta": {'alias': 'original_spans',
         'annotations': {'prompt.skip': {'tag': 'prompt.skip', 'value': 'true'}},
         'comments': ['This is determined during grounding and normalization',
                      'But is based on the full input text'],
         'domain_of': ['NamedEntity']} })

    @field_validator('original_spans')
    def pattern_original_spans(cls, v):
        pattern=re.compile(r"^\d+:\d+$")
        if isinstance(v, list):
            for element in v:
                if isinstance(element, str) and not pattern.match(element):
                    err_msg = f"Invalid original_spans format: {element}"
                    raise ValueError(err_msg)
        elif isinstance(v, str) and not pattern.match(v):
            err_msg = f"Invalid original_spans format: {v}"
            raise ValueError(err_msg)
        return v


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
ExtractionResult.model_rebuild()
NamedEntity.model_rebuild()
CompoundExpression.model_rebuild()
Triple.model_rebuild()
TextWithTriples.model_rebuild()
TextWithEntity.model_rebuild()
RelationshipType.model_rebuild()
Publication.model_rebuild()
AnnotatorResult.model_rebuild()
DataSourceEvaluation.model_rebuild()
EntityType.model_rebuild()
RelationType.model_rebuild()
DrugDiseaseEdgeType.model_rebuild()

