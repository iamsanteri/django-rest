"""
Tests for recipe APIs.
"""

from decimal import Decimal
# import tempfile
# import os

# from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """ Return recipe detail URL. """
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """ Return URL for recipe image upload. """
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def create_recipe(user, **params):
    """ Create and return a sample recipe. """
    defaults = {
        "title": "Sample recipe",
        "description": "Sample description",
        "time_minutes": 10,
        "price": Decimal("5.00"),
        "link": "https://sample.com/recipe.pdf"
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """ Create and return a sample user. """
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """ Test unauthenticated recipe API access. """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ Test that authentication is required. """
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """ Test authenticated recipe API access. """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com",
                                password="testpass123")
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """ Test retrieving a list of recipes. """
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_list_limited_to_user(self):
        """ Test retrieving recipes for authenticated user. """
        other_user = create_user(email="other@example.com",
                                 password="testpass123")
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """ Test get a recipe detail. """
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """ Test creating a recipe. """
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 30,
            "price": Decimal("5.00")
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """ Test updating a recipe with patch. """
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link=original_link)

        payload = {"title": "Chicken masala"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """ Test updating a recipe with put. """
        recipe = create_recipe(
            user=self.user,
            title="Sample recipe title",
            link="https://example.com/recipe.pdf",
            description="Sample description",
        )

        payload = {
            "title": "Spaghetti carbonara",
            "link": "https://example.com/spaghetti.pdf",
            "description": "Spaghetti carbonara description",
            "time_minutes": 25,
            "price": Decimal("7.00")
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)


def test_update_user_returns_error(self):
    """ Test that updating user returns an error. """
    new_user = create_user(email="user2@example.com", password="testpass123")
    recipe = create_recipe(user=self.user)

    payload = {"user": new_user}
    url = detail_url(recipe.id)
    self.client.put(url, payload)

    recipe.refresh_from_db()
    self.assertEqual(recipe.user, self.user)


def test_delete_recipe(self):
    """ Test deleting a recipe successful. """
    recipe = create_recipe(user=self.user)

    url = detail_url(recipe.id)
    res = self.client.delete(url)

    self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
    self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())


def test_delete_other_users_recipe_error(self):
    """ Test that deleting other users recipe returns an error. """
    other_user = create_user(email="user2@example.com", password="test123")
    recipe = create_recipe(user=other_user)

    url = detail_url(recipe.id)
    res = self.client.delete(url)

    self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
    self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


class ImageUploadTests(TestCase):
    """ Tests for the image upload API. """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "password123"
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    """
    def test_upload_image(self):
        # Test uploading an image to recipe. #
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))
    """

    def test_upload_image_bad_request(self):
        """ Test uploading an invalid image. """
        url = image_upload_url(self.recipe.id)
        payload = {"image": "notimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
