from __future__ import annotations

import os
from io import BytesIO
from typing import Any

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string

from xhtml2pdf import pisa


def _link_callback(uri: str, rel: str) -> str:
	"""Resolve static/media URIs to absolute filesystem paths for xhtml2pdf."""
	if uri.startswith(settings.MEDIA_URL or '/media/'):
		path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, '').lstrip('/'))
		return path

	if uri.startswith(settings.STATIC_URL or '/static/'):
		rel_path = uri.replace(settings.STATIC_URL, '').lstrip('/')
		found = finders.find(rel_path)
		if found:
			return found
		if getattr(settings, 'STATIC_ROOT', None):
			return os.path.join(settings.STATIC_ROOT, rel_path)

	# Return URI unchanged if we can't resolve it.
	return uri


def render_pdf_from_template(*, template_name: str, context: dict[str, Any], filename: str) -> HttpResponse:
	html = render_to_string(template_name, context=context)
	result = BytesIO()
	pdf = pisa.CreatePDF(html, dest=result, link_callback=_link_callback, encoding='utf-8')
	if pdf.err:
		return HttpResponse('Could not generate PDF.', status=500)

	response = HttpResponse(result.getvalue(), content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="{filename}"'
	return response
