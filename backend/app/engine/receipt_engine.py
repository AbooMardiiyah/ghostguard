"""Receipt forensics — EXIF, pHash, VAT math check."""

import io
import hashlib
from decimal import Decimal
from datetime import datetime, timezone

from app.models.schemas import LayerFinding


NIGERIAN_VAT_RATE = Decimal("0.075")


def check_vat_math(subtotal: Decimal, stated_vat: Decimal) -> dict:
    """Check if stated VAT matches 7.5% of subtotal."""
    expected_vat = (subtotal * NIGERIAN_VAT_RATE).quantize(Decimal("0.01"))
    diff = abs(stated_vat - expected_vat)
    matches = diff <= Decimal("1.00")  # Allow ₦1 rounding tolerance
    return {
        "subtotal": float(subtotal),
        "stated_vat": float(stated_vat),
        "expected_vat": float(expected_vat),
        "difference": float(diff),
        "matches": matches,
    }


async def analyze_receipt(
    image_bytes: bytes,
    claimed_amount: float,
    claimed_vat: float | None = None,
    employee_id: str | None = None,
    db=None,
) -> dict:
    """Analyze a receipt image for forensic red flags."""
    findings = []
    steps = []

    # Step 1: EXIF extraction
    exif_data = {}
    try:
        from PIL import Image
        import piexif

        img = Image.open(io.BytesIO(image_bytes))
        steps.append(
            {
                "step": "exif_extraction",
                "status": "complete",
                "detail": f"Image: {img.size[0]}x{img.size[1]}",
            }
        )

        if img.info.get("exif"):
            exif_dict = piexif.load(img.info["exif"])
            # Check for software editing markers
            ifd = exif_dict.get("0th", {})
            software = ifd.get(piexif.ImageIFD.Software, b"").decode(
                "utf-8", errors="ignore"
            )
            if software and any(
                s in software.lower() for s in ["photoshop", "gimp", "canva"]
            ):
                exif_data["software"] = software
                findings.append(
                    LayerFinding(
                        layer="process",
                        signal="receipt_edited",
                        description=f"Receipt image edited with {software}",
                        evidence={"software": software},
                        points=30,
                        source="receipt_engine",
                    )
                )
                steps.append(
                    {
                        "step": "exif_software_check",
                        "status": "flagged",
                        "detail": f"Edited with {software}",
                    }
                )
            else:
                steps.append(
                    {
                        "step": "exif_software_check",
                        "status": "clean",
                        "detail": "No editing software detected",
                    }
                )
        else:
            steps.append(
                {
                    "step": "exif_extraction",
                    "status": "info",
                    "detail": "No EXIF data found (stripped)",
                }
            )
    except Exception as e:
        steps.append({"step": "exif_extraction", "status": "error", "detail": str(e)})

    # Step 2: Perceptual hash + duplicate check
    phash_value = None
    try:
        from PIL import Image
        import imagehash

        img = Image.open(io.BytesIO(image_bytes))
        phash_value = str(imagehash.phash(img))
        steps.append(
            {
                "step": "phash_computation",
                "status": "complete",
                "detail": f"pHash: {phash_value}",
            }
        )

        # Check for duplicates in DB
        if db and phash_value:
            cursor = await db.execute(
                "SELECT receipt_id, employee_id, expense_date, amount FROM receipt_hashes WHERE phash = ?",
                (phash_value,),
            )
            existing = await cursor.fetchone()
            if existing:
                findings.append(
                    LayerFinding(
                        layer="process",
                        signal="duplicate_receipt",
                        description=f"Receipt matches previously submitted receipt {existing['receipt_id']}",
                        evidence={
                            "matching_receipt": existing["receipt_id"],
                            "original_employee": existing["employee_id"],
                            "original_date": existing["expense_date"],
                        },
                        points=40,
                        source="receipt_engine",
                    )
                )
                steps.append(
                    {
                        "step": "duplicate_check",
                        "status": "flagged",
                        "detail": f"Matches {existing['receipt_id']}",
                    }
                )
            else:
                steps.append(
                    {
                        "step": "duplicate_check",
                        "status": "clean",
                        "detail": "No duplicate found",
                    }
                )

            # Store the hash
            receipt_id = f"RCP-{hashlib.md5(image_bytes).hexdigest()[:8].upper()}"
            await db.execute(
                """INSERT OR IGNORE INTO receipt_hashes (receipt_id, phash, employee_id, amount, uploaded_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    receipt_id,
                    phash_value,
                    employee_id,
                    claimed_amount,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            await db.commit()
    except Exception as e:
        steps.append({"step": "phash_computation", "status": "error", "detail": str(e)})

    # Step 3: VAT math check
    if claimed_vat is not None:
        subtotal = Decimal(str(claimed_amount)) - Decimal(str(claimed_vat))
        vat_result = check_vat_math(subtotal, Decimal(str(claimed_vat)))
        if not vat_result["matches"]:
            findings.append(
                LayerFinding(
                    layer="process",
                    signal="vat_math_mismatch",
                    description=f"Stated VAT (₦{claimed_vat:,.2f}) doesn't match 7.5% of subtotal (expected ₦{vat_result['expected_vat']:,.2f})",
                    evidence=vat_result,
                    points=35,
                    source="receipt_engine",
                )
            )
            steps.append(
                {
                    "step": "vat_check",
                    "status": "flagged",
                    "detail": f"Expected ₦{vat_result['expected_vat']:,.2f}, got ₦{claimed_vat:,.2f}",
                }
            )
        else:
            steps.append(
                {
                    "step": "vat_check",
                    "status": "clean",
                    "detail": "VAT math checks out",
                }
            )

    # Compute overall verdict
    total_points = sum(f.points for f in findings)
    if total_points >= 70:
        verdict = "BLOCK"
    elif total_points >= 30:
        verdict = "FLAG"
    else:
        verdict = "CLEAR"

    return {
        "verdict": verdict,
        "score": total_points,
        "findings": [f.model_dump() for f in findings],
        "steps": steps,
        "phash": phash_value,
        "exif": exif_data,
    }
