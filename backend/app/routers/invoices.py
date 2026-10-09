from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.deps import get_current_user, get_db
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas.invoice import InvoiceOcrOut, InvoiceOut
from app.services.processing import process_invoice
from app.services.storage import save_upload

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _owned_invoice(db: Session, invoice_id: int, user: User) -> Invoice:
    invoice = db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id, Invoice.user_id == user.id)
    )
    if invoice is None:
        # 404 (not 403) so we don't reveal that someone else's invoice exists
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_202_ACCEPTED)
def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stored_path, content_type = save_upload(file, current_user.id)

    # Keep the client's filename for display only, never for the file path
    display_name = Path(file.filename or "upload").name[:255]

    invoice = Invoice(
        user_id=current_user.id,
        original_filename=display_name,
        file_path=stored_path,
        content_type=content_type,
        status=InvoiceStatus.PROCESSING.value,
    )
    db.add(invoice)
    try:
        db.commit()
    except Exception:
        db.rollback()
        Path(stored_path).unlink(missing_ok=True)
        raise
    db.refresh(invoice)

    background_tasks.add_task(process_invoice, invoice.id)
    return invoice


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status_filter: InvoiceStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.user_id == current_user.id)
    )
    if status_filter is not None:
        stmt = stmt.where(Invoice.status == status_filter.value)
    stmt = (
        stmt.order_by(Invoice.created_at.desc(), Invoice.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(stmt).all()


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _owned_invoice(db, invoice_id, current_user)


@router.get("/{invoice_id}/ocr", response_model=InvoiceOcrOut)
def get_invoice_ocr(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invoice = _owned_invoice(db, invoice_id, current_user)
    return InvoiceOcrOut(
        raw_ocr_text=invoice.raw_ocr_text, confidence=invoice.confidence
    )


@router.post(
    "/{invoice_id}/reprocess",
    response_model=InvoiceOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def reprocess_invoice(
    invoice_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run OCR and extraction again on the stored file (for example after
    tuning the prompt or fixing the LLM settings)."""
    invoice = _owned_invoice(db, invoice_id, current_user)
    if invoice.status == InvoiceStatus.PROCESSING.value:
        raise HTTPException(status_code=409, detail="Invoice is already being processed")
    if invoice.status == InvoiceStatus.VERIFIED.value:
        raise HTTPException(
            status_code=409, detail="Verified invoices cannot be reprocessed"
        )

    invoice.status = InvoiceStatus.PROCESSING.value
    invoice.error_message = None
    db.commit()
    db.refresh(invoice)

    background_tasks.add_task(process_invoice, invoice.id)
    return invoice