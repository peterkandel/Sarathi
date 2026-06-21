# OCR Design for Nepali Citizenship Documents

## Scope
This design covers OCR, preprocessing, field extraction, validation, confidence scoring, and fraud detection for Nepali citizenship documents. It is intended to support both Nepali text extraction and English text extraction in a government-grade environment.

## Structured Outputs

### 1. Architecture
```json
{
  "system_name": "Nepali Citizenship OCR Service",
  "purpose": "Extract, validate, and assess citizenship document content from uploaded images for downstream government services.",
  "design_principles": [
    "Asynchronous document processing",
    "Multi-stage extraction with explicit confidence and validation outputs",
    "Separate Nepali and English text handling with language-aware routing",
    "Government-grade auditability and traceability",
    "Fraud-aware processing with tamper and anomaly signals",
    "Loose coupling between document intake and OCR inference"
  ],
  "logical_components": [
    {
      "name": "Document Intake Adapter",
      "responsibility": "Accepts document images and creates OCR work items.",
      "interfaces": ["create_job", "attach_file", "retrieve_job_status"]
    },
    {
      "name": "Preprocessing Service",
      "responsibility": "Normalizes images before OCR using orientation, denoise, crop, and contrast operations.",
      "interfaces": ["preprocess_image", "score_image_quality"]
    },
    {
      "name": "Language Detection Service",
      "responsibility": "Determines whether image regions contain Nepali, English, or mixed-script content.",
      "interfaces": ["detect_language", "route_by_script"]
    },
    {
      "name": "OCR Inference Service",
      "responsibility": "Performs OCR for Devanagari and Latin scripts.",
      "interfaces": ["extract_text", "extract_lines", "extract_words"]
    },
    {
      "name": "Field Extraction Service",
      "responsibility": "Maps OCR output to citizenship document fields.",
      "interfaces": ["extract_fields", "normalize_values"]
    },
    {
      "name": "Validation Service",
      "responsibility": "Checks field completeness, format, cross-field consistency, and reference data constraints.",
      "interfaces": ["validate_fields", "validate_document"]
    },
    {
      "name": "Confidence Scoring Service",
      "responsibility": "Produces document-level, field-level, and page-level confidence signals.",
      "interfaces": ["score_confidence"]
    },
    {
      "name": "Fraud Detection Service",
      "responsibility": "Detects tampering, duplication, inconsistency, and suspicious submission patterns.",
      "interfaces": ["detect_fraud", "score_risk"]
    },
    {
      "name": "Audit Publisher",
      "responsibility": "Emits immutable processing events for oversight and traceability.",
      "interfaces": ["publish_audit_event"]
    }
  ],
  "deployment_view": {
    "runtime": "Containerized asynchronous workers behind a FastAPI control plane",
    "storage": [
      "PostgreSQL for job and metadata state",
      "Redis for queue coordination, rate limiting, and temporary state",
      "S3-compatible object storage for original images and artifacts"
    ],
    "scaling_model": "Horizontally scaled stateless API layer with independently scaled worker pools for preprocessing, OCR, validation, and fraud analysis"
  },
  "integration_points": [
    "Document Intake Service",
    "Audit & Records Service",
    "Reference Policy Service",
    "Service Orchestration Service"
  ]
}
```

