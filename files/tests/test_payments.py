import io
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework.test import APIClient

from files.models import Category, Media
from files.tests.user_utils import create_account


@pytest.fixture
def temp_media_root(tmp_path):
    with override_settings(MEDIA_ROOT=tmp_path):
        yield tmp_path


def _generate_image_file(filename="test.jpg"):
    buffer = io.BytesIO()
    image = Image.new("RGB", (10, 10), color="blue")
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(filename, buffer.read(), content_type="image/jpeg")


@pytest.mark.django_db
def test_paid_media_access_respects_customer_type_session(temp_media_root):
    owner = create_account()
    viewer = create_account(username="viewer", email="viewer@example.com")

    media = Media.objects.create(
        user=owner,
        title="Premium Image",
        media_type="image",
        media_file=_generate_image_file(),
        requires_payment=True,
        price=Decimal("4.99"),
        currency="EUR",
        encoding_status="success",
        state="public",
        listable=True,
    )

    client = APIClient()
    detail_url = f"/api/v1/media/{media.friendly_token}"

    anonymous_response = client.get(detail_url)
    assert anonymous_response.status_code == 402

    client.force_authenticate(user=viewer)

    unauthorised_response = client.get(detail_url)
    assert unauthorised_response.status_code == 402

    session = client.session
    session["customerType"] = [str(media.id)]
    session.save()

    authorised_response = client.get(detail_url)
    assert authorised_response.status_code == 200
    payload = authorised_response.json()
    assert payload["user_has_access"] is True
    assert payload["payment_required"] is True


@pytest.mark.django_db
def test_category_access_granted_when_all_media_ids_present(temp_media_root):
    owner = create_account()
    viewer = create_account(username="viewer2", email="viewer2@example.com")

    category = Category.objects.create(
        user=owner,
        title="Documentaries",
        requires_payment=True,
        price=Decimal("9.99"),
        currency="USD",
    )

    primary_media = Media.objects.create(
        user=owner,
        title="Exclusive Documentary",
        media_type="image",
        media_file=_generate_image_file("doc.jpg"),
        encoding_status="success",
        state="public",
        listable=True,
    )
    secondary_media = Media.objects.create(
        user=owner,
        title="Behind the Scenes",
        media_type="image",
        media_file=_generate_image_file("bts.jpg"),
        encoding_status="success",
        state="public",
        listable=True,
    )

    primary_media.category.add(category)
    secondary_media.category.add(category)

    client = APIClient()
    client.force_authenticate(user=viewer)

    list_url = "/api/v1/categories"

    initial_response = client.get(list_url)
    assert initial_response.status_code == 200
    category_payload = next(item for item in initial_response.json() if item["uid"] == category.uid)
    assert category_payload["user_has_access"] is False

    session = client.session
    session["customerType"] = [
        str(primary_media.id),
        secondary_media.friendly_token,
    ]
    session.save()

    updated_response = client.get(list_url)
    assert updated_response.status_code == 200
    updated_category_payload = next(item for item in updated_response.json() if item["uid"] == category.uid)
    assert updated_category_payload["user_has_access"] is True
