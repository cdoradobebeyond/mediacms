import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


class ApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.USERS_NEEDS_TO_BE_APPROVED and request.user.is_authenticated and not request.user.is_superuser and not getattr(request.user, 'is_approved', False):
            allowed_paths = [
                reverse('approval_required'),
                reverse('account_logout'),
            ]
            if request.path not in allowed_paths:
                if request.path.startswith('/api/'):
                    return JsonResponse({'detail': 'User account not approved.'}, status=403)
                return redirect('approval_required')

        response = self.get_response(request)
        return response


class CustomerMediaAccessMiddleware:
    """Populate request and user objects with Keycloak customerType data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        media_ids = self._extract_customer_media_ids(request)
        request.customer_media_ids = media_ids

        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            try:
                user.customer_media_ids = media_ids
            except AttributeError:
                setattr(user, "_customer_media_ids", media_ids)

        response = self.get_response(request)
        return response

    def _extract_customer_media_ids(self, request):
        candidate_values = []

        session = getattr(request, "session", None)
        if session is not None:
            direct_value = session.get("customerType")
            if direct_value:
                candidate_values.append(direct_value)

            for container_key in ("user", "metadata", "attributes"):
                container = session.get(container_key)
                if isinstance(container, dict) and container.get("customerType"):
                    candidate_values.append(container["customerType"])

        cookies = getattr(request, "COOKIES", {}) or {}
        cookie_value = cookies.get("customerType")
        if cookie_value:
            candidate_values.append(cookie_value)

        metadata_cookie_key = getattr(settings, "KEYCLOAK_CUSTOMER_METADATA_COOKIE", None)
        if metadata_cookie_key:
            metadata_cookie_value = cookies.get(metadata_cookie_key)
            if metadata_cookie_value:
                candidate_values.append(metadata_cookie_value)

        normalized = set()
        for value in candidate_values:
            normalized.update(self._normalize_media_ids(value))

        return frozenset(normalized)

    def _normalize_media_ids(self, value):
        if value is None:
            return set()

        if isinstance(value, (set, frozenset, list, tuple)):
            iterable = value
        elif isinstance(value, dict):
            if "customerType" in value:
                return self._normalize_media_ids(value["customerType"])
            iterable = value.values()
        else:
            text = str(value).strip()
            if not text:
                return set()

            try:
                parsed = json.loads(text)
            except (TypeError, ValueError):
                iterable = [item for item in text.split(",") if item]
            else:
                return self._normalize_media_ids(parsed)

        normalized = set()
        for item in iterable:
            if item is None:
                continue
            try:
                text_item = str(item).strip()
            except Exception:  # pragma: no cover - defensive
                continue
            if text_item:
                normalized.add(text_item)

        return normalized