### 2. Pipeline
```json
{
  "pipeline_name": "Citizenship OCR Pipeline",
  "stages": [
    {
      "stage": 1,
      "name": "Job Creation",
      "inputs": ["document image metadata", "citizen reference", "document type"],
      "outputs": ["ocr_job_id", "processing_plan"],
      "notes": "Creates an auditable work item and assigns processing priority."
    },
    {
      "stage": 2,
      "name": "Image Validation",
      "inputs": ["original image"],
      "outputs": ["file_integrity_result", "image_quality_result"],
      "notes": "Rejects unreadable, corrupted, or unsupported files early."
    },
    {
      "stage": 3,
      "name": "Preprocessing",
      "inputs": ["original image", "quality signals"],
      "outputs": ["normalized image", "preprocessing_metadata"],
      "notes": "Applies orientation correction, denoising, perspective correction, crop normalization, and contrast enhancement."
    },
    {
      "stage": 4,
      "name": "Script and Language Detection",
      "inputs": ["normalized image"],
      "outputs": ["script_map", "language_map"],
      "notes": "Identifies Nepali Devanagari regions, English Latin regions, and mixed-script areas."
    },
    {
      "stage": 5,
      "name": "OCR Inference",
      "inputs": ["script_map", "normalized image"],
      "outputs": ["text_lines", "text_words", "character_confidence"],
      "notes": "Runs script-aware OCR and returns structured text with bounding boxes."
    },
    {
      "stage": 6,
      "name": "Field Extraction",
      "inputs": ["text_lines", "text_words", "document template rules"],
      "outputs": ["field_candidates", "normalized_field_values"],
      "notes": "Extracts citizenship number, name, date of birth, issue details, district, and related fields."
    },
    {
      "stage": 7,
      "name": "Validation",
      "inputs": ["normalized_field_values", "reference data"],
      "outputs": ["validation_result", "field_errors"],
      "notes": "Checks required fields, pattern rules, checksum-like formats where applicable, and cross-field consistency."
    },
    {
      "stage": 8,
      "name": "Confidence Scoring",
      "inputs": ["ocr results", "field extraction results", "validation results"],
      "outputs": ["document_confidence", "field_confidences", "risk_confidence"],
      "notes": "Produces confidence at document and field levels and marks low-trust outputs for review."
    },
    {
      "stage": 9,
      "name": "Fraud Detection",
      "inputs": ["original image", "preprocessing metadata", "extracted text", "submission history"],
      "outputs": ["fraud_score", "fraud_signals", "review_required_flag"],
      "notes": "Detects tampering, duplication, template mismatch, improbable edits, and suspicious reuse patterns."
    },
    {
      "stage": 10,
      "name": "Publish Results",
      "inputs": ["final extraction package"],
      "outputs": ["submission-ready payload", "audit events"],
      "notes": "Persists outputs and emits events to the Document Intake and Audit services."
    }
  ],
  "routing_rules": {
    "nepali_text": "Use Devanagari OCR path and Nepali normalization rules.",
    "english_text": "Use Latin OCR path and English normalization rules.",
    "mixed_script": "Run parallel OCR paths and merge field candidates by region and context.",
    "low_confidence": "Route to human review and mark the submission as needing confirmation."
  }
}
```

### 3. Models
```json
{
  "models": [
    {
      "name": "Image Quality Model",
      "purpose": "Assess blur, glare, skew, crop completeness, and compression artifacts.",
      "input": ["image"],
      "output": ["quality_score", "quality_flags"],
      "metrics": ["blur_detected", "glare_detected", "skew_angle", "crop_completeness"]
    },
    {
      "name": "Script and Language Detector",
      "purpose": "Detect Devanagari, Latin, and mixed-script regions.",
      "input": ["image or text region"],
      "output": ["script_label", "language_label", "region_boxes"],
      "metrics": ["script_precision", "script_recall"]
    },
    {
      "name": "Nepali OCR Model",
      "purpose": "Extract Nepali text from Devanagari script.",
      "input": ["normalized Devanagari image region"],
      "output": ["text", "word_boxes", "character_confidence"],
      "metrics": ["character_error_rate", "word_error_rate"]
    },
    {
      "name": "English OCR Model",
      "purpose": "Extract English text from Latin script.",
      "input": ["normalized Latin image region"],
      "output": ["text", "word_boxes", "character_confidence"],
      "metrics": ["character_error_rate", "word_error_rate"]
    },
    {
      "name": "Field Extraction Model",
      "purpose": "Map OCR output to citizenship document fields.",
      "input": ["ocr_text", "layout_features", "template metadata"],
      "output": ["field_candidates", "confidence_by_field"],
      "metrics": ["field_f1", "field_exact_match"]
    },
    {
      "name": "Validation Rules Engine",
      "purpose": "Apply deterministic checks for required fields, formats, and cross-field consistency.",
      "input": ["field values", "reference data"],
      "output": ["validation_passed", "validation_errors"],
      "metrics": ["false_reject_rate", "false_accept_rate"]
    },
    {
      "name": "Fraud Detection Model",
      "purpose": "Identify forged, altered, reused, or suspicious documents.",
      "input": ["image features", "OCR output", "submission history", "metadata anomalies"],
      "output": ["fraud_score", "fraud_signals", "review_required"],
      "metrics": ["fraud_detection_precision", "fraud_detection_recall"]
    },
    {
      "name": "Confidence Aggregator",
      "purpose": "Combine OCR, extraction, validation, and fraud signals into a unified confidence view.",
      "input": ["model confidences", "validation results", "fraud score"],
      "output": ["document_confidence", "field_confidence", "final_risk_level"],
      "metrics": ["calibration_error", "ranking_quality"]
    }
  ],
  "model_selection_policy": {
    "primary_choice": "Use a hybrid system combining deep OCR models for text extraction and deterministic rules for validation.",
    "fallback": "Route to human review when confidence is below threshold or fraud risk is elevated.",
    "thresholds": {
      "auto_accept_document_confidence": 0.92,
      "human_review_document_confidence": 0.75,
      "fraud_review_threshold": 0.7
    }
  }
}
```

