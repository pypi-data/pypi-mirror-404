"""
VibeDNA REST API Server

FastAPI-based REST API for VibeDNA operations.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

import base64
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import io

from vibedna.api.schemas import (
    EncodingScheme,
    EncodeRequest,
    EncodeResponse,
    DecodeRequest,
    DecodeResponse,
    QuickEncodeRequest,
    QuickDecodeRequest,
    ComputeRequest,
    ComputeResponse,
    GateRequest,
    ArithmeticRequest,
    CreateFileRequest,
    FileInfo,
    StorageStats,
    ValidateRequest,
    ValidateResponse,
    SequenceInfo,
    ErrorResponse,
)

COPYRIGHT = "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."

app = FastAPI(
    title="VibeDNA API",
    description="""
Binary ↔ DNA Encoding and Computation API

Convert binary data to DNA sequences, perform computations on DNA,
and manage files in a DNA-based virtual file system.

## Features

- **Encoding**: Convert binary data to DNA sequences with multiple encoding schemes
- **Decoding**: Convert DNA sequences back to binary with error correction
- **Computation**: Perform logic and arithmetic operations on DNA-encoded data
- **File System**: Store and manage files as DNA sequences

---

""" + COPYRIGHT,
    version="1.0.0",
    contact={
        "name": "NeuralQuantum.ai",
        "url": "https://vibecaas.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://neuralquantum.ai/license",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (lazy-loaded)
_encoder = None
_decoder = None
_filesystem = None
_compute_engine = None


def get_encoder():
    """Get or create encoder instance."""
    global _encoder
    if _encoder is None:
        from vibedna.core.encoder import DNAEncoder
        _encoder = DNAEncoder()
    return _encoder


def get_decoder():
    """Get or create decoder instance."""
    global _decoder
    if _decoder is None:
        from vibedna.core.decoder import DNADecoder
        _decoder = DNADecoder()
    return _decoder


def get_filesystem():
    """Get or create filesystem instance."""
    global _filesystem
    if _filesystem is None:
        from vibedna.storage.dna_file_system import DNAFileSystem
        _filesystem = DNAFileSystem()
    return _filesystem


def get_compute_engine():
    """Get or create compute engine instance."""
    global _compute_engine
    if _compute_engine is None:
        from vibedna.compute.dna_logic_gates import DNAComputeEngine
        _compute_engine = DNAComputeEngine()
    return _compute_engine


# ═══════════════════════════════════════════════════════════════
# ROOT ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.get("/", tags=["Info"])
async def root():
    """API information and health check."""
    return {
        "name": "VibeDNA API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "copyright": COPYRIGHT,
    }


@app.get("/health", tags=["Info"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ═══════════════════════════════════════════════════════════════
# ENCODING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/encode", response_model=EncodeResponse, tags=["Encoding"])
async def encode_data(request: EncodeRequest):
    """
    Encode binary data to DNA sequence.

    Accepts base64-encoded data and returns a complete DNA sequence
    with headers, error correction, and metadata.
    """
    from vibedna.core.encoder import DNAEncoder, EncodingConfig
    from vibedna.core.encoder import EncodingScheme as ES

    try:
        # Decode base64 input
        data = base64.b64decode(request.data)

        # Configure encoder
        scheme = ES(request.scheme.value)
        config = EncodingConfig(
            scheme=scheme,
            error_correction=request.error_correction,
        )
        encoder = DNAEncoder(config)

        # Encode
        dna_sequence = encoder.encode(
            data,
            filename=request.filename,
            mime_type=request.mime_type,
        )

        # Calculate checksum
        import hashlib
        checksum = hashlib.sha256(dna_sequence.encode()).hexdigest()[:16]

        return EncodeResponse(
            dna_sequence=dna_sequence,
            nucleotide_count=len(dna_sequence),
            compression_ratio=len(dna_sequence) / len(data) if data else 0,
            encoding_scheme=request.scheme.value,
            checksum=checksum,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/encode/file", tags=["Encoding"])
async def encode_file(
    file: UploadFile = File(...),
    scheme: EncodingScheme = EncodingScheme.quaternary,
    error_correction: bool = True,
    output_format: str = Query("fasta", enum=["fasta", "raw", "json"]),
):
    """
    Encode uploaded file to DNA sequence.

    Returns the DNA sequence as a downloadable file.
    """
    from vibedna.core.encoder import DNAEncoder, EncodingConfig
    from vibedna.core.encoder import EncodingScheme as ES

    try:
        data = await file.read()

        # Configure encoder
        es = ES(scheme.value)
        config = EncodingConfig(scheme=es, error_correction=error_correction)
        encoder = DNAEncoder(config)

        # Encode
        dna_sequence = encoder.encode(
            data,
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
        )

        # Format output
        if output_format == "fasta":
            content = f">VibeDNA:{file.filename}\n"
            for i in range(0, len(dna_sequence), 80):
                content += dna_sequence[i:i + 80] + "\n"
            media_type = "text/plain"
            filename = f"{file.filename}.fasta"
        elif output_format == "json":
            import json
            content = json.dumps({
                "filename": file.filename,
                "scheme": scheme.value,
                "sequence": dna_sequence,
                "length": len(dna_sequence),
                "original_size": len(data),
            })
            media_type = "application/json"
            filename = f"{file.filename}.json"
        else:
            content = dna_sequence
            media_type = "text/plain"
            filename = f"{file.filename}.dna"

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/decode", response_model=DecodeResponse, tags=["Decoding"])
async def decode_sequence(request: DecodeRequest):
    """
    Decode DNA sequence to binary data.

    Performs error correction and integrity verification.
    Returns base64-encoded binary data.
    """
    try:
        decoder = get_decoder()
        result = decoder.decode(request.dna_sequence)

        return DecodeResponse(
            data=base64.b64encode(result.data).decode(),
            filename=result.filename,
            mime_type=result.mime_type,
            original_size=len(result.data),
            errors_corrected=result.errors_corrected,
            integrity_valid=result.integrity_valid,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/decode/file", tags=["Decoding"])
async def decode_to_file(
    file: UploadFile = File(...),
    verify: bool = True,
):
    """
    Decode DNA file and return original binary.

    Accepts FASTA or raw DNA sequence files.
    """
    try:
        content = (await file.read()).decode()

        # Parse DNA from various formats
        dna_sequence = _parse_dna_input(content)

        decoder = get_decoder()
        result = decoder.decode(dna_sequence)

        return Response(
            content=result.data,
            media_type=result.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={result.filename}",
                "X-VibeDNA-Errors-Corrected": str(result.errors_corrected),
                "X-VibeDNA-Integrity-Valid": str(result.integrity_valid),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/quick/encode", tags=["Quick Operations"])
async def quick_encode(request: QuickEncodeRequest):
    """Quick encode text to DNA (no headers)."""
    from vibedna.core.encoder import DNAEncoder, EncodingConfig
    from vibedna.core.encoder import EncodingScheme as ES

    es = ES(request.scheme.value)
    config = EncodingConfig(scheme=es, error_correction=False)
    encoder = DNAEncoder(config)

    dna = encoder.encode_raw(request.text)

    return {"dna_sequence": dna, "length": len(dna)}


@app.post("/quick/decode", tags=["Quick Operations"])
async def quick_decode(request: QuickDecodeRequest):
    """Quick decode DNA to text (no headers)."""
    decoder = get_decoder()
    data = decoder.decode_raw(request.dna_sequence, request.scheme.value)

    try:
        text = data.decode("utf-8")
        return {"text": text, "size": len(data)}
    except UnicodeDecodeError:
        return {
            "text": None,
            "hex": data.hex(),
            "size": len(data),
            "is_binary": True,
        }


# ═══════════════════════════════════════════════════════════════
# COMPUTATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/compute", response_model=ComputeResponse, tags=["Computation"])
async def compute_operation(request: ComputeRequest):
    """
    Perform computation on DNA sequences.

    Supports logic gates (AND, OR, XOR, NOT, NAND, NOR)
    and arithmetic (ADD, SUB, MUL, DIV).
    """
    from vibedna.compute.dna_logic_gates import DNALogicGate

    engine = get_compute_engine()

    try:
        op = request.operation.upper()

        # Logic gates
        if op in ["AND", "OR", "XOR", "NOT", "NAND", "NOR", "XNOR"]:
            gate = DNALogicGate(op.lower())
            result = engine.apply_gate(gate, request.sequence_a, request.sequence_b)
            return ComputeResponse(result=result, operation=op)

        # Arithmetic
        elif op == "ADD":
            result, overflow = engine.add(request.sequence_a, request.sequence_b)
            return ComputeResponse(result=result, operation=op, overflow=overflow)

        elif op == "SUB":
            result, underflow = engine.subtract(request.sequence_a, request.sequence_b)
            return ComputeResponse(result=result, operation=op, overflow=underflow)

        elif op == "MUL":
            result = engine.multiply(request.sequence_a, request.sequence_b)
            return ComputeResponse(result=result, operation=op)

        elif op == "DIV":
            quotient, remainder = engine.divide(request.sequence_a, request.sequence_b)
            return ComputeResponse(result=f"{quotient} R {remainder}", operation=op)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {op}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/compute/gate", tags=["Computation"])
async def compute_gate(request: GateRequest):
    """Apply logic gate to DNA sequences."""
    from vibedna.compute.dna_logic_gates import DNALogicGate

    engine = get_compute_engine()
    gate = DNALogicGate(request.gate.value.lower())

    result = engine.apply_gate(gate, request.sequence_a, request.sequence_b)

    return {
        "result": result,
        "gate": request.gate.value,
        "input_a": request.sequence_a,
        "input_b": request.sequence_b,
    }


@app.post("/compute/arithmetic", tags=["Computation"])
async def compute_arithmetic(request: ArithmeticRequest):
    """Perform arithmetic on DNA sequences."""
    engine = get_compute_engine()

    op = request.operation.value

    if op == "ADD":
        result, flag = engine.add(request.sequence_a, request.sequence_b)
        return {"result": result, "operation": op, "overflow": flag}
    elif op == "SUB":
        result, flag = engine.subtract(request.sequence_a, request.sequence_b)
        return {"result": result, "operation": op, "underflow": flag}
    elif op == "MUL":
        result = engine.multiply(request.sequence_a, request.sequence_b)
        return {"result": result, "operation": op}
    elif op == "DIV":
        quotient, remainder = engine.divide(request.sequence_a, request.sequence_b)
        return {"quotient": quotient, "remainder": remainder, "operation": op}


# ═══════════════════════════════════════════════════════════════
# FILE SYSTEM ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/fs/list", tags=["File System"])
async def list_files(path: str = "/"):
    """List files in DNA storage."""
    from vibedna.storage.dna_file_system import DNAFile, DNADirectory

    fs = get_filesystem()

    try:
        contents = fs.list_directory(path)

        files = []
        directories = []

        for item in contents:
            if isinstance(item, DNAFile):
                files.append(item.to_dict())
            else:
                directories.append(item.to_dict())

        return {
            "path": path,
            "files": files,
            "directories": directories,
            "total_items": len(contents),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/fs/store", tags=["File System"])
async def store_file(
    file: UploadFile = File(...),
    path: str = "/",
    tags: List[str] = Query(default=[]),
):
    """Store file in DNA file system."""
    fs = get_filesystem()

    try:
        data = await file.read()
        file_path = f"{path.rstrip('/')}/{file.filename}"

        dna_file = fs.create_file(
            file_path,
            data,
            mime_type=file.content_type or "application/octet-stream",
            tags=tags,
        )

        return dna_file.to_dict()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/fs/retrieve/{file_path:path}", tags=["File System"])
async def retrieve_file(file_path: str):
    """Retrieve file from DNA storage."""
    fs = get_filesystem()

    try:
        # Ensure path starts with /
        if not file_path.startswith("/"):
            file_path = "/" + file_path

        data = fs.read_file(file_path)
        file_info = fs.get_file_info(file_path)

        return Response(
            content=data,
            media_type=file_info.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_info.name}",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/fs/delete/{file_path:path}", tags=["File System"])
async def delete_file(file_path: str):
    """Delete file from DNA storage."""
    fs = get_filesystem()

    try:
        if not file_path.startswith("/"):
            file_path = "/" + file_path

        fs.delete_file(file_path)
        return {"message": f"Deleted {file_path}", "success": True}

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/fs/stats", response_model=StorageStats, tags=["File System"])
async def storage_stats():
    """Get DNA storage statistics."""
    fs = get_filesystem()
    stats = fs.get_storage_stats()
    return StorageStats(**stats)


@app.get("/fs/sequence/{file_path:path}", tags=["File System"])
async def get_sequence(file_path: str):
    """Get raw DNA sequence for a file."""
    fs = get_filesystem()

    try:
        if not file_path.startswith("/"):
            file_path = "/" + file_path

        sequence = fs.get_raw_sequence(file_path)

        return {
            "path": file_path,
            "sequence": sequence,
            "length": len(sequence),
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# VALIDATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/validate", response_model=ValidateResponse, tags=["Validation"])
async def validate_sequence(request: ValidateRequest):
    """Validate DNA sequence structure."""
    from vibedna.utils.validators import validate_dna_sequence

    is_valid, issues = validate_dna_sequence(
        request.sequence,
        require_header=request.require_header,
        require_footer=request.require_footer,
    )

    return ValidateResponse(is_valid=is_valid, issues=issues)


@app.get("/info/{sequence}", response_model=SequenceInfo, tags=["Validation"])
async def sequence_info(sequence: str):
    """Get detailed information about a DNA sequence."""
    from vibedna.utils.constants import MAGIC_SEQUENCE, END_MARKER

    sequence = sequence.upper()

    # Calculate statistics
    gc_count = sum(1 for n in sequence if n in "GC")
    gc_content = gc_count / len(sequence) if sequence else 0

    nucleotide_counts = {
        "A": sequence.count("A"),
        "T": sequence.count("T"),
        "C": sequence.count("C"),
        "G": sequence.count("G"),
    }

    # Check for VibeDNA structure
    has_header = sequence.startswith(MAGIC_SEQUENCE)
    has_footer = sequence.endswith(END_MARKER) or END_MARKER in sequence[-50:]

    # Detect scheme
    decoder = get_decoder()
    detected_scheme = decoder.detect_encoding_scheme(sequence)

    return SequenceInfo(
        length=len(sequence),
        gc_content=gc_content,
        detected_scheme=detected_scheme,
        nucleotide_counts=nucleotide_counts,
        has_header=has_header,
        has_footer=has_footer,
    )


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _parse_dna_input(content: str) -> str:
    """Parse DNA from various formats."""
    lines = content.strip().split("\n")

    # Check for FASTA format
    if lines[0].startswith(">"):
        return "".join(line.strip() for line in lines[1:] if not line.startswith(">"))

    # Check for JSON format
    if content.strip().startswith("{"):
        import json
        data = json.loads(content)
        return data.get("sequence", "")

    # Raw format
    return "".join(content.split())


# ═══════════════════════════════════════════════════════════════
# STARTUP/SHUTDOWN
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
