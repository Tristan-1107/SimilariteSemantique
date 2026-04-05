from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.loader_utils import PROJECT_ROOT
from app.services.processor import (
    get_data_dir,
    load_uploaded_json,
    process_minimal_json,
    save_batch_results,
    validate_result_filename,
)
from app.services.similarity import (
    compute_similarity_response,
    list_available_languages,
    list_available_metrics,
)


router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "app" / "web" / "templates"))


def _render_home(
    request: Request,
    *,
    compare_form: dict | None = None,
    compare_result: dict | None = None,
    compare_error: str | None = None,
    upload_form: dict | None = None,
    upload_result: dict | None = None,
    upload_error: str | None = None,
    status_code: int = 200,
):
    context = {
        "request": request,
        "metrics": list_available_metrics(),
        "languages": list_available_languages(),
        "compare_form": {
            "phrase1": "",
            "phrase2": "",
            "metrics": ["jaccard"],
            "language": "fr",
        },
        "compare_result": compare_result,
        "compare_error": compare_error,
        "upload_form": {
            "language": "fr",
        },
        "upload_result": upload_result,
        "upload_error": upload_error,
    }

    if compare_form is not None:
        context["compare_form"].update(compare_form)

    if upload_form is not None:
        context["upload_form"].update(upload_form)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _render_home(request)


@router.post("/web/compare", response_class=HTMLResponse)
def compare(
    request: Request,
    phrase1: str = Form(""),
    phrase2: str = Form(""),
    metrics: list[str] | None = Form(None),
    language: str = Form("fr"),
):
    selected_metrics = metrics or []
    compare_form = {
        "phrase1": phrase1,
        "phrase2": phrase2,
        "metrics": selected_metrics,
        "language": language,
    }

    if not selected_metrics:
        return _render_home(
            request,
            compare_form=compare_form,
            compare_error="Sélectionnez au moins une métrique.",
            status_code=400,
        )

    try:
        compare_result = compute_similarity_response(
            phrase1=phrase1,
            phrase2=phrase2,
            metric_names=selected_metrics,
            language=language,
        )
    except ValueError as exc:
        return _render_home(
            request,
            compare_form=compare_form,
            compare_error=str(exc),
            status_code=400,
        )
    except RuntimeError as exc:
        return _render_home(
            request,
            compare_form=compare_form,
            compare_error=str(exc),
            status_code=500,
        )

    return _render_home(
        request,
        compare_form=compare_form,
        compare_result=compare_result,
    )


@router.post("/web/upload", response_class=HTMLResponse)
async def upload(
    request: Request,
    file: UploadFile | None = File(None),
    language: str = Form("fr"),
):
    upload_form = {"language": language}

    if file is None or not file.filename:
        return _render_home(
            request,
            upload_form=upload_form,
            upload_error="Sélectionnez un fichier JSON à envoyer.",
            status_code=400,
        )

    try:
        filename, data = load_uploaded_json(file.filename, await file.read())
        results = process_minimal_json(data, default_language=language)
        output_filename, _ = save_batch_results(results, filename)
    except ValueError as exc:
        return _render_home(
            request,
            upload_form=upload_form,
            upload_error=str(exc),
            status_code=400,
        )
    except RuntimeError as exc:
        return _render_home(
            request,
            upload_form=upload_form,
            upload_error=str(exc),
            status_code=500,
        )

    return _render_home(
        request,
        upload_form=upload_form,
        upload_result={
            "output_file": output_filename,
            "results": results,
        },
    )


@router.get("/web/download/{filename}")
def download(filename: str):
    try:
        safe_filename = validate_result_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_path = get_data_dir() / safe_filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Fichier introuvable.")

    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=safe_filename,
    )