### 4. API Contracts
```json
{
  "api_version": "v1",
  "base_path": "/ocr/v1",
  "authentication": {
    "scheme": "Bearer JWT",
    "service_access": "mTLS plus signed service token for system-to-system calls"
  },
  "endpoints": [
    {
      "method": "POST",
      "path": "/jobs",
      "purpose": "Create an OCR processing job.",
      "authorization": ["citizen access for own document uploads", "Document Intake service access"],
      "request_schema": {
        "type": "object",
        "required": ["document_id", "file_id", "document_type_code"],
        "properties": {
          "document_id": { "type": "string", "format": "uuid" },
          "file_id": { "type": "string", "format": "uuid" },
          "document_type_code": { "type": "string" },
          "priority": { "type": "string", "enum": ["normal", "high"] }
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["job_id", "status", "created_at"],
        "properties": {
          "job_id": { "type": "string", "format": "uuid" },
          "status": { "type": "string", "enum": ["queued", "running", "completed", "failed"] },
          "created_at": { "type": "string", "format": "date-time" }
        }
      },
      "error_responses": [400, 401, 403, 404, 413, 422, 429]
    },
    {
      "method": "GET",
      "path": "/jobs/{job_id}",
      "purpose": "Retrieve OCR job status and outputs.",
      "authorization": ["Document Intake service access", "authorized support access", "audit access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "job_id": { "type": "string", "format": "uuid" }
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["job_id", "status"],
        "properties": {
          "job_id": { "type": "string", "format": "uuid" },
          "status": { "type": "string" },
          "document_confidence": { "type": "number" },
          "field_confidences": { "type": "array", "items": { "type": "object" } },
          "extracted_text": { "type": "object" },
          "validation_result": { "type": "object" },
          "fraud_result": { "type": "object" }
        }
      },
      "error_responses": [401, 403, 404]
    },
    {
      "method": "POST",
      "path": "/jobs/{job_id}/reprocess",
      "purpose": "Re-run OCR and downstream analysis using updated models or settings.",
      "authorization": ["operator access", "Document Intake service access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "model_version": { "type": "string" },
          "force_human_review": { "type": "boolean" }
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["job_id", "status"],
        "properties": {
          "job_id": { "type": "string", "format": "uuid" },
          "status": { "type": "string" },
          "queued_at": { "type": "string", "format": "date-time" }
        }
      },
      "error_responses": [401, 403, 404, 409, 422]
    },
    {
      "method": "GET",
      "path": "/jobs/{job_id}/confidence",
      "purpose": "Retrieve confidence scores and component-level evidence.",
      "authorization": ["Document Intake service access", "audit access"],
      "request_schema": {
        "type": "object",
        "properties": {
          "job_id": { "type": "string", "format": "uuid" }
        }
      },
      "response_schema": {
        "type": "object",
        "required": ["job_id", "confidence"],
        "properties": {
          "job_id": { "type": "string", "format": "uuid" },
          "confidence": { "type": "number" },
          "field_confidence": { "type": "array", "items": { "type": "object" } },
          "risk_level": { "type": "string", "enum": ["low", "medium", "high"] }
        }
      },
      "error_responses": [401, 403, 404]
    }
  ]
}
```

### 5. Data Schemas
```json
{
  "data_model": {
    "job": {
      "description": "Represents a single OCR processing request.",
      "fields": {
        "job_id": "uuid",
        "document_id": "uuid",
        "file_id": "uuid",
        "document_type_code": "string",
        "status": "string",
        "priority": "string",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    },
    "page": {
      "description": "Represents one page of a document.",
      "fields": {
        "page_id": "uuid",
        "job_id": "uuid",
        "page_number": "integer",
        "storage_key": "string",
        "quality_score": "number",
        "script_labels": ["string"],
        "created_at": "datetime"
      }
    },
    "extracted_text": {
      "description": "Structured OCR output for mixed Nepali and English content.",
      "fields": {
        "text_block_id": "uuid",
        "job_id": "uuid",
        "language": "string",
        "script": "string",
        "text": "string",
        "confidence": "number",
        "bbox": {
          "x": "number",
          "y": "number",
          "width": "number",
          "height": "number"
        }
      }
    },
    "field_value": {
      "description": "Normalized citizenship field extracted from OCR output.",
      "fields": {
        "field_id": "uuid",
        "job_id": "uuid",
        "field_name": "string",
        "raw_value": "string",
        "normalized_value": "string",
        "confidence": "number",
        "validation_status": "string",
        "source_language": "string"
      }
    },
    "validation_result": {
      "description": "Validation outcome for a field or a complete document.",
      "fields": {
        "validation_id": "uuid",
        "job_id": "uuid",
        "status": "string",
        "issues": [
          {
            "code": "string",
            "field_name": "string",
            "message": "string",
            "severity": "string"
          }
        ]
      }
    },
    "fraud_result": {
      "description": "Fraud and tamper analysis outcome.",
      "fields": {
        "fraud_id": "uuid",
        "job_id": "uuid",
        "risk_score": "number",
        "signals": [
          {
            "code": "string",
            "description": "string",
            "severity": "string"
          }
        ],
        "review_required": "boolean"
      }
    }
  },
  "field_catalog": [
    "citizenship_number",
    "full_name_nepali",
    "full_name_english",
    "date_of_birth",
    "gender",
    "district",
    "municipality_or_vdc",
    "ward_number",
    "issue_date",
    "issue_office",
    "document_serial_number",
    "father_name",
    "mother_name",
    "spouse_name",
    "permanent_address",
    "citizenship_type"
  ],
  "storage_strategy": {
    "original_image": "S3 object per file",
    "normalized_image": "S3 object per stage output",
    "structured_output": "PostgreSQL JSONB",
    "audit_trail": "Append-only audit records"
  }
}
```

