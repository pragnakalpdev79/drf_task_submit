from django.test import TestCase,Client,override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.urls import reverse
from user.models import *
import tempfile
import shutil
from PIL import Image
from io import BytesIO

TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DocumentUploadTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT,ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.client.login(username='testuser',password='testpass123')

