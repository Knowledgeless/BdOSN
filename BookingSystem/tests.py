import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils.timezone import localdate

from .models import ArchivedBooking, Booking, Room
from .views import archive_expired_bookings


class BookingArchiveTests(TestCase):
	def setUp(self):
		self.room = Room.objects.create(name="Test room")
		self.booking = Booking.objects.create(
			room=self.room,
			title="Expired meeting",
			conference_date=localdate() - timedelta(days=1),
		)

	def test_expired_bookings_are_archived_and_removed_once(self):
		self.assertEqual(archive_expired_bookings(), 1)
		self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())
		self.assertEqual(ArchivedBooking.objects.filter(original_booking_id=self.booking.pk).count(), 1)
		self.assertEqual(archive_expired_bookings(), 0)
		self.assertEqual(ArchivedBooking.objects.filter(original_booking_id=self.booking.pk).count(), 1)

	def test_cron_endpoint_rejects_missing_bearer_secret(self):
		with patch.dict(os.environ, {"CRON_SECRET": "test-secret"}):
			response = self.client.get("/cron/archive-expired-bookings/")

		self.assertEqual(response.status_code, 403)

	def test_cron_endpoint_archives_with_valid_bearer_secret(self):
		with patch.dict(os.environ, {"CRON_SECRET": "test-secret"}):
			response = self.client.get(
				"/cron/archive-expired-bookings/",
				HTTP_AUTHORIZATION="Bearer test-secret",
			)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(json.loads(response.content), {"archived": 1})
		self.assertFalse(Booking.objects.filter(pk=self.booking.pk).exists())

	def test_staff_archive_filter_returns_archived_booking(self):
		staff = get_user_model().objects.create_user(username="staff", is_staff=True)
		archived = ArchivedBooking.objects.create(
			original_booking_id=42,
			user=staff,
			room=self.room,
			title="Archived meeting",
			conference_date=localdate() - timedelta(days=1),
			start_time="09:00",
			end_time="10:00",
		)
		self.client.force_login(staff)

		response = self.client.get(f"/rooms/{self.room.pk}/archived/filter/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["bookings"][0]["title"], archived.title)

		with override_settings(STORAGES={
			"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
			"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
		}):
			page = self.client.get(f"/book/{self.room.pk}/")
		self.assertContains(page, f'data-url="/rooms/{self.room.pk}/archived/filter/"')

	def test_booking_requires_one_hour_gap_after_previous_booking(self):
		today = localdate()
		user = get_user_model().objects.create_user(username="alice")
		self.client.force_login(user)
		Booking.objects.create(
			room=self.room,
			user=user,
			title="Existing meeting",
			conference_date=today,
			start_time="15:00",
			end_time="16:00",
		)

		response = self.client.post(
			f"/book/{self.room.pk}/",
			{
				"title": "Later meeting",
				"conference_date[]": [today.isoformat()],
				"start_time[]": ["16:30"],
				"end_time[]": ["17:30"],
				"organization": "BdOSN",
				"booked_for": "Alice",
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(Booking.objects.filter(room=self.room, conference_date=today).count(), 1)
