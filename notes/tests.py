from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Note

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.token = Token.objects.create(user=self.user)
    
    def test_register(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123'
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('token' in response.data)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_login(self):
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)
    
    def test_logout(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

class NoteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create some test notes
        self.note1 = Note.objects.create(
            user=self.user,
            title='Test Note 1',
            content='This is test note 1'
        )
        self.note2 = Note.objects.create(
            user=self.user,
            title='Test Note 2',
            content='This is test note 2'
        )
    
    def test_get_notes(self):
        response = self.client.get('/api/notes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_create_note(self):
        data = {
            'title': 'New Test Note',
            'content': 'This is a new test note'
        }
        response = self.client.post('/api/notes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Note.objects.count(), 3)
        self.assertEqual(Note.objects.get(id=response.data['id']).title, 'New Test Note')
    
    def test_update_note(self):
        data = {
            'title': 'Updated Test Note',
            'content': 'This is an updated test note'
        }
        response = self.client.put(f'/api/notes/{self.note1.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.note1.refresh_from_db()
        self.assertEqual(self.note1.title, 'Updated Test Note')
    
    def test_delete_note(self):
        response = self.client.delete(f'/api/notes/{self.note1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Note.objects.count(), 1)