### 6. Failure Handling
```json
{
  "failure_policy": {
    "principles": [
      "Fail closed for suspicious documents",
      "Preserve original input and intermediate artifacts for audit",
      "Return deterministic error codes",
      "Use retry only for transient failures",
      "Route low-confidence or fraud-suspect cases to human review"
    ],
    "error_catalog": [
      {
        "code": "OCR-4001",
        "name": "invalid_file_format",
        "condition": "Uploaded file is not a supported image or PDF format.",
        "user_action": "Resubmit a supported file type."
      },
      {
        "code": "OCR-4002",
        "name": "file_too_large",
        "condition": "File exceeds allowed upload size.",
        "user_action": "Compress or crop the image and try again."
      },
      {
        "code": "OCR-4003",
        "name": "image_quality_too_low",
        "condition": "Blur, glare, or crop completeness is below threshold.",
        "user_action": "Retake the image with better lighting and framing."
      },
      {
        "code": "OCR-5001",
        "name": "preprocessing_failed",
        "condition": "Normalization or image transformation failed.",
        "user_action": "Retry automatically; if repeated, resubmit the file."
      },
      {
        "code": "OCR-5002",
        "name": "ocr_inference_failed",
        "condition": "OCR engine produced no usable output or crashed.",
        "user_action": "Retry automatically; if repeated, escalate for review."
      },
      {
        "code": "OCR-5003",
        "name": "field_extraction_incomplete",
        "condition": "Required fields could not be extracted with acceptable confidence.",
        "user_action": "Review manually or capture a clearer image."
      },
      {
        "code": "OCR-5004",
        "name": "validation_failed",
        "condition": "Extracted values violate format, range, or consistency rules.",
        "user_action": "Correct the reviewed fields and resubmit."
      },
      {
        "code": "OCR-5005",
        "name": "fraud_suspected",
        "condition": "Tamper or anomaly score exceeds the review threshold.",
        "user_action": "Send to manual review and block auto-acceptance."
      },
      {
        "code": "OCR-5031",
        "name": "dependency_unavailable",
        "condition": "Reference policy, storage, or downstream service is unavailable.",
        "user_action": "Retry after service recovery; preserve job state."
      }
    ],
    "retry_strategy": {
      "transient_errors": "Retry with exponential backoff and bounded attempts.",
      "permanent_errors": "Do not retry; mark the job failed and present user guidance.",
      "dead_lettering": "Move repeatedly failing jobs to a dead-letter queue for operations review."
    },
    "human_review_triggers": [
      "Document confidence below threshold",
      "Any critical field confidence below threshold",
      "Fraud risk above threshold",
      "Validation failure on key identity fields",
      "Mixed-script ambiguity unresolved after dual OCR"
    ],
    "observability": {
      "logs": ["job lifecycle", "preprocessing metrics", "model versions", "validation errors", "fraud signals"],
      "metrics": ["job latency", "success rate", "confidence distribution", "fraud review rate"],
      "traces": ["upload to OCR", "OCR to extraction", "extraction to validation", "validation to publish"]
    }
  }
}
```

### 7. Operational Output Contract
```json
{
  "ocr_result": {
    "job_id": "uuid",
    "document_id": "uuid",
    "status": "completed",
    "language_breakdown": [
      {
        "language": "ne",
        "confidence": 0.98
      },
      {
        "language": "en",
        "confidence": 0.93
      }
    ],
    "document_confidence": 0.94,
    "field_confidences": [
      {
        "field_name": "citizenship_number",
        "confidence": 0.99
      },
      {
        "field_name": "full_name_nepali",
        "confidence": 0.96
      }
    ],
    "validation_status": "passed",
    "fraud_risk": "low",
    "next_action": "auto_accept"
  }
}
```

## Recommendation
Use a hybrid OCR architecture: script-aware OCR models for Nepali and English, deterministic preprocessing and validation, and a fraud detection layer that can block, downgrade, or route suspicious documents to manual review. This preserves accuracy, auditability, and government trust while keeping the pipeline horizontally scalable.
