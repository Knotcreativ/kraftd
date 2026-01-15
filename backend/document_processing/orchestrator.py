"""
Orchestrator Stage: Chain all 4 document processing stages into an integrated pipeline.

Pipeline Flow:
  1. Classifier - Identify document type (RFQ, PO, Invoice, etc.)
  2. Mapper - Extract structured fields into KraftdDocument schema
  3. Inferencer - Apply business logic (calculate totals, infer currency, etc.)
  4. Validator - Score completeness and quality, identify gaps

Returns: KraftdDocument with full metadata, scores, and readiness assessment.
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime
from .schemas import KraftdDocument, DocumentType
from .classifier import UniversalClassifier
from .mapper import map_document
from .inferencer import infer_document
from .validator import validate_document, ValidationResult


class ExtractionPipeline:
    """
    Orchestrates all 4 document processing stages.
    
    Usage:
        pipeline = ExtractionPipeline()
        result = pipeline.process_document(text)
        
        print(result.document.metadata.document_type)
        print(result.validation_result.completeness_score)
        print(result.is_ready_for_processing)
    """
    
    def __init__(self):
        """Initialize pipeline stages"""
        self.classifier = UniversalClassifier()
    
    def process_document(self, text: str, source_file: str = None) -> "PipelineResult":
        """
        Process a document through all 4 stages.
        
        Args:
            text: Document text (extracted from PDF, Word, etc.)
            source_file: Optional source filename for tracking
            
        Returns:
            PipelineResult with document, metadata, and validation results
        """
        
        start_time = datetime.now()
        
        # Stage 1: Classification
        classification = self._stage_classify(text)
        if not classification['success']:
            return PipelineResult.from_error(
                error=f"Classification failed: {classification['error']}",
                source_file=source_file,
                stage_failed="classifier"
            )
        
        # Stage 2: Field Mapping
        mapping = self._stage_map(text, classification['document_type'])
        if not mapping['success']:
            return PipelineResult.from_error(
                error=f"Mapping failed: {mapping['error']}",
                source_file=source_file,
                stage_failed="mapper"
            )
        
        # Stage 3: Field Inference
        inference = self._stage_infer(mapping['document'], text)
        if not inference['success']:
            return PipelineResult.from_error(
                error=f"Inference failed: {inference['error']}",
                source_file=source_file,
                stage_failed="inferencer"
            )
        
        # Stage 4: Validation
        validation = self._stage_validate(inference['document'])
        if not validation['success']:
            return PipelineResult.from_error(
                error=f"Validation failed: {validation['error']}",
                source_file=source_file,
                stage_failed="validator"
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Build result
        return PipelineResult(
            success=True,
            document=inference['document'],
            validation_result=validation['result'],
            source_file=source_file,
            processing_time_seconds=processing_time,
            stages_completed=["classifier", "mapper", "inferencer", "validator"],
            classifier_confidence=classification['confidence'],
            mapping_signals=mapping['signals_count'],
            inference_signals=len(inference['signals'])
        )
    
    def _stage_classify(self, text: str) -> Dict:
        """Stage 1: Classify document type"""
        try:
            result = self.classifier.classify(text)
            return {
                'success': True,
                'document_type': result.document_type,
                'confidence': result.confidence
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _stage_map(self, text: str, doc_type) -> Dict:
        """Stage 2: Extract fields into structured schema"""
        try:
            document = map_document(text)
            signals_count = self._count_extraction_signals(document)
            
            return {
                'success': True,
                'document': document,
                'signals_count': signals_count
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _stage_infer(self, document: KraftdDocument, text: str) -> Dict:
        """Stage 3: Apply business logic rules"""
        try:
            document, signals = infer_document(document, text)
            
            return {
                'success': True,
                'document': document,
                'signals': signals
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _stage_validate(self, document: KraftdDocument) -> Dict:
        """Stage 4: Score completeness and quality"""
        try:
            result = validate_document(document)
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _count_extraction_signals(self, document: KraftdDocument) -> int:
        """Count how many fields were extracted in mapping stage"""
        count = 0
        
        try:
            # Parties (dict-based)
            if document.parties:
                count += len(document.parties)
            
            # Dates
            if document.dates:
                if document.dates.issue_date:
                    count += 1
                if document.dates.submission_deadline:
                    count += 1
                if document.dates.delivery_date:
                    count += 1
                if document.dates.validity_date:
                    count += 1
            
            # Commercial Terms
            if document.commercial_terms:
                if document.commercial_terms.currency:
                    count += 1
                if document.commercial_terms.payment_terms:
                    count += 1
                if document.commercial_terms.incoterms:
                    count += 1
                if document.commercial_terms.vat_rate:
                    count += 1
            
            # Line Items
            if document.line_items:
                count += len(document.line_items)
        
        except Exception as e:
            pass
        
        return count


class PipelineResult:
    """Result of a document passing through the entire extraction pipeline"""
    
    def __init__(
        self,
        success: bool = True,
        document: KraftdDocument = None,
        validation_result: ValidationResult = None,
        source_file: str = None,
        processing_time_seconds: float = 0.0,
        stages_completed: List[str] = None,
        classifier_confidence: float = 0.0,
        mapping_signals: int = 0,
        inference_signals: int = 0,
        error: str = None,
        stage_failed: str = None
    ):
        self.success = success
        self.document = document
        self.validation_result = validation_result
        self.source_file = source_file
        self.processing_time_seconds = processing_time_seconds
        self.stages_completed = stages_completed or []
        self.classifier_confidence = classifier_confidence
        self.mapping_signals = mapping_signals
        self.inference_signals = inference_signals
        self.error = error
        self.stage_failed = stage_failed
    
    @classmethod
    def from_error(cls, error: str, source_file: str = None, stage_failed: str = None):
        """Create a failed result"""
        return cls(
            success=False,
            error=error,
            source_file=source_file,
            stage_failed=stage_failed
        )
    
    @property
    def is_ready_for_processing(self) -> bool:
        """Can this document be auto-processed?"""
        if not self.success:
            return False
        if not self.validation_result:
            return False
        return self.validation_result.ready_for_processing
    
    @property
    def needs_manual_review(self) -> bool:
        """Does this document need human review?"""
        if not self.success:
            return True
        if not self.validation_result:
            return True
        return self.validation_result.requires_manual_review
    
    def get_summary(self) -> Dict:
        """Get a summary of the extraction result"""
        
        if not self.success:
            return {
                'success': False,
                'error': self.error,
                'stage_failed': self.stage_failed,
                'source_file': self.source_file
            }
        
        doc_type = 'UNKNOWN'
        if self.document and self.document.metadata:
            doc_type = self.document.metadata.document_type.value
        
        return {
            'success': True,
            'document_type': doc_type,
            'source_file': self.source_file,
            'processing_time_seconds': round(self.processing_time_seconds, 2),
            'classification': {
                'type': doc_type,
                'confidence': round(self.classifier_confidence, 2)
            },
            'extraction': {
                'fields_mapped': self.mapping_signals,
                'inferences_made': self.inference_signals,
                'parties_found': len(self.document.parties) if self.document and self.document.parties else 0,
                'line_items': len(self.document.line_items) if self.document and self.document.line_items else 0
            },
            'validation': {
                'completeness_score': round(self.validation_result.completeness_score, 1) if self.validation_result else 0,
                'data_quality_score': round(self.validation_result.data_quality_score, 1) if self.validation_result else 0,
                'overall_score': round(self.validation_result.overall_score, 1) if self.validation_result else 0,
                'critical_gaps': len(self.validation_result.critical_gaps) if self.validation_result else 0,
                'important_gaps': len(self.validation_result.important_gaps) if self.validation_result else 0,
                'anomalies': len(self.validation_result.anomalies) if self.validation_result else 0
            },
            'readiness': {
                'ready_for_processing': self.is_ready_for_processing,
                'requires_manual_review': self.needs_manual_review
            }
        }
    
    def print_summary(self):
        """Print a formatted summary"""
        summary = self.get_summary()
        
        if not summary['success']:
            print(f"\n[FAILED] EXTRACTION FAILED")
            print(f"   Stage: {summary['stage_failed']}")
            print(f"   Error: {summary['error']}")
            return
        
        print("\n" + "="*80)
        print(f"[SUCCESS] DOCUMENT EXTRACTION COMPLETE")
        print("="*80)
        
        # Document info
        print(f"\n[DOCUMENT]")
        print(f"   Type: {summary['classification']['type']}")
        print(f"   Confidence: {summary['classification']['confidence']:.0%}")
        print(f"   File: {summary['source_file'] or 'N/A'}")
        print(f"   Processing Time: {summary['processing_time_seconds']:.2f}s")
        
        # Extraction metrics
        print(f"\n[EXTRACTION METRICS]")
        print(f"   Fields Mapped: {summary['extraction']['fields_mapped']}")
        print(f"   Inferences Made: {summary['extraction']['inferences_made']}")
        print(f"   Parties Found: {summary['extraction']['parties_found']}")
        print(f"   Line Items: {summary['extraction']['line_items']}")
        
        # Validation scores
        print(f"\n[VALIDATION SCORES]")
        print(f"   Completeness: {summary['validation']['completeness_score']:.0f}%")
        print(f"   Data Quality: {summary['validation']['data_quality_score']:.0f}%")
        print(f"   Overall Score: {summary['validation']['overall_score']:.0f}%")
        
        # Issues
        print(f"\n[ISSUES]")
        print(f"   Critical Gaps: {summary['validation']['critical_gaps']}")
        print(f"   Important Gaps: {summary['validation']['important_gaps']}")
        print(f"   Anomalies: {summary['validation']['anomalies']}")
        
        # Readiness
        print(f"\n[READINESS]")
        if summary['readiness']['ready_for_processing']:
            print(f"   [OK] Ready for Auto-Processing")
        else:
            print(f"   [NO] NOT Ready for Auto-Processing")
        
        if summary['readiness']['requires_manual_review']:
            print(f"   [WARN] Requires Manual Review")
        else:
            print(f"   [OK] No Manual Review Needed")
        
        print("\n" + "="*80)


def create_pipeline() -> ExtractionPipeline:
    """Factory to create a new pipeline instance"""
    return ExtractionPipeline()


def process_document(text: str, source_file: str = None) -> PipelineResult:
    """
    Convenience function to process a document through the full extraction pipeline.
    
    Usage:
        from orchestrator import process_document
        
        result = process_document(extracted_text, source_file="doc.pdf")
        
        if result.is_ready_for_processing:
            # Auto-process
            process_order(result.document)
        elif result.needs_manual_review:
            # Add to manual review queue
            queue_for_review(result)
    """
    pipeline = ExtractionPipeline()
    return pipeline.process_document(text, source_file)
